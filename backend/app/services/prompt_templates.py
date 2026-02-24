"""Prompt templates for LLM stock analysis in Traditional Chinese."""

SYSTEM_PROMPT = """你是一位專業的台灣股市分析師。根據提供的數據進行深入分析，使用繁體中文回答。
分析必須客觀且基於數據，不要給出絕對的買賣建議。
right_side_analysis 欄位要求：不要只重述數字，而是將右側信號與籌碼面、技術面、基本面進行交叉驗證。例如：信號觸發但 KD 過熱時，應指出矛盾並建議等待回測；信號與法人買超共振時，應強調進場信心較高。最後給出具體操作建議（進場/觀望/迴避）並說明理由。
recommendation 欄位要求：必須整合所有面向的分析結論，包含右側信號的研判結果。若有明確的進出場價位，應納入建議中（例如：「建議回測至 XX 元附近再考慮佈局，停損設 XX 元」）。避免空泛的「評估自身風險」，改為給出有依據的操作方向。
所有分析結論必須附加免責聲明：「本分析僅供參考，不構成投資建議。」"""


def build_analysis_prompt(
    stock_id: str,
    stock_name: str,
    chip_data: dict,
    fundamental_data: dict,
    technical_data: dict,
    right_side_data: dict,
    news_text: str,
    scores: dict
) -> str:
    """
    Build comprehensive analysis prompt with stock data.

    Args:
        stock_id: Stock ticker (e.g., "2330")
        stock_name: Company name (e.g., "台積電")
        chip_data: Institutional trading data
        fundamental_data: Financial metrics
        technical_data: Technical indicators
        right_side_data: Right-side momentum signals and prediction
        news_text: Formatted news summary
        scores: Individual and total scores

    Returns:
        Formatted prompt string for LLM
    """
    prompt = f"""股票: {stock_id} {stock_name}

=== 籌碼面數據 ===
三大法人近 10 日買賣超:
{_format_institutional(chip_data.get('institutional', []))}

融資融券近 5 日變化:
{_format_margin(chip_data.get('margin', []))}

=== 基本面數據 ===
近 3 月營收 YoY:
{_format_revenue(fundamental_data.get('revenue', []))}

近 4 季 EPS:
{_format_eps(fundamental_data.get('eps', []))}

財務指標:
ROE: {fundamental_data.get('roe', 'N/A')}%
負債比: {fundamental_data.get('debt_ratio', 'N/A')}%
營業現金流: {fundamental_data.get('cash_flow', 'N/A')} 億元

=== 技術面數據 ===
最新交易日: {technical_data.get('trade_date', 'N/A')}
收盤價: {technical_data.get('close', 'N/A')} 元
成交量: {_format_volume(technical_data.get('volume', 'N/A'))} 股

移動平均線:
MA5: {technical_data.get('ma5', 'N/A')} / MA10: {technical_data.get('ma10', 'N/A')} / MA20: {technical_data.get('ma20', 'N/A')}
MA60: {technical_data.get('ma60', 'N/A')} / MA120: {technical_data.get('ma120', 'N/A')}

技術指標:
KD: K={technical_data.get('k', 'N/A')}, D={technical_data.get('d', 'N/A')}
MACD: DIF={technical_data.get('macd_dif', 'N/A')}, MACD={technical_data.get('macd', 'N/A')}
RSI: {technical_data.get('rsi', 'N/A')}

=== 右側買法信號 ===
{_format_right_side(right_side_data)}

=== 近期新聞 ===
{news_text}

=== 評分 ===
籌碼面: {scores.get('chip', 0)} 分
基本面: {scores.get('fundamental', 0)} 分
技術面: {scores.get('technical', 0)} 分
總分: {scores.get('total', 0)} 分
右側信號: {right_side_data.get('score', 0)}/100 分 (觸發 {right_side_data.get('triggered_count', 0)}/6)
"""
    return prompt


def _format_institutional(data: list) -> str:
    """Format institutional trading data with foreign/trust/dealer breakdown."""
    if not data:
        return "無資料"
    lines = []
    for item in data[:5]:  # Last 5 days
        d = item.get('date', 'N/A')
        f_net = item.get('foreign_net', 0)
        t_net = item.get('trust_net', 0)
        d_net = item.get('dealer_net', 0)
        total = item.get('total_net', 0)
        lines.append(
            f"{d}: 外資 {f_net:+,} / 投信 {t_net:+,} / 自營 {d_net:+,} (合計 {total:+,})"
        )
    return "\n".join(lines) if lines else "無資料"


def _format_volume(vol) -> str:
    """Format volume with comma separator, handle N/A."""
    return f"{vol:,}" if isinstance(vol, (int, float)) else str(vol)


def _format_margin(data) -> str:
    """Format margin trading data (list of 5 days or legacy single dict)."""
    if not data:
        return "無資料"
    # Support list format (new) and dict format (legacy)
    if isinstance(data, dict):
        data = [data]
    lines = []
    for item in data[:5]:
        d = item.get('date', '')
        m_bal = item.get('margin_balance', 'N/A')
        m_chg = item.get('margin_change', 'N/A')
        s_bal = item.get('short_balance', 'N/A')
        s_chg = item.get('short_change', 'N/A')
        m_str = f"{m_chg:+}" if isinstance(m_chg, (int, float)) else str(m_chg)
        s_str = f"{s_chg:+}" if isinstance(s_chg, (int, float)) else str(s_chg)
        prefix = f"{d}: " if d else ""
        lines.append(f"{prefix}融資 {m_bal}張({m_str}) / 融券 {s_bal}張({s_str})")
    return "\n".join(lines) if lines else "無資料"


def _format_revenue(data: list) -> str:
    """Format revenue data."""
    if not data:
        return "無資料"
    lines = []
    for item in data[:3]:  # Last 3 months
        month = item.get('month', 'N/A')
        yoy = item.get('yoy', 0)
        lines.append(f"{month}: YoY {yoy:+.2f}%")
    return "\n".join(lines) if lines else "無資料"


def _format_eps(data: list) -> str:
    """Format EPS data."""
    if not data:
        return "無資料"
    lines = []
    for item in data[:4]:  # Last 4 quarters
        quarter = item.get('quarter', 'N/A')
        eps = item.get('eps', 0)
        lines.append(f"{quarter}: {eps:.2f} 元")
    return "\n".join(lines) if lines else "無資料"


def _format_right_side(data: dict) -> str:
    """Format right-side momentum signal data."""
    if not data or not data.get('triggered_count'):
        return "無觸發信號"

    lines = []
    lines.append(f"信號得分: {data.get('score', 0)}/100 (觸發 {data.get('triggered_count', 0)}/6)")

    # Triggered signals
    triggered = data.get('triggered_signals', [])
    if triggered:
        sig_list = ", ".join(s['label'] for s in triggered)
        lines.append(f"觸發信號: {sig_list}")

    # Prediction
    pred = data.get('prediction')
    if pred:
        action_map = {"buy": "建議買入", "hold": "觀望等待", "avoid": "暫不建議"}
        action_label = action_map.get(pred.get('action', ''), pred.get('action_label', ''))
        lines.append(f"操作建議: {action_label}")
        lines.append(f"進場價: {pred.get('entry', 'N/A')} / 停損: {pred.get('stop_loss', 'N/A')} / 目標價: {pred.get('target', 'N/A')}")
        lines.append(f"報酬風險比: {pred.get('risk_reward', 'N/A')}")

    # Conditions
    tags = []
    if data.get('today_breakout'):
        tags.append("今日突破")
    if data.get('weekly_trend_up'):
        tags.append("週趨勢向上")
    if data.get('strong_recommend'):
        tags.append("強力推薦")
    risk_map = {"low": "低風險", "medium": "中風險", "high": "高風險"}
    tags.append(risk_map.get(data.get('risk_level', 'high'), '高風險'))
    lines.append(f"條件標籤: {' / '.join(tags)}")

    return "\n".join(lines)


# Response schema for LLM structured output
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "chip_analysis": {
            "type": "string",
            "description": "籌碼面解讀 (法人動向、融資融券分析)"
        },
        "fundamental_analysis": {
            "type": "string",
            "description": "基本面分析 (營收、獲利、財務體質)"
        },
        "technical_analysis": {
            "type": "string",
            "description": "技術面判斷 (趨勢、支撐壓力、指標)"
        },
        "news_sentiment": {
            "type": "string",
            "enum": ["正面", "中性", "負面"],
            "description": "新聞情緒"
        },
        "news_summary": {
            "type": "string",
            "description": "新聞摘要與影響評估"
        },
        "risk_alerts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "風險提示項目"
        },
        "right_side_analysis": {
            "type": "string",
            "description": "右側買法綜合研判：將觸發信號與籌碼/技術/基本面交叉驗證，指出共振或矛盾，給出具體操作建議與理由"
        },
        "recommendation": {
            "type": "string",
            "description": "綜合建議：整合所有面向結論，納入具體進出場價位與操作方向，必須包含免責聲明"
        },
        "confidence": {
            "type": "string",
            "enum": ["高", "中", "低"],
            "description": "分析信心水準"
        }
    },
    "required": [
        "chip_analysis",
        "fundamental_analysis",
        "technical_analysis",
        "news_sentiment",
        "news_summary",
        "risk_alerts",
        "recommendation",
        "confidence"
    ]
}
