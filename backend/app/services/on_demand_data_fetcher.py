"""On-demand data fetcher for stocks not covered by daily pipeline."""
import logging
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from app.config import settings
from app.services.finmind_collector import FinMindCollector
from app.models.institutional import Institutional
from app.models.margin_trading import MarginTrading
from app.models.revenue import Revenue
from app.models.financial import Financial
from app.models.daily_price import DailyPrice

logger = logging.getLogger(__name__)

# Data considered fresh if exists within this many days
FRESHNESS_DAYS = 30


class OnDemandDataFetcher:
    """Fetch missing stock data on-demand from FinMind API."""

    def __init__(self, db: Session):
        self.db = db
        self.finmind = FinMindCollector(token=settings.FINMIND_TOKEN)

    def check_data_freshness(self, stock_id: str) -> dict[str, bool]:
        """Check if each data type has recent data in DB."""
        cutoff = date.today() - timedelta(days=FRESHNESS_DAYS)
        return {
            "institutional": self.db.query(Institutional).filter(
                Institutional.stock_id == stock_id,
                Institutional.trade_date >= cutoff,
            ).first() is not None,
            "margin": self.db.query(MarginTrading).filter(
                MarginTrading.stock_id == stock_id,
                MarginTrading.trade_date >= cutoff,
            ).first() is not None,
            "revenue": self.db.query(Revenue).filter(
                Revenue.stock_id == stock_id,
            ).first() is not None,
            "financial": self.db.query(Financial).filter(
                Financial.stock_id == stock_id,
            ).first() is not None,
            "prices": self.db.query(DailyPrice).filter(
                DailyPrice.stock_id == stock_id,
                DailyPrice.trade_date >= cutoff,
            ).count() >= 10,
        }

    def fetch_missing_data(self, stock_id: str) -> dict:
        """Fetch and save missing data types. Returns summary."""
        freshness = self.check_data_freshness(stock_id)
        fetched, skipped, failed = [], [], []
        today = date.today()

        for data_type, is_fresh in freshness.items():
            if is_fresh:
                skipped.append(data_type)
                continue
            try:
                count = self._fetch_and_save(stock_id, data_type, today)
                if count > 0:
                    fetched.append(data_type)
                else:
                    skipped.append(data_type)
            except Exception as e:
                logger.warning(f"On-demand fetch {data_type} failed for {stock_id}: {e}")
                failed.append(data_type)

        self.db.commit()
        result = {"fetched": fetched, "skipped": skipped, "failed": failed}
        logger.info(f"On-demand fetch for {stock_id}: {result}")
        return result

    def _fetch_and_save(self, stock_id: str, data_type: str, today: date) -> int:
        """Dispatch fetch+save by data type. Returns saved count."""
        if data_type == "institutional":
            return self._save_institutional(stock_id, today)
        elif data_type == "margin":
            return self._save_margin(stock_id, today)
        elif data_type == "revenue":
            return self._save_revenue(stock_id, today)
        elif data_type == "financial":
            return self._save_financial(stock_id, today)
        elif data_type == "prices":
            return self._save_prices(stock_id, today)
        return 0

    def _save_prices(self, stock_id: str, today: date) -> int:
        """Fetch and save historical prices from FinMind."""
        start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        df = self.finmind.fetch_daily_prices(stock_id, start, end)
        if df is None or df.empty:
            return 0
        saved = 0
        for _, row in df.iterrows():
            trade_date = row["date"]
            exists = self.db.query(DailyPrice).filter_by(
                stock_id=stock_id, trade_date=trade_date
            ).first()
            if not exists:
                self.db.add(DailyPrice(
                    stock_id=stock_id, trade_date=trade_date,
                    open=row.get("open"), high=row.get("max"),
                    low=row.get("min"), close=row.get("close"),
                    volume=int(row.get("Trading_Volume", 0)),
                ))
                saved += 1
        return saved

    def _save_institutional(self, stock_id: str, today: date) -> int:
        """Fetch and save institutional data from FinMind."""
        start = (today - timedelta(days=45)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        df = self.finmind.fetch_institutional(stock_id, start, end)
        if df is None or df.empty:
            return 0
        saved = 0
        for trade_date, grp in df.groupby("date"):
            if self.db.query(Institutional).filter_by(
                stock_id=stock_id, trade_date=trade_date
            ).first():
                continue
            vals = {}
            for _, row in grp.iterrows():
                name = row.get("name", "")
                buy = int(row.get("buy", 0))
                sell = int(row.get("sell", 0))
                if "外資" in name or "Foreign" in name:
                    vals["foreign_buy"] = vals.get("foreign_buy", 0) + buy
                    vals["foreign_sell"] = vals.get("foreign_sell", 0) + sell
                elif "投信" in name or "Investment_Trust" in name:
                    vals["trust_buy"] = vals.get("trust_buy", 0) + buy
                    vals["trust_sell"] = vals.get("trust_sell", 0) + sell
                elif "自營" in name or "Dealer" in name:
                    vals["dealer_buy"] = vals.get("dealer_buy", 0) + buy
                    vals["dealer_sell"] = vals.get("dealer_sell", 0) + sell
            fb, fs = vals.get("foreign_buy", 0), vals.get("foreign_sell", 0)
            tb, ts = vals.get("trust_buy", 0), vals.get("trust_sell", 0)
            db_, ds = vals.get("dealer_buy", 0), vals.get("dealer_sell", 0)
            self.db.add(Institutional(
                stock_id=stock_id, trade_date=trade_date,
                foreign_buy=fb, foreign_sell=fs, foreign_net=fb - fs,
                trust_buy=tb, trust_sell=ts, trust_net=tb - ts,
                dealer_buy=db_, dealer_sell=ds, dealer_net=db_ - ds,
                total_net=(fb - fs) + (tb - ts) + (db_ - ds),
            ))
            saved += 1
        return saved

    def _save_margin(self, stock_id: str, today: date) -> int:
        """Fetch and save margin trading data from FinMind."""
        start = (today - timedelta(days=25)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        df = self.finmind.fetch_margin_trading(stock_id, start, end)
        if df is None or df.empty:
            return 0
        saved = 0
        for _, row in df.iterrows():
            trade_date = row.get("date")
            if not trade_date:
                continue
            row_sid = str(row.get("stock_id", stock_id))
            if not row_sid.isdigit():
                continue
            if self.db.query(MarginTrading).filter_by(
                stock_id=stock_id, trade_date=trade_date
            ).first():
                continue
            self.db.add(MarginTrading(
                stock_id=stock_id, trade_date=trade_date,
                margin_buy=int(row.get("MarginPurchaseBuy", 0)),
                margin_sell=int(row.get("MarginPurchaseSell", 0)),
                margin_balance=int(row.get("MarginPurchaseTodayBalance", 0)),
                margin_change=int(row.get("MarginPurchaseChange", 0)),
                short_buy=int(row.get("ShortSaleBuy", 0)),
                short_sell=int(row.get("ShortSaleSell", 0)),
                short_balance=int(row.get("ShortSaleTodayBalance", 0)),
                short_change=int(row.get("ShortSaleChange", 0)),
            ))
            saved += 1
        return saved

    def _save_revenue(self, stock_id: str, today: date) -> int:
        """Fetch and save revenue data from FinMind with YoY calculation."""
        start = (today - timedelta(days=550)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        df = self.finmind.fetch_revenue(stock_id, start, end)
        if df is None or df.empty:
            return 0
        df = df.sort_values("date")
        # Build revenue lookup for YoY/MoM
        rev_map = {str(row["date"]): int(row.get("revenue", 0)) for _, row in df.iterrows()}
        saved = 0
        for _, row in df.iterrows():
            rev_date = row["date"]
            if self.db.query(Revenue).filter_by(
                stock_id=stock_id, revenue_date=rev_date
            ).first():
                continue
            revenue_val = int(row.get("revenue", 0))
            from dateutil.relativedelta import relativedelta
            rev_dt = datetime.strptime(str(rev_date), "%Y-%m-%d")
            yoy_key = (rev_dt - relativedelta(years=1)).strftime("%Y-%m-%d")
            mom_key = (rev_dt - relativedelta(months=1)).strftime("%Y-%m-%d")
            yoy_rev = rev_map.get(yoy_key, 0)
            mom_rev = rev_map.get(mom_key, 0)
            yoy = ((revenue_val - yoy_rev) / yoy_rev * 100) if yoy_rev > 0 else 0
            mom = ((revenue_val - mom_rev) / mom_rev * 100) if mom_rev > 0 else 0
            self.db.add(Revenue(
                stock_id=stock_id, revenue_date=rev_date,
                revenue=revenue_val,
                revenue_yoy=round(yoy, 2),
                revenue_mom=round(mom, 2),
            ))
            saved += 1
        return saved

    def _save_financial(self, stock_id: str, today: date) -> int:
        """Fetch and save quarterly financial data from FinMind."""
        start = (today - timedelta(days=730)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        inc_df = self.finmind.fetch_financial(stock_id, start, end)
        if inc_df is None or inc_df.empty:
            return 0
        bs_df = self.finmind._get(
            "TaiwanStockBalanceSheet", data_id=stock_id,
            start_date=start, end_date=end,
        )
        cf_df = self.finmind._get(
            "TaiwanStockCashFlowsStatement", data_id=stock_id,
            start_date=start, end_date=end,
        )
        saved = 0
        for qdate, grp in inc_df.groupby("date"):
            if self.db.query(Financial).filter_by(
                stock_id=stock_id, report_date=qdate
            ).first():
                continue
            vals = dict(zip(grp["type"], grp["value"]))
            eps = vals.get("EPS", 0)
            revenue = vals.get("Revenue", 0)
            gross_profit = vals.get("GrossProfit", 0)
            op_income = vals.get("OperatingIncome", 0)
            gross_margin = (gross_profit / revenue * 100) if revenue else None
            op_margin = (op_income / revenue * 100) if revenue else None
            roe_val, debt_ratio_val, ocf, fcf = None, None, None, None
            if bs_df is not None and not bs_df.empty:
                bs_q = bs_df[bs_df["date"] == qdate]
                if not bs_q.empty:
                    bs_vals = dict(zip(bs_q["type"], bs_q["value"]))
                    total_assets = bs_vals.get("TotalAssets", 0)
                    liabilities = bs_vals.get("Liabilities", 0)
                    equity = bs_vals.get("Equity", 0)
                    debt_ratio_val = (liabilities / total_assets * 100) if total_assets else None
                    net_income = vals.get("IncomeAfterTaxes", 0)
                    roe_val = (net_income / equity * 100) if equity else None
            if cf_df is not None and not cf_df.empty:
                cf_q = cf_df[cf_df["date"] == qdate]
                if not cf_q.empty:
                    cf_vals = dict(zip(cf_q["type"], cf_q["value"]))
                    ocf = int(cf_vals.get(
                        "CashFlowsFromOperatingActivities",
                        cf_vals.get("NetCashInflowFromOperatingActivities", 0)
                    ) or 0)
                    capex = abs(int(cf_vals.get("PropertyAndPlantAndEquipment", 0) or 0))
                    fcf = ocf - capex if ocf else None
            self.db.add(Financial(
                stock_id=stock_id, report_date=qdate,
                eps=round(float(eps), 4),
                gross_margin=round(gross_margin, 4) if gross_margin else None,
                operating_margin=round(op_margin, 4) if op_margin else None,
                roe=round(roe_val, 4) if roe_val else None,
                debt_ratio=round(debt_ratio_val, 4) if debt_ratio_val else None,
                operating_cash_flow=ocf, free_cash_flow=fcf,
            ))
            saved += 1
        return saved
