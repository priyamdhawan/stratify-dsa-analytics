"""
forecast.py

A genuinely earned use of regression: fits a straight line through your
REAL logged history (from history_store.py) and projects it forward. No
invented labels, no "AI predicted" framing - just np.polyfit on points
you actually logged over real sessions.

Refuses to forecast (returns None) until there's enough real history to
fit a line honestly - a confident-looking number from 2 noisy points is
worse than no number at all.

v2: generalized to forecast any logged numeric column, not just
readiness_score. readiness_score is a capped composite averaged across
every one of your tags - solving 2-3 problems a day barely moves it, so
it's a poor "did today count" metric on its own. total_solved moves by
exactly however many problems you actually solved, so forecasting THAT
gives a visibly honest trend instead of a flat line.
"""

import numpy as np
import pandas as pd

MIN_POINTS_FOR_FORECAST = 3


def forecast_metric(history_df, value_column="readiness_score", days_ahead=30, clip_range=None):
    """
    history_df: DataFrame with 'snapshot_date' (ISO string) and
    `value_column`, from history_store.get_history().

    clip_range: optional (min, max) tuple to clip the projection to a
    sane range (e.g. (0, 100) for a score). Left uncapped by default,
    since something like total_solved has no natural ceiling.

    Returns None if there isn't enough real history yet. Otherwise:
      {
        "projected_value": float,
        "days_ahead": int,
        "num_points": int,
        "slope_per_day": float,
      }
    """
    if history_df is None or len(history_df) < MIN_POINTS_FOR_FORECAST:
        return None

    dates = pd.to_datetime(history_df["snapshot_date"])
    day_numbers = (dates - dates.min()).dt.days.to_numpy()
    values = history_df[value_column].to_numpy(dtype=float)

    if len(set(day_numbers)) < 2:
        # everything logged on the same calendar day somehow - no real
        # time axis to fit a trend against
        return None

    slope, intercept = np.polyfit(day_numbers, values, 1)

    last_day = day_numbers.max()
    projected_day = last_day + days_ahead
    projected_value = slope * projected_day + intercept

    if clip_range:
        projected_value = max(clip_range[0], min(clip_range[1], projected_value))

    return {
        "projected_value": round(float(projected_value), 1),
        "days_ahead": days_ahead,
        "num_points": len(history_df),
        "slope_per_day": round(float(slope), 3),
    }


def forecast_readiness(history_df, days_ahead=30):
    """Backward-compatible wrapper - forecasts readiness_score specifically."""
    result = forecast_metric(history_df, "readiness_score", days_ahead, clip_range=(0.0, 100.0))
    if result:
        result["projected_score"] = result.pop("projected_value")
    return result


if __name__ == "__main__":
    import history_store
    df = history_store.get_history("testuser")
    print("readiness forecast:", forecast_readiness(df))
    print("total_solved forecast:", forecast_metric(df, "total_solved"))