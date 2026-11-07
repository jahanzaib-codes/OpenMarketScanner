from typing import Dict, Any


def calculate_rvol(current_volume: int, avg_volume_30d: int, time_of_day_fraction: float = 0.5) -> float:
    """
    Calculates institutional Relative Volume (RVOL).
    
    Formula:
        Expected Cumulative Volume = 30d Avg Volume * time_of_day_fraction
        RVOL = Current Volume / Expected Cumulative Volume

    Parameters:
        current_volume: Cumulative volume traded today
        avg_volume_30d: 30-day baseline average daily volume
        time_of_day_fraction: Elapsed fraction of the standard trading session (0.0 to 1.0)
    """
    if avg_volume_30d <= 0:
        return 1.0

    # Avoid divide-by-zero during market open
    effective_fraction = max(0.05, min(1.0, time_of_day_fraction))
    expected_vol = avg_volume_30d * effective_fraction

    rvol = current_volume / expected_vol
    return round(rvol, 2)


def classify_rvol_urgency(rvol: float) -> str:
    """Classifies RVOL into quantitative conviction buckets."""
    if rvol >= 5.0:
        return "EXTREME_INSTITUTIONAL"
    elif rvol >= 3.0:
        return "HIGH_SURGE"
    elif rvol >= 1.8:
        return "ABOVE_AVERAGE"
    elif rvol >= 0.8:
        return "NORMAL"
    else:
        return "ANEMIC"
