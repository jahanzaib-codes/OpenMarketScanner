from typing import Dict, Any


def calculate_momentum_score(
    change_pct: float,
    rvol: float,
    is_breaking_high: bool,
    float_shares: float
) -> float:
    """
    Computes a composite multi-factor quantitative momentum score (0 to 100).

    Factor Weightings:
    - Intraday / Gap Change % (35%)
    - Relative Volume RVOL (35%)
    - Resistance Breakout Multiplier (20%)
    - Float Dynamics (Low float acceleration bonus) (10%)
    """
    # 1. Price velocity component (clamped to 35 points max)
    price_score = min(35.0, max(0.0, abs(change_pct) * 1.5))

    # 2. Volume conviction component (clamped to 35 points max)
    vol_score = min(35.0, max(0.0, (rvol / 5.0) * 35.0))

    # 3. Structural breakout bonus (20 points)
    breakout_bonus = 20.0 if is_breaking_high else 5.0

    # 4. Low-float velocity factor (10 points)
    float_bonus = 10.0 if float_shares < 30_000_000 else (6.0 if float_shares < 100_000_000 else 2.0)

    raw_score = price_score + vol_score + breakout_bonus + float_bonus
    return round(min(100.0, raw_score), 1)

