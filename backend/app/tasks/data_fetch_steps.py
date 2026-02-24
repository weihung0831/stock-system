"""Data fetching steps for pipeline - hybrid TWSE OpenAPI + FinMind."""
import logging
import time
from datetime import datetime, date, timedelta
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.config import settings
from app.services.finmind_collector import FinMindCollector
from app.services.twse_collector import TWSECollector
from app.services.news_collector import NewsCollector
from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.models.institutional import Institutional
from app.models.margin_trading import MarginTrading
from app.models.revenue import Revenue
from app.models.financial import Financial
from app.models.news import News

logger = logging.getLogger(__name__)

# Priority stocks for FinMind per-stock fetching (institutional/margin)
PRIORITY_STOCKS = [
    # 半導體
    '2330', '2303', '2454', '3711', '2379',
    # 金融
    '2881', '2882', '2883', '2884', '2885', '2886', '2887', '2888',
    '2889', '2890', '2891', '2892', '5880',
    # 電子
    '2317', '2308', '2382', '3008', '2357', '2327', '3034', '2345',
    '2395', '2377', '2301', '2356', '6505', '2474',
    # 傳產
    '1301', '1303', '1326', '2002', '1101', '1102', '2207', '9910',
    '1216', '2912', '2105', '9904',
    # 航運
    '2603', '2609', '2615',
    # 電信
    '2412', '3682', '4904',
]


def _get_top_stocks_by_volume(db: Session, limit: int = 100) -> List[str]:
    """Get top N stock IDs by latest day volume."""
    from sqlalchemy import func as sqlfunc, desc
    max_date = db.query(sqlfunc.max(DailyPrice.trade_date)).scalar()
    if not max_date:
        return []
    rows = (
        db.query(DailyPrice.stock_id)
        .filter(DailyPrice.trade_date == max_date)
        .order_by(desc(DailyPrice.volume))
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows]


def _stocks_needing_backfill(
    db: Session, stock_ids: List[str], min_days: int = 120
) -> List[str]:
    """Return stock IDs that have fewer than min_days of price data."""
    from sqlalchemy import func as sqlfunc
    counts = (
        db.query(DailyPrice.stock_id, sqlfunc.count(DailyPrice.trade_date))
        .filter(DailyPrice.stock_id.in_(stock_ids))
        .group_by(DailyPrice.stock_id)
        .all()
    )
    existing = {sid: cnt for sid, cnt in counts}
    need = [sid for sid in stock_ids if existing.get(sid, 0) < min_days]
    return need


def _save_twse_prices(db: Session, prices: List[Dict]) -> int:
    """Save TWSE latest prices to DB, skip duplicates (batch check)."""
    if not prices:
        return 0

    # Batch: pre-fetch existing price keys and stock IDs
    trade_date = prices[0]["trade_date"]
    existing_price_ids = set(
        r[0] for r in db.query(DailyPrice.stock_id)
        .filter(DailyPrice.trade_date == trade_date).all()
    )
    existing_stock_ids = set(
        r[0] for r in db.query(Stock.stock_id).all()
    )

    saved = 0
    for p in prices:
        sid = p["stock_id"]
        if sid not in existing_stock_ids:
            db.add(Stock(stock_id=sid, stock_name=sid, market="TWSE"))
            existing_stock_ids.add(sid)

        if sid not in existing_price_ids:
            db.add(DailyPrice(
                stock_id=sid,
                trade_date=trade_date,
                open=p["open"],
                high=p["high"],
                low=p["low"],
                close=p["close"],
                volume=p["volume"],
            ))
            saved += 1

        if saved % 200 == 0 and saved > 0:
            db.commit()

    db.commit()
    return saved


def _fetch_finmind_prices_batch(
    collector: FinMindCollector,
    db: Session,
    stock_ids: List[str],
    start_date: str,
    end_date: str,
) -> tuple[int, bool]:
    """Fetch historical prices via FinMind per-stock API.

    Returns:
        (saved_count, quota_exhausted) tuple.
    """
    from app.services.finmind_collector import FinMindQuotaExhausted

    saved = 0
    total = len(stock_ids)
    for i, sid in enumerate(stock_ids):
        if i > 0 and i % 30 == 0:
            logger.info(f"  FinMind progress: {i}/{total}, {saved} saved")

        try:
            df = collector.fetch_daily_prices(sid, start_date, end_date)
        except FinMindQuotaExhausted:
            logger.warning(
                f"FinMind quota exhausted at {i}/{total}, "
                f"saved {saved} so far. Remaining stocks need TWSE fallback."
            )
            db.commit()
            return saved, True

        if df is None or df.empty:
            continue

        for _, row in df.iterrows():
            trade_date = row['date']
            existing = db.query(DailyPrice).filter_by(
                stock_id=sid, trade_date=trade_date
            ).first()
            if not existing:
                db.add(DailyPrice(
                    stock_id=sid,
                    trade_date=trade_date,
                    open=row.get('open'),
                    high=row.get('max'),
                    low=row.get('min'),
                    close=row.get('close'),
                    volume=int(row.get('Trading_Volume', 0))
                ))
                saved += 1

        if i % 20 == 0:
            db.commit()

    db.commit()
    return saved, False


def _fetch_twse_history_batch(
    twse: 'TWSECollector',
    db: Session,
    stock_ids: List[str],
    months: int = 8,
) -> int:
    """Fetch historical prices via TWSE STOCK_DAY API (free, per-stock)."""
    saved = 0
    total = len(stock_ids)
    for i, sid in enumerate(stock_ids):
        if i > 0 and i % 10 == 0:
            logger.info(f"  TWSE history progress: {i}/{total}, {saved} saved")

        prices = twse.fetch_stock_history(sid, months=months)
        for p in prices:
            existing = db.query(DailyPrice).filter_by(
                stock_id=sid, trade_date=p["trade_date"]
            ).first()
            if not existing:
                # Ensure stock exists
                stock = db.query(Stock).filter_by(stock_id=sid).first()
                if not stock:
                    db.add(Stock(stock_id=sid, stock_name=sid, market="TWSE"))
                    db.flush()

                db.add(DailyPrice(
                    stock_id=sid,
                    trade_date=p["trade_date"],
                    open=p["open"],
                    high=p["high"],
                    low=p["low"],
                    close=p["close"],
                    volume=p["volume"],
                ))
                saved += 1

        if i % 5 == 0:
            db.commit()

    db.commit()
    return saved


def _fetch_finmind_institutional_batch(
    finmind: 'FinMindCollector',
    db: Session,
    stock_ids: List[str],
    start_date: str,
    end_date: str,
) -> tuple[int, bool]:
    """Fetch historical institutional data via FinMind per-stock API.

    Returns:
        (saved_count, quota_exhausted) tuple.
    """
    from app.services.finmind_collector import FinMindQuotaExhausted

    saved = 0
    total = len(stock_ids)
    for i, sid in enumerate(stock_ids):
        if i > 0 and i % 30 == 0:
            logger.info(f"  FinMind inst progress: {i}/{total}, {saved} saved")
        try:
            df = finmind.fetch_institutional(sid, start_date, end_date)
            if df is None or df.empty:
                continue
            for trade_date, grp in df.groupby('date'):
                existing = db.query(Institutional).filter_by(
                    stock_id=sid, trade_date=trade_date
                ).first()
                if existing:
                    continue
                vals = {}
                for _, row in grp.iterrows():
                    name = row.get('name', '')
                    buy = int(row.get('buy', 0))
                    sell = int(row.get('sell', 0))
                    if '外資' in name or 'Foreign' in name:
                        vals['foreign_buy'] = vals.get('foreign_buy', 0) + buy
                        vals['foreign_sell'] = vals.get('foreign_sell', 0) + sell
                    elif '投信' in name or 'Investment_Trust' in name:
                        vals['trust_buy'] = vals.get('trust_buy', 0) + buy
                        vals['trust_sell'] = vals.get('trust_sell', 0) + sell
                    elif '自營' in name or 'Dealer' in name:
                        vals['dealer_buy'] = vals.get('dealer_buy', 0) + buy
                        vals['dealer_sell'] = vals.get('dealer_sell', 0) + sell
                fb = vals.get('foreign_buy', 0)
                fs = vals.get('foreign_sell', 0)
                tb = vals.get('trust_buy', 0)
                ts = vals.get('trust_sell', 0)
                db_ = vals.get('dealer_buy', 0)
                ds = vals.get('dealer_sell', 0)
                db.add(Institutional(
                    stock_id=sid,
                    trade_date=trade_date,
                    foreign_buy=fb, foreign_sell=fs, foreign_net=fb - fs,
                    trust_buy=tb, trust_sell=ts, trust_net=tb - ts,
                    dealer_buy=db_, dealer_sell=ds, dealer_net=db_ - ds,
                    total_net=(fb - fs) + (tb - ts) + (db_ - ds),
                ))
                saved += 1
            if i % 20 == 0:
                db.commit()
        except FinMindQuotaExhausted:
            logger.warning(f"FinMind quota exhausted at inst {i}/{total}, saved {saved}")
            db.commit()
            return saved, True
        except Exception as e:
            logger.warning(f"FinMind institutional error for {sid}: {e}")
            continue
    db.commit()
    return saved, False


def _fetch_finmind_margin_batch(
    finmind: 'FinMindCollector',
    db: Session,
    stock_ids: List[str],
    start_date: str,
    end_date: str,
) -> tuple[int, bool]:
    """Fetch historical margin trading data via FinMind per-stock API.

    Returns:
        (saved_count, quota_exhausted) tuple.
    """
    from app.services.finmind_collector import FinMindQuotaExhausted

    saved = 0
    total = len(stock_ids)
    for i, sid in enumerate(stock_ids):
        if i > 0 and i % 30 == 0:
            logger.info(f"  FinMind margin progress: {i}/{total}, {saved} saved")
        try:
            df = finmind.fetch_margin_trading(sid, start_date, end_date)
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                trade_date = row.get('date')
                if not trade_date:
                    continue
                row_sid = str(row.get('stock_id', sid))
                if not row_sid.isdigit():
                    continue
                existing = db.query(MarginTrading).filter_by(
                    stock_id=sid, trade_date=trade_date
                ).first()
                if existing:
                    continue
                db.add(MarginTrading(
                    stock_id=sid,
                    trade_date=trade_date,
                    margin_buy=int(row.get('MarginPurchaseBuy', 0)),
                    margin_sell=int(row.get('MarginPurchaseSell', 0)),
                    margin_balance=int(row.get('MarginPurchaseTodayBalance', 0)),
                    margin_change=int(row.get('MarginPurchaseChange', 0)),
                    short_buy=int(row.get('ShortSaleBuy', 0)),
                    short_sell=int(row.get('ShortSaleSell', 0)),
                    short_balance=int(row.get('ShortSaleTodayBalance', 0)),
                    short_change=int(row.get('ShortSaleChange', 0)),
                ))
                saved += 1
            if i % 20 == 0:
                db.commit()
        except FinMindQuotaExhausted:
            logger.warning(f"FinMind quota exhausted at margin {i}/{total}, saved {saved}")
            db.commit()
            return saved, True
        except Exception as e:
            logger.warning(f"FinMind margin error for {sid}: {e}")
            continue
    db.commit()
    return saved, False


def _fetch_financials(
    finmind: 'FinMindCollector', db: Session,
    stock_ids: List[str], target_date: date,
) -> tuple[int, bool]:
    """Fetch quarterly financial data from FinMind (3 datasets).

    Returns:
        (saved_count, quota_exhausted) tuple.
    """
    from app.services.finmind_collector import FinMindQuotaExhausted

    logger.info(f"Step G: Fetching financials for {len(stock_ids)} stocks")
    fin_start = (target_date - timedelta(days=730)).strftime("%Y-%m-%d")
    fin_end = target_date.strftime("%Y-%m-%d")
    saved = 0

    for i, sid in enumerate(stock_ids):
        try:
            # Income statement (EPS, gross margin, operating margin)
            inc_df = finmind.fetch_financial(sid, fin_start, fin_end)
            if inc_df is None or inc_df.empty:
                continue

            # Balance sheet (debt ratio, ROE)
            bs_df = finmind._get(
                'TaiwanStockBalanceSheet', data_id=sid,
                start_date=fin_start, end_date=fin_end,
            )
            # Cash flow (operating, free cash flow)
            cf_df = finmind._get(
                'TaiwanStockCashFlowsStatement', data_id=sid,
                start_date=fin_start, end_date=fin_end,
            )

            # Group by quarter date
            for qdate, grp in inc_df.groupby('date'):
                existing = db.query(Financial).filter_by(
                    stock_id=sid, report_date=qdate
                ).first()
                if existing:
                    continue

                vals = dict(zip(grp['type'], grp['value']))
                eps = vals.get('EPS', 0)
                revenue = vals.get('Revenue', 0)
                gross_profit = vals.get('GrossProfit', 0)
                op_income = vals.get('OperatingIncome', 0)
                gross_margin = (gross_profit / revenue * 100) if revenue else None
                op_margin = (op_income / revenue * 100) if revenue else None

                # Balance sheet values for this quarter
                roe_val = None
                debt_ratio_val = None
                if bs_df is not None and not bs_df.empty:
                    bs_q = bs_df[bs_df['date'] == qdate]
                    if not bs_q.empty:
                        bs_vals = dict(zip(bs_q['type'], bs_q['value']))
                        total_assets = bs_vals.get('TotalAssets', 0)
                        liabilities = bs_vals.get('Liabilities', 0)
                        equity = bs_vals.get('Equity', 0)
                        debt_ratio_val = (
                            (liabilities / total_assets * 100) if total_assets else None
                        )
                        net_income = vals.get('IncomeAfterTaxes', 0)
                        roe_val = (net_income / equity * 100) if equity else None

                # Cash flow values
                ocf = None
                fcf = None
                if cf_df is not None and not cf_df.empty:
                    cf_q = cf_df[cf_df['date'] == qdate]
                    if not cf_q.empty:
                        cf_vals = dict(zip(cf_q['type'], cf_q['value']))
                        ocf = int(cf_vals.get(
                            'CashFlowsFromOperatingActivities',
                            cf_vals.get('NetCashInflowFromOperatingActivities', 0)
                        ) or 0)
                        capex = abs(int(cf_vals.get(
                            'PropertyAndPlantAndEquipment', 0
                        ) or 0))
                        fcf = ocf - capex if ocf else None

                db.add(Financial(
                    stock_id=sid,
                    report_date=qdate,
                    eps=round(float(eps), 4),
                    gross_margin=round(gross_margin, 4) if gross_margin else None,
                    operating_margin=round(op_margin, 4) if op_margin else None,
                    roe=round(roe_val, 4) if roe_val else None,
                    debt_ratio=round(debt_ratio_val, 4) if debt_ratio_val else None,
                    operating_cash_flow=ocf,
                    free_cash_flow=fcf,
                ))
                saved += 1

            if i % 10 == 0:
                db.commit()

        except FinMindQuotaExhausted:
            logger.warning(f"FinMind quota exhausted at financials {i}/{len(stock_ids)}, saved {saved}")
            db.commit()
            return saved, True
        except Exception as e:
            logger.warning(f"Financial fetch error for {sid}: {e}")
            continue

    db.commit()
    logger.info(f"Financials saved: {saved}")
    return saved, False


def step_fetch_stock_data(db: Session, date_str: str) -> Dict[str, Any]:
    """
    Hybrid fetch: TWSE OpenAPI bulk + FinMind per-stock.

    Strategy:
    A. Stock list from FinMind (name/industry)
    B. Latest prices from TWSE OpenAPI (1 call, all stocks)
    C. Historical backfill from FinMind (top 100 + priority, per-stock)
    D. Institutional data from TWSE T86 (1 call, all stocks)
    E. Margin data from TWSE MI_MARGN (1 call, all stocks)
    F. Monthly revenue: TWSE bulk + FinMind YoY calc
    G. Quarterly financials from FinMind (top 100 + priority, per-stock)
    """
    try:
        finmind = FinMindCollector(token=settings.FINMIND_TOKEN)
        twse = TWSECollector()
        target_date = date.fromisoformat(date_str)
        finmind_exhausted = False  # Global quota flag

        # Detect incremental (daily) vs initial run
        from sqlalchemy import func as sqlfunc_detect
        latest_db_date = db.query(sqlfunc_detect.max(DailyPrice.trade_date)).scalar()
        is_incremental = (
            latest_db_date is not None
            and (target_date - date.fromisoformat(str(latest_db_date))).days <= 5
        )
        if is_incremental:
            logger.info("Incremental mode: will skip heavy historical fetches")

        # --- Step A: Fetch and save stock list ---
        logger.info("Step A: Fetching stock list from FinMind...")
        stocks = finmind.fetch_stock_list()
        if not stocks:
            logger.warning("FinMind stock list empty, will rely on TWSE data")

        seen_ids = set()
        for s in stocks:
            sid = s['stock_id']
            if sid.isdigit() and sid not in seen_ids:
                seen_ids.add(sid)
                existing = db.query(Stock).filter_by(stock_id=sid).first()
                market_type = s.get('type', '未知')
                if market_type in ('twse', '上市'):
                    market_type = 'TWSE'
                elif market_type in ('tpex', '上櫃'):
                    market_type = 'TPEx'

                if not existing:
                    db.add(Stock(
                        stock_id=sid,
                        stock_name=s['stock_name'],
                        market=market_type,
                        industry=s.get('industry_category')
                    ))
                else:
                    existing.stock_name = s['stock_name']
                    if market_type != '未知':
                        existing.market = market_type
                    if s.get('industry_category'):
                        existing.industry = s.get('industry_category')
        db.commit()
        logger.info(f"Stock list: {len(seen_ids)} stocks saved")

        # --- Step B: Fetch latest prices from TWSE OpenAPI ---
        logger.info("Step B: Fetching latest prices from TWSE OpenAPI...")
        twse_prices = twse.fetch_latest_prices()
        saved_twse = 0
        if twse_prices:
            saved_twse = _save_twse_prices(db, twse_prices)
            logger.info(f"TWSE prices saved: {saved_twse} (total fetched: {len(twse_prices)})")
        else:
            logger.warning("TWSE prices empty (market may be closed)")

        # Step B fallback: if STOCK_DAY_ALL is stale (date != target),
        # use MI_INDEX endpoint which updates faster (1 call, all stocks)
        twse_data_date = twse_prices[0]["trade_date"] if twse_prices else None
        if twse_data_date != date_str:
            logger.warning(
                f"TWSE bulk data is stale ({twse_data_date}), "
                f"trying MI_INDEX fallback for {date_str}"
            )
            fallback_prices = twse.fetch_latest_prices_fallback(date_str)
            if fallback_prices:
                fallback_saved = _save_twse_prices(db, fallback_prices)
                saved_twse += fallback_saved
                logger.info(f"MI_INDEX fallback saved: {fallback_saved}")
            else:
                logger.warning("MI_INDEX fallback also empty")

        # --- Step C: Historical backfill for top stocks ---
        saved_hist = 0
        # Get top 100 by volume from latest TWSE data
        top_stock_ids = _get_top_stocks_by_volume(db, limit=500)
        # Merge with priority stocks for coverage
        all_target_ids = list(set(top_stock_ids) | set(PRIORITY_STOCKS))
        # Filter to valid numeric stock IDs
        all_target_ids = [
            sid for sid in all_target_ids
            if sid.isdigit() or (sid[0].isdigit() and len(sid) <= 6)
        ]
        all_target_ids.sort()

        # Check which stocks need backfill (<30 days for scoring)
        need_backfill = _stocks_needing_backfill(db, all_target_ids, 30)
        if need_backfill:
            # Use FinMind per-stock first (faster, no 3s delay)
            fm_start = (target_date - timedelta(days=180)).strftime("%Y-%m-%d")
            logger.info(
                f"Step C: Backfill {len(need_backfill)}/{len(all_target_ids)} "
                f"stocks via FinMind (6 months)"
            )
            saved_hist, exhausted = _fetch_finmind_prices_batch(
                finmind, db, need_backfill, fm_start, date_str
            )
            if exhausted:
                finmind_exhausted = True
                logger.warning("FinMind quota exhausted during Step C")
            logger.info(f"Historical prices saved: {saved_hist}")

            # Check if any still need more data, use TWSE STOCK_DAY as fallback
            still_need = _stocks_needing_backfill(db, need_backfill, 20)
            if still_need:
                logger.info(
                    f"Step C fallback: {len(still_need)} stocks via TWSE STOCK_DAY "
                    f"(~{len(still_need) * 6}s estimated)"
                )
                # Only fetch 2 months (enough for 20+ trading days) to speed up
                saved_hist += _fetch_twse_history_batch(twse, db, still_need, months=2)
        else:
            logger.info("Step C: All target stocks have 30+ days data")

        # --- Step D: Fetch institutional data ---
        # D-1: TWSE T86 bulk for latest trading day
        from sqlalchemy import func as sqlfunc
        max_trade_date = db.query(sqlfunc.max(DailyPrice.trade_date)).scalar()
        inst_date = str(max_trade_date) if max_trade_date else date_str
        logger.info(f"Step D-1: TWSE bulk institutional for {inst_date}")
        saved_inst = 0
        inst_data = twse.fetch_institutional_all(inst_date)
        # Batch: pre-fetch existing institutional stock IDs for this date
        existing_inst_ids = set(
            r[0] for r in db.query(Institutional.stock_id)
            .filter(Institutional.trade_date == inst_date).all()
        )
        for item in inst_data:
            if item["stock_id"] in existing_inst_ids:
                continue
            db.add(Institutional(**item))
            saved_inst += 1
            if saved_inst % 500 == 0:
                db.commit()
        db.commit()
        logger.info(f"TWSE T86 institutional saved: {saved_inst}")

        # D-2: FinMind per-stock institutional (skip on daily — D-1 covers today)
        fm_inst_saved = 0
        if is_incremental:
            logger.info("D-2: Skipped (incremental mode, D-1 covers today)")
        elif not finmind_exhausted:
            inst_start = (target_date - timedelta(days=45)).strftime("%Y-%m-%d")
            fm_inst_saved, exhausted = _fetch_finmind_institutional_batch(
                finmind, db, all_target_ids, inst_start, date_str
            )
            if exhausted:
                finmind_exhausted = True
        else:
            logger.info("D-2: Skipped FinMind institutional (quota exhausted)")
        saved_inst += fm_inst_saved
        logger.info(f"Institutional total saved: {saved_inst} (FinMind: {fm_inst_saved})")

        # --- Step E: Fetch margin data ---
        # E-1: TWSE MI_MARGN bulk for latest day
        logger.info("Step E-1: TWSE bulk margin data")
        saved_margin = 0
        margin_data = twse.fetch_margin_all()
        # Batch: pre-fetch existing margin stock IDs for this date
        existing_margin_ids = set(
            r[0] for r in db.query(MarginTrading.stock_id)
            .filter(MarginTrading.trade_date == inst_date).all()
        )
        for item in margin_data:
            if item["stock_id"] in existing_margin_ids:
                continue
            db.add(MarginTrading(
                stock_id=item["stock_id"],
                trade_date=inst_date,
                margin_balance=item["margin_balance"],
                short_balance=item["short_balance"],
            ))
            saved_margin += 1
            if saved_margin % 500 == 0:
                db.commit()
        db.commit()
        logger.info(f"TWSE margin saved: {saved_margin}")

        # E-2: FinMind per-stock margin (skip on daily — E-1 covers today)
        fm_margin_saved = 0
        if is_incremental:
            logger.info("E-2: Skipped (incremental mode, E-1 covers today)")
        elif not finmind_exhausted:
            margin_start = (target_date - timedelta(days=25)).strftime("%Y-%m-%d")
            fm_margin_saved, exhausted = _fetch_finmind_margin_batch(
                finmind, db, all_target_ids, margin_start, date_str
            )
            if exhausted:
                finmind_exhausted = True
        else:
            logger.info("E-2: Skipped FinMind margin (quota exhausted)")
        saved_margin += fm_margin_saved
        logger.info(f"Margin total saved: {saved_margin} (FinMind: {fm_margin_saved})")

        # --- Step F: Fetch monthly revenue ---
        # TWSE bulk (already-filed companies) + FinMind (priority stocks)
        logger.info("Step F: Fetching monthly revenue...")
        saved_rev = 0

        # F-1: TWSE bulk revenue (companies that already filed)
        rev_data = twse.fetch_monthly_revenue()
        # Batch: pre-fetch existing revenue keys for this month
        if rev_data:
            rev_month = rev_data[0]["revenue_date"]
            existing_rev_ids = set(
                r[0] for r in db.query(Revenue.stock_id)
                .filter(Revenue.revenue_date == rev_month).all()
            )
        else:
            existing_rev_ids = set()
        for r in rev_data:
            if r["stock_id"] in existing_rev_ids:
                continue
            db.add(Revenue(
                stock_id=r["stock_id"],
                revenue_date=r["revenue_date"],
                revenue=r["revenue"],
                revenue_yoy=r["revenue_yoy"],
                revenue_mom=r["revenue_mom"],
            ))
            saved_rev += 1
        db.commit()
        logger.info(f"TWSE revenue saved: {saved_rev}")

        # F-2: FinMind revenue supplement (historical gap-filling only)
        # F-1 covers current month. F-2 only needed on initial run.
        fm_rev_saved = 0
        if is_incremental:
            logger.info("F-2: Skipped (incremental mode, F-1 covers current month)")
        elif not finmind_exhausted:
            from app.services.finmind_collector import FinMindQuotaExhausted
            rev_start = (target_date - timedelta(days=550)).strftime("%Y-%m-%d")
            rev_target_ids = [
                sid for sid in all_target_ids
                if sid.isdigit() and len(sid) == 4
            ]
            logger.info(f"F-2: FinMind revenue supplement for {len(rev_target_ids)} stocks")
            for sid in rev_target_ids:
                try:
                    df = finmind.fetch_revenue(sid, rev_start, date_str)
                except FinMindQuotaExhausted:
                    logger.warning("FinMind quota exhausted during F-2 revenue")
                    finmind_exhausted = True
                    break
                if df is None or df.empty:
                    continue
                df = df.sort_values('date')
                rev_map = {}
                for _, row in df.iterrows():
                    rev_date_str = str(row['date'])
                    rev_val = int(row.get('revenue', 0))
                    rev_map[rev_date_str] = rev_val

                for _, row in df.iterrows():
                    rev_date = row['date']
                    existing = db.query(Revenue).filter_by(
                        stock_id=sid, revenue_date=rev_date
                    ).first()
                    revenue_val = int(row.get('revenue', 0))

                    from dateutil.relativedelta import relativedelta
                    rev_dt = datetime.strptime(str(rev_date), "%Y-%m-%d")
                    yoy_dt = (rev_dt - relativedelta(years=1)).strftime("%Y-%m-%d")
                    mom_dt = (rev_dt - relativedelta(months=1)).strftime("%Y-%m-%d")
                    yoy_rev = rev_map.get(yoy_dt, 0)
                    mom_rev = rev_map.get(mom_dt, 0)
                    yoy = ((revenue_val - yoy_rev) / yoy_rev * 100) if yoy_rev > 0 else 0
                    mom = ((revenue_val - mom_rev) / mom_rev * 100) if mom_rev > 0 else 0

                    if existing:
                        if float(existing.revenue_yoy) == 0 and yoy != 0:
                            existing.revenue_yoy = round(yoy, 2)
                            existing.revenue_mom = round(mom, 2)
                    else:
                        db.add(Revenue(
                            stock_id=sid,
                            revenue_date=rev_date,
                            revenue=revenue_val,
                            revenue_yoy=round(yoy, 2),
                            revenue_mom=round(mom, 2),
                        ))
                        fm_rev_saved += 1
            db.commit()
        else:
            logger.info("F-2: Skipped FinMind revenue (quota exhausted, F-1 TWSE covers current month)")
        saved_rev += fm_rev_saved
        logger.info(f"FinMind revenue saved: {fm_rev_saved} (total: {saved_rev})")

        # --- Step F-3: Fetch PER/PBR from TWSE (bulk, all stocks) ---
        logger.info("Step F-3: TWSE bulk PER/PBR data")
        per_data = twse.fetch_per_ratio()
        updated_per = 0
        for item in per_data:
            stock = db.query(Stock).filter_by(stock_id=item["stock_id"]).first()
            if stock:
                stock.per = item["per"] if item["per"] > 0 else None
                stock.pbr = item["pbr"] if item["pbr"] > 0 else None
                stock.dividend_yield = item["dividend_yield"] if item["dividend_yield"] > 0 else None
                updated_per += 1
        db.commit()
        logger.info(f"PER/PBR updated: {updated_per}")

        # --- Step G: Fetch quarterly financials ---
        # Find stocks missing recent quarterly data (last 6 months)
        from sqlalchemy import func as sqlfunc_g
        recent_cutoff = (target_date - timedelta(days=180)).strftime("%Y-%m-%d")
        stocks_with_recent_fin = set(
            r[0] for r in db.query(Financial.stock_id)
            .filter(Financial.report_date >= recent_cutoff)
            .distinct().all()
        )
        fin_target_ids = [
            sid for sid in all_target_ids
            if sid not in stocks_with_recent_fin
            and sid.isdigit()
            and len(sid) == 4
        ]
        logger.info(
            f"Step G: {len(fin_target_ids)} stocks need financials update "
            f"({len(stocks_with_recent_fin)} already have recent data)"
        )

        saved_fin = 0
        if is_incremental:
            logger.info("Step G: Incremental mode, using TWSE daily filers only")
        elif not finmind_exhausted:
            saved_fin, exhausted = _fetch_financials(finmind, db, fin_target_ids, target_date)
            if exhausted:
                finmind_exhausted = True
        else:
            logger.info("Step G: FinMind quota exhausted, using TWSE fallback")

        # G supplement: TWSE quarterly financials (today's filers, always run)
        if is_incremental or finmind_exhausted:
            logger.info("Step G fallback: Fetching TWSE quarterly financials...")
            twse_fin_data = twse.fetch_quarterly_financials()
            twse_fin_saved = 0
            for item in twse_fin_data:
                existing = db.query(Financial).filter_by(
                    stock_id=item["stock_id"], report_date=item["report_date"]
                ).first()
                if not existing:
                    db.add(Financial(
                        stock_id=item["stock_id"],
                        report_date=item["report_date"],
                        eps=item["eps"],
                        gross_margin=item["gross_margin"],
                        operating_margin=item["operating_margin"],
                        roe=item["roe"],
                        debt_ratio=item["debt_ratio"],
                        operating_cash_flow=None,
                        free_cash_flow=None,
                    ))
                    twse_fin_saved += 1
            db.commit()
            saved_fin += twse_fin_saved
            logger.info(f"TWSE quarterly financials saved: {twse_fin_saved}")

        total_prices = saved_twse + saved_hist
        msg = (f"TWSE: {saved_twse}, Hist: {saved_hist} "
               f"(backfill: {len(need_backfill) if need_backfill else 0}), "
               f"Inst: {saved_inst}, Margin: {saved_margin}, "
               f"Rev: {saved_rev}, Fin: {saved_fin}")
        logger.info(f"Data fetch done: {msg}")
        return {"success": True, "message": msg}

    except Exception as e:
        logger.error(f"Stock data fetch failed: {e}", exc_info=True)
        db.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}


def step_fetch_news(db: Session) -> Dict[str, Any]:
    """Fetch latest news articles per stock from Google News RSS."""
    try:
        logger.info("Starting per-stock news fetch")
        collector = NewsCollector()

        # Get target stocks: priority + top volume
        top_ids = _get_top_stocks_by_volume(db, limit=50)
        target_ids = list(set(top_ids) | set(PRIORITY_STOCKS))
        target_ids = [sid for sid in target_ids if sid.isdigit()]

        # Build stock_id -> stock_name mapping
        stocks = (
            db.query(Stock.stock_id, Stock.stock_name)
            .filter(Stock.stock_id.in_(target_ids))
            .all()
        )
        stock_map = {s.stock_id: s.stock_name for s in stocks}

        saved_count = 0
        fetched_stocks = 0
        for sid in target_ids:
            name = stock_map.get(sid, sid)
            # Search by "stock_id stock_name" for precise results
            query = f"{sid} {name} 股票"
            articles = collector.fetch_news(query=query, max_results=3)

            for article in articles:
                try:
                    existing = db.query(News).filter_by(
                        url=article['url']
                    ).first()
                    if not existing:
                        db.add(News(
                            stock_id=sid,
                            title=article['title'],
                            source=article['source'],
                            url=article['url'],
                            published_at=datetime.fromisoformat(
                                article['published_at']
                            ),
                            content=article['content'],
                        ))
                        saved_count += 1
                except Exception as e:
                    logger.warning(f"Failed to save article for {sid}: {e}")

            fetched_stocks += 1
            # Commit periodically and brief pause to avoid rate limiting
            if fetched_stocks % 20 == 0:
                db.commit()
                time.sleep(1)
                logger.info(
                    f"News progress: {fetched_stocks}/{len(target_ids)}, "
                    f"saved {saved_count}"
                )

        db.commit()
        msg = f"Saved {saved_count} articles for {fetched_stocks} stocks"
        logger.info(f"News fetch done: {msg}")
        return {"success": True, "message": msg}

    except Exception as e:
        logger.error(f"News fetch failed: {e}", exc_info=True)
        return {"success": False, "message": f"Error: {str(e)}"}
