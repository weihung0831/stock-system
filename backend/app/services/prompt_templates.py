"""Prompt templates for LLM stock analysis in Traditional Chinese."""

SYSTEM_PROMPT = """你是一位專業的台灣股市分析師。根據提供的數據進行深入分析，使用繁體中文回答。
分析必須客觀且基於數據，不要給出絕對的買賣建議。
所有分析結論必須附加免責聲明：「本分析僅供參考，不構成投資建議。」"""


def build_analysis_prompt(
    stock_id: str,
    stock_name: str,
    chip_data: dict,
    fundamental_data: dict,
    technical_data: dict,
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
        news_text: Formatted news summary
        scores: Individual and total scores

    Returns:
        Formatted prompt string for LLM
    """
    prompt = f"""股票: {stock_id} {stock_name}

=== 籌碼面數據 ===
三大法人近 10 日買賣超:
{_format_institutional(chip_data.get('institutional', []))}

融資融券變化:
{_format_margin(chip_data.get('margin', {}))}

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
移動平均線:
MA5: {technical_data.get('ma5', 'N/A')} / MA10: {technical_data.get('ma10', 'N/A')} / MA20: {technical_data.get('ma20', 'N/A')}
MA60: {technical_data.get('ma60', 'N/A')} / MA120: {technical_data.get('ma120', 'N/A')}

技術指標:
KD: K={technical_data.get('k', 'N/A')}, D={technical_data.get('d', 'N/A')}
MACD: DIF={technical_data.get('macd_dif', 'N/A')}, MACD={technical_data.get('macd', 'N/A')}
RSI: {technical_data.get('rsi', 'N/A')}

=== 近期新聞 ===
{news_text}

=== 評分 ===
籌碼面: {scores.get('chip', 0)} 分
基本面: {scores.get('fundamental', 0)} 分
技術面: {scores.get('technical', 0)} 分
總分: {scores.get('total', 0)} 分
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


def _format_margin(data: dict) -> str:
    """Format margin trading data."""
    if not data:
        return "無資料"
    margin_bal = data.get('margin_balance', 'N/A')
    margin_chg = data.get('margin_change', 'N/A')
    short_bal = data.get('short_balance', 'N/A')
    short_chg = data.get('short_change', 'N/A')
    m_chg_str = f"{margin_chg:+}" if isinstance(margin_chg, (int, float)) else str(margin_chg)
    s_chg_str = f"{short_chg:+}" if isinstance(short_chg, (int, float)) else str(short_chg)
    return f"融資餘額: {margin_bal} 張 (變化: {m_chg_str} 張)\n融券餘額: {short_bal} 張 (變化: {s_chg_str} 張)"


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
        "recommendation": {
            "type": "string",
            "description": "綜合建議 (必須包含免責聲明)"
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
