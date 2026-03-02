"""TWSE Open Data collector - free, no auth, all stocks at once."""
import logging
import time
from datetime import date, timedelta
from typing import Any, List, Dict, Optional
import requests

logger = logging.getLogger(__name__)

TWSE_OPENAPI = "https://openapi.twse.com.tw/v1/exchangeReport"
TWSE_STOCK_DAY = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
TWSE_MI_INDEX = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"


class TWSECollector:
    """Collector for TWSE Open Data (free, no API key needed)."""

    def fetch_latest_prices(self) -> List[Dict]:
        """
        Fetch latest trading day prices for ALL stocks (1 API call).

        Returns:
            List of dicts with stock_id, date, open, high, low, close, volume
        """
        try:
            resp = requests.get(
                f"{TWSE_OPENAPI}/STOCK_DAY_ALL",
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code != 200:
                logger.error(f"TWSE API error: {resp.status_code}")
                return []

            raw = resp.json()
            if not raw:
                return []

            results = []
            for item in raw:
                code = item.get("Code", "")
                # Skip non-numeric stock codes (ETFs like 0050 are fine)
                if not code or not code[0].isdigit():
                    continue

                # Parse ROC date (1150211) to western date (2026-02-11)
                roc_date = item.get("Date", "")
                if len(roc_date) == 7:
                    year = int(roc_date[:3]) + 1911
                    month = roc_date[3:5]
                    day = roc_date[5:7]
                    trade_date = f"{year}-{month}-{day}"
                else:
                    continue

                try:
                    results.append({
                        "stock_id": code,
                        "stock_name": item.get("Name", code).strip(),
                        "trade_date": trade_date,
                        "open": float(item.get("OpeningPrice", 0) or 0),
                        "high": float(item.get("HighestPrice", 0) or 0),
                        "low": float(item.get("LowestPrice", 0) or 0),
                        "close": float(item.get("ClosingPrice", 0) or 0),
                        "volume": int(item.get("TradeVolume", 0) or 0),
                    })
                except (ValueError, TypeError):
                    continue

            logger.info(f"TWSE: fetched {len(results)} stocks for {results[0]['trade_date'] if results else '?'}")
            return results

        except Exception as e:
            logger.error(f"TWSE fetch failed: {e}")
            return []

    def fetch_latest_prices_fallback(self, date_str: str) -> List[Dict]:
        """
        Fallback: fetch all stock prices via MI_INDEX endpoint.

        Use when STOCK_DAY_ALL (OpenAPI) is stale. MI_INDEX updates faster
        and returns the same data (1 API call, all stocks).
        """
        try:
            twse_date = date_str.replace("-", "")
            resp = requests.get(
                TWSE_MI_INDEX,
                params={
                    "date": twse_date,
                    "type": "ALLBUT0999",
                    "response": "json",
                },
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code != 200:
                logger.error(f"TWSE MI_INDEX error: {resp.status_code}")
                return []

            data = resp.json()
            if data.get("stat") != "OK":
                return []

            # Price table is typically at index 8
            price_table = None
            for t in data.get("tables", []):
                if t.get("data") and len(t["data"]) > 100:
                    fields = t.get("fields", [])
                    if "證券代號" in fields and "收盤價" in fields:
                        price_table = t
                        break

            if not price_table:
                logger.warning("MI_INDEX: price table not found")
                return []

            def clean_num(s):
                return str(s).replace(",", "").strip()

            results = []
            for row in price_table["data"]:
                code = str(row[0]).strip()
                if not code or not code[0].isdigit():
                    continue
                try:
                    volume = int(clean_num(row[2]) or 0)
                    open_p = float(clean_num(row[5]) or 0)
                    high = float(clean_num(row[6]) or 0)
                    low = float(clean_num(row[7]) or 0)
                    close = float(clean_num(row[8]) or 0)
                    if close == 0:
                        continue
                    name = str(row[1]).strip() if len(row) > 1 else code
                    results.append({
                        "stock_id": code,
                        "stock_name": name,
                        "trade_date": date_str,
                        "open": open_p,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                    })
                except (ValueError, TypeError, IndexError):
                    continue

            logger.info(f"TWSE MI_INDEX fallback: {len(results)} stocks for {date_str}")
            return results

        except Exception as e:
            logger.error(f"TWSE MI_INDEX fallback failed: {e}")
            return []

    def fetch_per_ratio(self) -> List[Dict]:
        """
        Fetch latest PER/PBR/Dividend yield for all stocks.

        Returns:
            List of dicts with stock_id, per, pbr, dividend_yield
        """
        try:
            resp = requests.get(
                f"{TWSE_OPENAPI}/BWIBBU_ALL",
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code != 200:
                return []

            raw = resp.json()
            results = []
            for item in raw:
                code = item.get("Code", "")
                if not code or not code[0].isdigit():
                    continue
                try:
                    results.append({
                        "stock_id": code,
                        "per": float(item.get("PEratio", 0) or 0),
                        "pbr": float(item.get("PBratio", 0) or 0),
                        "dividend_yield": float(item.get("DividendYield", 0) or 0),
                    })
                except (ValueError, TypeError):
                    continue

            logger.info(f"TWSE: fetched PER/PBR for {len(results)} stocks")
            return results

        except Exception as e:
            logger.error(f"TWSE PER fetch failed: {e}")
            return []

    def fetch_institutional_all(self, date_str: str) -> List[Dict]:
        """
        Fetch institutional buy/sell for ALL stocks (TWSE T86, 1 API call).

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            List of dicts with stock_id, trade_date, foreign/trust/dealer data
        """
        try:
            # Convert to YYYYMMDD format
            twse_date = date_str.replace("-", "")
            resp = requests.get(
                f"https://www.twse.com.tw/rwd/zh/fund/T86"
                f"?date={twse_date}&selectType=ALL&response=json",
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code != 200:
                logger.error(f"TWSE T86 error: {resp.status_code}")
                return []

            data = resp.json()
            rows = data.get("data", [])
            if not rows:
                return []

            def parse_int(s):
                return int(str(s).replace(",", "").strip() or 0)

            results = []
            for row in rows:
                code = str(row[0]).strip()
                if not code or not code[0].isdigit():
                    continue
                try:
                    f_buy = parse_int(row[2])
                    f_sell = parse_int(row[3])
                    t_buy = parse_int(row[8])
                    t_sell = parse_int(row[9])
                    d_buy = parse_int(row[12]) + parse_int(row[15])
                    d_sell = parse_int(row[13]) + parse_int(row[16])
                    results.append({
                        "stock_id": code,
                        "trade_date": date_str,
                        "foreign_buy": f_buy,
                        "foreign_sell": f_sell,
                        "foreign_net": f_buy - f_sell,
                        "trust_buy": t_buy,
                        "trust_sell": t_sell,
                        "trust_net": t_buy - t_sell,
                        "dealer_buy": d_buy,
                        "dealer_sell": d_sell,
                        "dealer_net": d_buy - d_sell,
                        "total_net": (f_buy - f_sell) + (t_buy - t_sell) + (d_buy - d_sell),
                    })
                except (ValueError, IndexError):
                    continue

            logger.info(f"TWSE T86: {len(results)} institutional records for {date_str}")
            return results

        except Exception as e:
            logger.error(f"TWSE T86 fetch failed: {e}")
            return []

    def fetch_margin_all(self) -> List[Dict]:
        """
        Fetch margin trading for ALL stocks (TWSE MI_MARGN, 1 API call).

        Returns:
            List of dicts with stock_id, margin_balance, short_balance
        """
        try:
            resp = requests.get(
                "https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN",
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code != 200:
                logger.error(f"TWSE MI_MARGN error: {resp.status_code}")
                return []

            raw = resp.json()
            if not raw:
                return []

            def parse_int(s):
                return int(str(s).replace(",", "").strip() or 0)

            results = []
            for item in raw:
                code = item.get("股票代號", "").strip()
                if not code or not code[0].isdigit():
                    continue
                try:
                    results.append({
                        "stock_id": code,
                        "margin_balance": parse_int(item.get("融資今日餘額", 0)),
                        "short_balance": parse_int(item.get("融券今日餘額", 0)),
                    })
                except (ValueError, TypeError):
                    continue

            logger.info(f"TWSE MI_MARGN: {len(results)} margin records")
            return results

        except Exception as e:
            logger.error(f"TWSE margin fetch failed: {e}")
            return []

    def _parse_revenue_items(self, raw: list) -> List[Dict]:
        """Parse revenue JSON items from TWSE OpenAPI endpoint."""
        results = []
        for item in raw:
            code = item.get("公司代號", "")
            if not code or not code[0].isdigit():
                continue

            # Parse ROC year-month (11501 → 2026-01)
            roc_ym = item.get("資料年月", "")
            if len(roc_ym) >= 4:
                year = int(roc_ym[:3]) + 1911
                month = int(roc_ym[3:])
                revenue_date = f"{year}-{month:02d}-01"
            else:
                continue

            try:
                revenue = int(item.get("營業收入-當月營收", 0) or 0)
                yoy_str = item.get("營業收入-去年同月增減(%)", "0") or "0"
                mom_str = item.get("營業收入-上月比較增減(%)", "0") or "0"
                yoy = float(yoy_str) if yoy_str != "-" else 0.0
                mom = float(mom_str) if mom_str != "-" else 0.0

                results.append({
                    "stock_id": code,
                    "revenue_date": revenue_date,
                    "revenue": revenue,
                    "revenue_yoy": round(yoy, 4),
                    "revenue_mom": round(mom, 4),
                })
            except (ValueError, TypeError):
                continue
        return results

    def fetch_monthly_revenue(self) -> List[Dict]:
        """
        Fetch latest monthly revenue for ALL companies (listed + OTC).

        Calls both t187ap05_L (上市) and t187ap05_P (上櫃) endpoints.
        TWSE data already includes pre-calculated YoY% and MoM%.

        Returns:
            List of dicts with stock_id, revenue_date, revenue, yoy, mom
        """
        endpoints = [
            ("t187ap05_L", "上市"),
            ("t187ap05_P", "上櫃"),
        ]
        all_results = []
        for endpoint, label in endpoints:
            try:
                resp = requests.get(
                    f"https://openapi.twse.com.tw/v1/opendata/{endpoint}",
                    timeout=30,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code != 200:
                    logger.error(f"TWSE revenue {label} ({endpoint}) error: {resp.status_code}")
                    continue

                raw = resp.json()
                if not raw:
                    continue

                parsed = self._parse_revenue_items(raw)
                logger.info(f"TWSE revenue {label}: {len(parsed)} companies")
                all_results.extend(parsed)

            except Exception as e:
                logger.error(f"TWSE revenue {label} fetch failed: {e}")
                continue

        logger.info(f"TWSE: fetched revenue for {len(all_results)} companies total")
        return all_results

    def fetch_quarterly_financials(self) -> List[Dict]:
        """
        Fetch quarterly financial data from TWSE OpenAPI streaming endpoints.

        Combines data from:
        - t187ap06_L_ci: Income statement (EPS, Revenue, GrossProfit, OperatingIncome)
        - t187ap07_L_ci: Balance sheet (TotalAssets, Liabilities, Equity)
        - t187ap17_L: Profitability ratios (gross margin, operating margin)

        NOTE: These endpoints only return companies that filed TODAY.
        During filing season, ~15-25 companies per day. Needs daily accumulation.
        No cash flow data available — operating_cash_flow/free_cash_flow will be null.

        Returns:
            List of dicts compatible with Financial model fields.
        """
        # Step 1: Fetch income statement data
        income_map = {}  # key: (stock_id, report_date)
        try:
            resp = requests.get(
                "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci",
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                raw = resp.json() or []
                for item in raw:
                    code = item.get("公司代號", "")
                    if not code or not code[0].isdigit():
                        continue
                    # Parse report date from ROC format
                    roc_ym = item.get("資料年度", "")
                    season = item.get("資料季別", "")
                    if not roc_ym or not season:
                        continue
                    try:
                        year = int(roc_ym) + 1911
                        quarter = int(season)
                        quarter_month = {1: 3, 2: 6, 3: 9, 4: 12}
                        month = quarter_month.get(quarter, 12)
                        report_date = f"{year}-{month:02d}-01"

                        eps = float(item.get("基本每股盈餘（元）", 0) or 0)
                        revenue = int(float(item.get("營業收入", 0) or 0))
                        gross_profit = int(float(item.get("營業毛利（毛損）", 0) or 0))
                        op_income = int(float(item.get("營業利益（損失）", 0) or 0))
                        net_income = int(float(item.get("本期淨利（淨損）", 0) or 0))

                        income_map[(code, report_date)] = {
                            "stock_id": code,
                            "report_date": report_date,
                            "eps": round(eps, 4),
                            "revenue": revenue,
                            "gross_profit": gross_profit,
                            "operating_income": op_income,
                            "net_income": net_income,
                        }
                    except (ValueError, TypeError):
                        continue
                logger.info(f"TWSE income statement: {len(income_map)} records")
        except Exception as e:
            logger.error(f"TWSE income statement fetch failed: {e}")

        # Step 2: Fetch balance sheet data
        balance_map = {}  # key: (stock_id, report_date)
        try:
            resp = requests.get(
                "https://openapi.twse.com.tw/v1/opendata/t187ap07_L_ci",
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                raw = resp.json() or []
                for item in raw:
                    code = item.get("公司代號", "")
                    if not code or not code[0].isdigit():
                        continue
                    roc_ym = item.get("資料年度", "")
                    season = item.get("資料季別", "")
                    if not roc_ym or not season:
                        continue
                    try:
                        year = int(roc_ym) + 1911
                        quarter = int(season)
                        quarter_month = {1: 3, 2: 6, 3: 9, 4: 12}
                        month = quarter_month.get(quarter, 12)
                        report_date = f"{year}-{month:02d}-01"

                        total_assets = float(item.get("資產總計", 0) or 0)
                        liabilities = float(item.get("負債總計", 0) or 0)
                        equity = float(item.get("權益總計", 0) or 0)

                        balance_map[(code, report_date)] = {
                            "total_assets": total_assets,
                            "liabilities": liabilities,
                            "equity": equity,
                        }
                    except (ValueError, TypeError):
                        continue
                logger.info(f"TWSE balance sheet: {len(balance_map)} records")
        except Exception as e:
            logger.error(f"TWSE balance sheet fetch failed: {e}")

        # Step 3: Combine into Financial-compatible records
        results = []
        for key, inc in income_map.items():
            revenue = inc["revenue"]
            gross_profit = inc["gross_profit"]
            op_income = inc["operating_income"]
            gross_margin = (gross_profit / revenue * 100) if revenue else None
            op_margin = (op_income / revenue * 100) if revenue else None

            roe_val = None
            debt_ratio_val = None
            bs = balance_map.get(key)
            if bs:
                total_assets = bs["total_assets"]
                liabilities = bs["liabilities"]
                equity = bs["equity"]
                debt_ratio_val = (liabilities / total_assets * 100) if total_assets else None
                net_income = inc["net_income"]
                roe_val = (net_income / equity * 100) if equity else None

            results.append({
                "stock_id": inc["stock_id"],
                "report_date": inc["report_date"],
                "eps": inc["eps"],
                "gross_margin": round(gross_margin, 4) if gross_margin else None,
                "operating_margin": round(op_margin, 4) if op_margin else None,
                "roe": round(roe_val, 4) if roe_val else None,
                "debt_ratio": round(debt_ratio_val, 4) if debt_ratio_val else None,
                "operating_cash_flow": None,  # TWSE has no cash flow endpoint
                "free_cash_flow": None,
            })

        logger.info(f"TWSE quarterly financials: {len(results)} combined records")
        return results

    def fetch_stock_history(
        self, stock_id: str, months: int = 8
    ) -> List[Dict]:
        """
        Fetch historical daily prices for a single stock from TWSE.

        Uses STOCK_DAY API (1 month per call, free, no auth).

        Args:
            stock_id: Stock code (e.g., '2330')
            months: Number of months to fetch back

        Returns:
            List of dicts with stock_id, trade_date, open, high, low, close, volume
        """
        results = []
        current = date.today()

        for m in range(months):
            target = date(current.year, current.month, 1) - timedelta(days=30 * m)
            twse_date = target.strftime("%Y%m01")

            try:
                resp = requests.get(
                    TWSE_STOCK_DAY,
                    params={
                        "date": twse_date,
                        "stockNo": stock_id,
                        "response": "json",
                    },
                    timeout=15,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code != 200:
                    continue

                data = resp.json()
                if data.get("stat") != "OK":
                    continue

                for row in data.get("data", []):
                    try:
                        # Parse ROC date (115/02/11 → 2026-02-11)
                        parts = row[0].split("/")
                        year = int(parts[0]) + 1911
                        trade_date = f"{year}-{parts[1]}-{parts[2]}"

                        def clean_num(s):
                            return s.replace(",", "").strip()

                        results.append({
                            "stock_id": stock_id,
                            "trade_date": trade_date,
                            "open": float(clean_num(row[3]) or 0),
                            "high": float(clean_num(row[4]) or 0),
                            "low": float(clean_num(row[5]) or 0),
                            "close": float(clean_num(row[6]) or 0),
                            "volume": int(clean_num(row[1]) or 0),
                        })
                    except (ValueError, IndexError):
                        continue

                # TWSE rate limit: wait 3s between requests
                time.sleep(3)

            except Exception as e:
                logger.warning(f"TWSE STOCK_DAY error for {stock_id}/{twse_date}: {e}")
                continue

        logger.info(f"TWSE history: {len(results)} days for {stock_id}")
        return results
