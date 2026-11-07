import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from config.settings import settings
from src.feed.universe import universe_manager
from src.feed.data_provider import get_data_provider, BaseDataProvider
from src.analytics.rvol import classify_rvol_urgency
from src.analytics.gap import evaluate_gap_quality
from src.analytics.breakout import detect_breakout
from src.analytics.momentum import calculate_momentum_score
from src.alerts.dispatcher import alert_dispatcher

logger = logging.getLogger("OpenMarketScanner.Engine")


class ScanningEngine:
    """High-throughput multi-threaded screening engine for 5,000+ US stocks."""

    def __init__(self, cfg=settings, provider: Optional[BaseDataProvider] = None):
        self.cfg = cfg
        self.provider = provider or get_data_provider(cfg.default_provider, cfg.polygon_api_key)
        self.last_scan_results: List[Dict[str, Any]] = []
        self.last_scan_timestamp: float = 0.0

    async def scan_universe(
        self,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rvol: Optional[float] = None,
        min_gap_pct: Optional[float] = None,
        limit: int = 50,
        preset: str = "ALL"
    ) -> Dict[str, Any]:
        """
        Executes a high-performance screening pass across the full equities universe.
        """
        start_time = time.time()
        p_min = min_price if min_price is not None else self.cfg.min_price
        p_max = max_price if max_price is not None else self.cfg.max_price
        rvol_min = min_rvol if min_rvol is not None else self.cfg.min_rvol
        gap_min = min_gap_pct if min_gap_pct is not None else self.cfg.min_gap_pct

        symbols = universe_manager.get_symbols()
        total_symbols = len(symbols)

        # Batch processing in chunks
        chunk_size = 500
        chunks = [symbols[i:i + chunk_size] for i in range(0, total_symbols, chunk_size)]

        all_snapshots = []
        tasks = [self.provider.get_market_snapshot(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)
        for sublist in results:
            all_snapshots.extend(sublist)

        matched_stocks = []

        for item in all_snapshots:
            price = item["price"]
            rvol = item["rvol"]
            gap = item["gap_pct"]
            is_breakout = item["is_breaking_high"]

            # 1. Price boundaries
            if not (p_min <= price <= p_max):
                continue

            # 2. Minimum liquidity check
            if item["avg_volume_30d"] < self.cfg.min_avg_volume:
                continue

            # 3. Preset specific evaluation
            preset_upper = preset.upper()
            trigger_reason = "GENERAL_HIT"

            if preset_upper == "PREMARKET_GAPPERS":
                if abs(gap) < gap_min or rvol < rvol_min:
                    continue
                trigger_reason = f"GAP_{'UP' if gap > 0 else 'DOWN'}_{abs(gap):.1f}%"

            elif preset_upper == "UNUSUAL_RVOL":
                if rvol < max(3.0, rvol_min):
                    continue
                trigger_reason = f"RVOL_SURGE_{rvol:.1f}x"

            elif preset_upper == "MOMENTUM_BREAKOUT":
                breakout_data = detect_breakout(price, item["high_20d"], item["low_20d"], rvol)
                if not breakout_data["is_breakout"]:
                    continue
                trigger_reason = breakout_data["breakout_type"]

            else:
                # Default "ALL" criteria: either unusual RVOL, notable gap, or breakout
                if rvol < rvol_min and abs(gap) < gap_min and not is_breakout:
                    continue
                if is_breakout:
                    trigger_reason = "20D_BREAKOUT"
                elif abs(gap) >= gap_min:
                    trigger_reason = f"GAP_{abs(gap):.1f}%"
                else:
                    trigger_reason = f"RVOL_{rvol:.1f}x"

            # Compute quantitative momentum conviction score
            momentum_score = calculate_momentum_score(
                change_pct=item["change_pct"],
                rvol=rvol,
                is_breaking_high=is_breakout,
                float_shares=item["float_shares"]
            )

            urgency = classify_rvol_urgency(rvol)
            gap_quality = evaluate_gap_quality(gap, rvol, item["float_shares"])

            processed_entry = {
                "symbol": item["symbol"],
                "price": price,
                "change_pct": item["change_pct"],
                "gap_pct": gap,
                "rvol": rvol,
                "volume": item["volume"],
                "avg_volume": item["avg_volume_30d"],
                "momentum_score": momentum_score,
                "trigger": trigger_reason,
                "urgency": urgency,
                "gap_quality": gap_quality,
                "sector": item["sector"],
                "float_shares": item["float_shares"],
                "market_cap": item["market_cap"],
                "timestamp": item["timestamp"]
            }
            matched_stocks.append(processed_entry)

        # Sort by institutional momentum score descending
        matched_stocks.sort(key=lambda x: x["momentum_score"], reverse=True)
        top_candidates = matched_stocks[:limit]

        elapsed_sec = time.time() - start_time
        throughput = round(total_symbols / max(0.001, elapsed_sec), 0)

        self.last_scan_results = top_candidates
        self.last_scan_timestamp = time.time()

        # Trigger alerts for top 3 candidates if dispatcher is active
        for candidate in top_candidates[:3]:
            asyncio.create_task(alert_dispatcher.dispatch(candidate))

        return {
            "total_screened": total_symbols,
            "matched_count": len(matched_stocks),
            "returned_count": len(top_candidates),
            "preset": preset_upper,
            "execution_time_sec": round(elapsed_sec, 3),
            "throughput_tickers_per_sec": throughput,
            "results": top_candidates
        }


scanning_engine = ScanningEngine()
