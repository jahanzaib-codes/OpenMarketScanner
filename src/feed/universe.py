from typing import List, Dict, Any
import random

# Major benchmark tickers for baseline universe representation
CORE_BENCHMARKS = [
    # Mega-Cap Tech & Leaders
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK.B", "LLY", "AVGO",
    "JPM", "V", "UNH", "XOM", "MA", "JNJ", "PG", "HD", "COST", "MRK", "ABBV", "CVX",
    "NFLX", "AMD", "ADBE", "CRM", "PEP", "KO", "BAC", "WMT", "TMO", "ACN", "MCD",
    "CSCO", "ABT", "LIN", "ORCL", "INTC", "TXN", "QCOM", "AMGN", "IBM", "HON", "GE",
    "SPGI", "CAT", "PFE", "NOW", "AMAT", "DIS", "GS", "MS", "RTX", "UBER", "ISRG",
    # Active Small/Mid-Caps & Volatile Retail Favorites
    "PLTR", "SOFI", "SMCI", "COIN", "MARA", "RIOT", "CLSK", "MSTR", "HOOD", "RIVN",
    "LCID", "NIO", "DKNG", "SNAP", "PINS", "ROKU", "AFRM", "UPST", "CVNA", "AI",
    "BBAI", "SOUN", "ARM", "RDDT", "CELH", "SYM", "IONQ", "RGTI", "QUBT", "ASTS",
    "LUNR", "RKLB", "JOBY", "ACHR", "OPEN", "WISH", "FUBO", "HIMS", "DNA", "TEM",
    # Benchmarks & Sector ETFs
    "SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XBI", "SMH", "IBB"
]

SECTORS = [
    "Technology", "Healthcare", "Financial Services", "Consumer Cyclical",
    "Communication Services", "Industrials", "Consumer Defensive", "Energy",
    "Basic Materials", "Real Estate", "Utilities"
]


class UniverseManager:
    """Manages the 5,000+ US stock ticker universe and metadata."""

    def __init__(self, target_size: int = 5000):
        self.target_size = target_size
        self._universe: List[Dict[str, Any]] = []
        self._lookup: Dict[str, Dict[str, Any]] = {}
        self._build_universe()

    def _build_universe(self):
        # 1. Add known core equities with representative attributes
        known_stocks = []
        for sym in CORE_BENCHMARKS:
            known_stocks.append({
                "symbol": sym,
                "name": f"{sym} Corporation",
                "sector": random.choice(SECTORS),
                "market_cap": random.uniform(2e9, 3e12),
                "float_shares": random.uniform(5e7, 5e9),
                "avg_volume_30d": random.randint(1_000_000, 80_000_000),
                "is_core": True
            })

        self._universe.extend(known_stocks)

        # 2. Procedurally generate realistic universe to scale to 5,000+ tickers
        current_count = len(self._universe)
        needed = max(0, self.target_size - current_count)

        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        generated_symbols = set(CORE_BENCHMARKS)

        for i in range(needed):
            # Synthesize valid 3-4 letter ticker symbols
            while True:
                length = random.choice([3, 4])
                cand = "".join(random.choices(letters, k=length))
                if cand not in generated_symbols:
                    generated_symbols.add(cand)
                    break

            is_micro = random.random() < 0.4
            market_cap = random.uniform(5e7, 2e9) if is_micro else random.uniform(2e9, 5e10)
            avg_vol = random.randint(200_000, 3_000_000) if is_micro else random.randint(1_000_000, 15_000_000)

            self._universe.append({
                "symbol": cand,
                "name": f"{cand} Holdings Inc.",
                "sector": random.choice(SECTORS),
                "market_cap": market_cap,
                "float_shares": random.uniform(1e7, 2e8),
                "avg_volume_30d": avg_vol,
                "is_core": False
            })

        # Build O(1) instant lookup dictionary
        self._lookup = {item["symbol"]: item for item in self._universe}

    def get_symbols(self) -> List[str]:
        """Returns list of ticker symbols."""
        return [item["symbol"] for item in self._universe]

    def get_all(self) -> List[Dict[str, Any]]:
        """Returns full metadata universe list."""
        return self._universe

    def get_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """Instant O(1) lookup of metadata for a single symbol."""
        sym_clean = symbol.strip().upper()
        if sym_clean in self._lookup:
            return self._lookup[sym_clean]
        return {
            "symbol": sym_clean,
            "name": f"{sym_clean} Inc.",
            "sector": "Technology",
            "market_cap": 1e9,
            "float_shares": 5e7,
            "avg_volume_30d": 1_000_000,
            "is_core": False
        }


universe_manager = UniverseManager()
