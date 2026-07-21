import numpy as np
import pandas as pd

MIN_POINTS_FOR_FORECAST = 3


def forecast_metric(history_df, value_column="readiness_score", days_ahead=30, clip_range=None):

    if history_df is None or len(history_df) < MIN_POINTS_FOR_FORECAST:
        return None

    dates = pd.to_datetime(history_df["snapshot_date"])
    day_numbers = (dates - dates.min()).dt.days.to_numpy()
    values = history_df[value_column].to_numpy(dtype=float)

    if len(set(day_numbers)) < 2:
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
