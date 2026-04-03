"""Chat service for AI assistant conversations about stock analysis."""
import re
import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.score_result import ScoreResult
from app.models.llm_report import LLMReport
from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.models.institutional import Institutional
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

# System prompt for chat assistant
CHAT_SYSTEM_PROMPT = """你是「Stock Screener」平台的 AI 投資小幫手，使用繁體中文回答。

你的角色：
- 根據提供的數據，給出有深度的股票分析回覆
- 解讀技術指標、籌碼資訊、基本面數據
- 解釋投資相關術語和概念
- 引導使用者使用平台功能

格式：
- 使用純文字為主，不要用 **粗體** 或 markdown 格式
- 可用 • 符號做列點，但不要過度使用

規則：
- 回答要有實質內容，包含具體數據和分析觀點
- 不提供具體買賣建議，但可以客觀分析多空因素
- 引用數據時標明來源
- 適時建議使用者前往相關功能頁面查看詳細數據
- 回答結尾附上「⚠️ 以上僅供參考，不構成投資建議。」
- 回覆最後必須附上 2~3 個延伸問題供使用者繼續提問，格式如下：
  <<SUGGESTIONS>>
  延伸問題1
  延伸問題2
  延伸問題3
  （延伸問題要簡短、與回覆主題相關、能引導更深入分析）

{context}"""


# Delimiter for parsing follow-up suggestions from LLM response
SUGGESTIONS_DELIMITER = "<<SUGGESTIONS>>"


# Regex to find stock IDs (4-digit numbers) or stock names in messages
STOCK_ID_PATTERN = re.compile(r'\b(\d{4})\b')


def _extract_stock_ids(messages: list[dict[str, str]], db: Session) -> list[str]:
    """Extract stock IDs mentioned in the latest user message."""
    # Get the last user message
    last_user_msg = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break

    if not last_user_msg:
        return []

    # Find 4-digit stock IDs
    found_ids = STOCK_ID_PATTERN.findall(last_user_msg)

    # Also search by stock name in DB
    if not found_ids:
        stocks = db.query(Stock.stock_id, Stock.stock_name).all()
        for sid, name in stocks:
            if name and name in last_user_msg:
                found_ids.append(sid)

    return found_ids[:3]  # Limit to 3 stocks max


def _build_stock_detail(db: Session, stock_id: str) -> str:
    """Build detailed context for a specific stock."""
    lines = []

    # Stock name
    stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
    stock_name = stock.stock_name if stock else stock_id
    lines.append(f"\n【{stock_name}({stock_id}) 詳細資料】")

    # Latest price
    price = (
        db.query(DailyPrice)
        .filter(DailyPrice.stock_id == stock_id)
        .order_by(desc(DailyPrice.trade_date))
        .first()
    )
    if price:
        change_str = f"+{price.change_price}" if price.change_price and price.change_price > 0 else str(price.change_price or 0)
        pct_str = f"+{price.change_percent}" if price.change_percent and price.change_percent > 0 else str(price.change_percent or 0)
        lines.append(f"最新收盤: {price.close} 元 ({change_str}, {pct_str}%) | 成交量: {price.volume:,} | 日期: {price.trade_date}")

    # Latest score
    score = (
        db.query(ScoreResult)
        .filter(ScoreResult.stock_id == stock_id)
        .order_by(desc(ScoreResult.score_date))
        .first()
    )
    if score:
        cls = score.classification or "N/A"
        momentum = float(score.momentum_score or 0)
        parts = [f"評分: 總分 {score.total_score:.1f} | 動能 {momentum:.1f} | 分類 {cls}"]
        price_parts = []
        if score.buy_price:
            price_parts.append(f"進場 {float(score.buy_price):.1f}")
        if score.stop_price:
            price_parts.append(f"停損 {float(score.stop_price):.1f}")
        if score.target_price:
            price_parts.append(f"目標 {float(score.target_price):.1f}")
        if price_parts:
            parts.append(" ".join(price_parts))
        parts.append(f"排名 #{score.rank}")
        lines.append(" | ".join(parts))

    # Latest institutional data (last 5 days summary)
    inst_data = (
        db.query(Institutional)
        .filter(Institutional.stock_id == stock_id)
        .order_by(desc(Institutional.trade_date))
        .limit(5)
        .all()
    )
    if inst_data:
        foreign_total = sum(i.foreign_net or 0 for i in inst_data)
        trust_total = sum(i.trust_net or 0 for i in inst_data)
        lines.append(
            f"近 {len(inst_data)} 日法人: "
            f"外資累計 {foreign_total:+,} 張 | "
            f"投信累計 {trust_total:+,} 張"
        )

    # Latest LLM report summary
    report = (
        db.query(LLMReport)
        .filter(LLMReport.stock_id == stock_id)
        .order_by(desc(LLMReport.report_date))
        .first()
    )
    if report:
        lines.append(f"AI 報告 ({report.report_date}): 信心度={report.confidence}")
        # Include key analysis sections (truncated)
        if report.chip_analysis:
            lines.append(f"  籌碼分析: {report.chip_analysis[:100]}")
        if report.technical_analysis:
            lines.append(f"  技術分析: {report.technical_analysis[:100]}")
        if report.recommendation:
            lines.append(f"  建議: {report.recommendation[:100]}")
        if report.risk_alerts:
            alerts = report.risk_alerts if isinstance(report.risk_alerts, list) else [report.risk_alerts]
            lines.append(f"  風險: {'; '.join(str(a) for a in alerts[:2])}")

    return "\n".join(lines)


def build_stock_context(db: Session, stock_ids: list[str] = None) -> str:
    """
    Build market context summary from latest DB data.

    Args:
        db: Database session
        stock_ids: Optional specific stock IDs to include detailed data for

    Returns:
        Context string for system prompt
    """
    lines = []

    try:
        # Latest scoring date and top 5 stocks
        latest_score = (
            db.query(ScoreResult.score_date)
            .order_by(desc(ScoreResult.score_date))
            .first()
        )
        if latest_score:
            top_stocks = (
                db.query(ScoreResult.stock_id, ScoreResult.total_score, Stock.stock_name)
                .outerjoin(Stock, ScoreResult.stock_id == Stock.stock_id)
                .filter(ScoreResult.score_date == latest_score[0])
                .order_by(desc(ScoreResult.total_score))
                .limit(5)
                .all()
            )
            if top_stocks:
                lines.append(f"最新評分日期: {latest_score[0]}")
                lines.append("綜合評分前 5 名：")
                for sid, score, name in top_stocks:
                    lines.append(f"  {name or sid}({sid}) - {score:.1f} 分")

        # Latest report date
        latest_report = (
            db.query(LLMReport.report_date)
            .order_by(desc(LLMReport.report_date))
            .first()
        )
        if latest_report:
            report_count = (
                db.query(func.count(LLMReport.id))
                .filter(LLMReport.report_date == latest_report[0])
                .scalar()
            )
            lines.append(f"最新 AI 報告日期: {latest_report[0]}（共 {report_count} 份）")

        # Add detailed data for mentioned stocks
        if stock_ids:
            for sid in stock_ids:
                try:
                    detail = _build_stock_detail(db, sid)
                    if detail:
                        lines.append(detail)
                except Exception as e:
                    logger.warning(f"Failed to build detail for {sid}: {e}")

    except Exception as e:
        logger.warning(f"Failed to build stock context: {e}")

    if lines:
        return "平台最新數據摘要：\n" + "\n".join(lines)
    return ""


def _parse_suggestions(raw_reply: str) -> Tuple[str, list[str]]:
    """Parse follow-up suggestions from LLM response.

    Returns:
        Tuple of (clean reply text, list of suggestion strings)
    """
    if SUGGESTIONS_DELIMITER not in raw_reply:
        return raw_reply.strip(), []

    parts = raw_reply.split(SUGGESTIONS_DELIMITER, 1)
    reply = parts[0].strip()
    suggestion_lines = [
        line.strip().lstrip("•-．·0123456789.、） ")
        for line in parts[1].strip().splitlines()
        if line.strip()
    ]
    # Keep only non-empty, reasonable-length suggestions (max 3)
    suggestions = [s for s in suggestion_lines if 2 < len(s) <= 50][:3]
    return reply, suggestions


def chat_with_assistant(
    db: Session,
    llm_client: LLMClient,
    messages: list[dict[str, str]],
) -> Tuple[Optional[str], list[str]]:
    """
    Process a chat conversation with the AI assistant.

    Args:
        db: Database session
        llm_client: LLM API client
        messages: Conversation history

    Returns:
        Tuple of (reply text or None, list of follow-up suggestions)
    """
    # Extract stock IDs mentioned by user for enriched context
    stock_ids = _extract_stock_ids(messages, db)
    context = build_stock_context(db, stock_ids)
    system_prompt = CHAT_SYSTEM_PROMPT.format(context=context)
    raw_reply = llm_client.generate_chat(system_prompt, messages)

    if not raw_reply:
        return None, []

    return _parse_suggestions(raw_reply)
