from typing import Dict, Any


def detect_breakout(
    current_price: float,
    high_20d: float,
    low_20d: float,
    rvol: float,
    tolerance_pct: float = 0.5
) -> Dict[str, Any]:
    """
    Identifies 20-day resistance / consolidation breakouts confirmed by RVOL.
    """
    if high_20d <= 0 or low_20d <= 0:
        return {"is_breakout": False, "breakout_type": "NONE", "distance_to_high_pct": 0.0}

    distance_to_high_pct = ((high_20d - current_price) / high_20d) * 100.0

    # Breakout above 20-day high with volume confirmation
    if current_price >= (high_20d * (1.0 - (tolerance_pct / 100.0))):
        if rvol >= 1.8:
            return {
                "is_breakout": True,
                "breakout_type": "BULLISH_20D_BREAKOUT",
                "distance_to_high_pct": round(distance_to_high_pct, 2),
                "rvol_confirmed": True
            }

    # Breakdown below 20-day low with volume confirmation
    distance_to_low_pct = ((current_price - low_20d) / low_20d) * 100.0
    if current_price <= (low_20d * (1.0 + (tolerance_pct / 100.0))):
        if rvol >= 1.8:
            return {
                "is_breakout": True,
                "breakout_type": "BEARISH_20D_BREAKDOWN",
                "distance_to_low_pct": round(distance_to_low_pct, 2),
                "rvol_confirmed": True
            }

    return {
        "is_breakout": False,
        "breakout_type": "CONSOLIDATING",
        "distance_to_high_pct": round(distance_to_high_pct, 2),
        "rvol_confirmed": False
    }
