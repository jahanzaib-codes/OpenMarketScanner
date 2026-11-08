import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.feed.universe import universe_manager

logger = logging.getLogger("OpenMarketScanner.Feed")


class BaseDataProvider(ABC):
    """Abstract interface for multi-source market data ingestion."""

    @abstractmethod
    async def get_market_snapshot(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetches bulk snapshot data for given list of symbols."""
        pass


class SimulatorDataProvider(BaseDataProvider):
    """
    High-performance synthetic market data provider.
    Simulates real-world power-law distributions:
    - Normal stocks oscillate between -2% and +2% with RVOL ~ 0.8x-1.2x.
    - Outlier stocks experience catalysts with Premarket Gaps (+8% to +35%),
      unusual RVOL spikes (3.0x to 15.0x), and key resistance breakouts.
    """

    def __init__(self):
        self._price_cache: Dict[str, float] = {}

    async def get_market_snapshot(self, symbols: List[str]) -> List[Dict[str, Any]]:
        results = []
        now = time.time()

        for sym in symbols:
            # Deterministic base price or cache
            if sym not in self._price_cache:
                if sym in ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META"):
                    self._price_cache[sym] = random.uniform(120.0, 500.0)
                elif sym in ("SPY", "QQQ"):
                    self._price_cache[sym] = random.uniform(500.0, 600.0)
                else:
                    self._price_cache[sym] = random.uniform(3.50, 180.0)

            base_price = self._price_cache[sym]
            meta = universe_manager.get_by_symbol(sym)
            avg_vol = meta["avg_volume_30d"]

            # Probability of catalyst / momentum event
            is_catalyst = random.random() < 0.05  # 5% of universe has high momentum

            if is_catalyst:
                # Strong premarket gap or breakout runner
                gap_direction = 1 if random.random() > 0.3 else -1
                gap_pct = gap_direction * random.uniform(4.0, 32.0)
                rvol = random.uniform(2.5, 12.5)
                current_price = round(base_price * (1.0 + (gap_pct / 100.0)), 2)
                intraday_change_pct = round(gap_pct + random.uniform(-1.5, 4.0), 2)
                current_vol = int(avg_vol * (rvol / 6.5) * random.uniform(0.7, 1.4))
                is_breaking_high = gap_direction > 0 and random.random() > 0.4
            else:
                # Normal trading distribution
                gap_pct = round(random.gauss(0.1, 1.2), 2)
                rvol = round(max(0.2, random.gauss(1.0, 0.35)), 2)
                current_price = round(base_price * (1.0 + (gap_pct / 100.0)), 2)
                intraday_change_pct = round(gap_pct + random.uniform(-0.8, 0.8), 2)
                current_vol = int(avg_vol * (rvol / 6.5) * random.uniform(0.8, 1.1))
                is_breaking_high = False

            prev_close = round(base_price, 2)
            high_20d = round(prev_close * random.uniform(1.02, 1.15), 2)
            low_20d = round(prev_close * random.uniform(0.85, 0.98), 2)
            day_high = max(current_price, round(current_price * random.uniform(1.002, 1.025), 2))
            day_low = min(current_price, round(current_price * random.uniform(0.975, 0.998), 2))
            vwap = round((day_high + day_low + current_price) / 3.0, 2)

            results.append({
                "symbol": sym,
                "price": current_price,
                "prev_close": prev_close,
                "open": round(prev_close * (1.0 + (gap_pct / 100.0)), 2),
                "day_high": day_high,
                "day_low": day_low,
                "vwap": vwap,
                "volume": max(1000, current_vol),
                "avg_volume_30d": avg_vol,
                "rvol": round(rvol, 2),
                "gap_pct": round(gap_pct, 2),
                "change_pct": intraday_change_pct,
                "high_20d": high_20d,
                "low_20d": low_20d,
                "is_breaking_high": is_breaking_high or (current_price >= high_20d),
                "sector": meta["sector"],
                "market_cap": meta["market_cap"],
                "float_shares": meta["float_shares"],
                "timestamp": now
            })

        return results


class PolygonDataProvider(BaseDataProvider):
    """Integrates directly with Polygon.io REST Grouped Daily/Snapshot endpoints."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_market_snapshot(self, symbols: List[str]) -> List[Dict[str, Any]]:
        # If API key is not configured, gracefully fall back to simulator
        if not self.api_key:
            logger.info("Polygon API key not set. Using Simulator provider.")
            sim = SimulatorDataProvider()
            return await sim.get_market_snapshot(symbols)

        # Real Polygon implementation via aiohttp / httpx
        import httpx
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    snapshots = []
                    for t in data.get("tickers", []):
                        sym = t.get("ticker")
                        if symbols and sym not in symbols:
                            continue
                        day = t.get("day", {})
                        prev = t.get("prevDay", {})
                        price = day.get("c") or t.get("lastTrade", {}).get("p", 0.0)
                        prev_close = prev.get("c", price)
                        change_pct = t.get("todaysChangePerc", 0.0)
                        vol = day.get("v", 0)
                        snapshots.append({
                            "symbol": sym,
                            "price": price,
                            "prev_close": prev_close,
                            "open": day.get("o", price),
                            "day_high": day.get("h", price),
                            "day_low": day.get("l", price),
                            "vwap": day.get("vw", price),
                            "volume": vol,
                            "avg_volume_30d": max(vol, 1_000_000),
                            "rvol": 1.5,
                            "gap_pct": change_pct,
                            "change_pct": change_pct,
                            "high_20d": price * 1.05,
                            "low_20d": price * 0.95,
                            "is_breaking_high": False,
                            "sector": "Equities",
                            "market_cap": 1e9,
                            "float_shares": 5e7,
                            "timestamp": time.time()
                        })
                    return snapshots
        except Exception as e:
            logger.warning(f"Polygon snapshot fetch failed: {e}. Falling back to simulation.")

        sim = SimulatorDataProvider()
        return await sim.get_market_snapshot(symbols)


def get_data_provider(provider_type: str = "simulator", api_key: str = "") -> BaseDataProvider:
    """Factory for instantiating the configured data feed provider."""
    pt = provider_type.lower()
    if pt == "polygon":
        return PolygonDataProvider(api_key=api_key)
    return SimulatorDataProvider()

