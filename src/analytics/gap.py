from typing import Dict, Any, Tuple


def calculate_gap(premarket_price: float, previous_close: float) -> Tuple[float, str]:
    """
    Calculates percentage gap from previous session close to premarket price.

    Returns:
        (gap_pct: float, gap_type: str) -> ("GAP_UP", "GAP_DOWN", "FLAT")
    """
    if previous_close <= 0:
        return 0.0, "FLAT"

    gap_pct = ((premarket_price - previous_close) / previous_close) * 100.0
    gap_pct_rounded = round(gap_pct, 2)

    if gap_pct_rounded >= 3.0:
        gap_type = "GAP_UP"
    elif gap_pct_rounded <= -3.0:
        gap_type = "GAP_DOWN"
    else:
        gap_type = "FLAT"

    return gap_pct_rounded, gap_type


def evaluate_gap_quality(gap_pct: float, rvol: float, float_shares: float) -> str:
    """
    Evaluates gap continuation vs exhaustion probability based on RVOL and float rotation.
    - Low float + high gap + high RVOL = High momentum continuation runner.
    - Massive float + modest gap = Mean reversion fade candidate.
    """
    abs_gap = abs(gap_pct)
    if abs_gap >= 8.0 and rvol >= 3.0:
        if float_shares < 50_000_000:
            return "A_PLUS_RUNNER"
        return "HIGH_MOMENTUM"
    elif abs_gap >= 3.0 and rvol >= 1.8:
        return "TRADABLE_GAP"
    else:
        return "CHOP_OR_FADE"
