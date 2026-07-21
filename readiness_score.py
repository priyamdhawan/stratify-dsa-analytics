import pandas as pd


def calculate_readiness_score(df, leetcode_total_solved):

    confidence_values = pd.to_numeric(df.get("confidence", pd.Series(dtype=float)), errors="coerce")
    valid_confidence = confidence_values.dropna()

    if not valid_confidence.empty:
        avg_confidence = float(valid_confidence.mean())
    else:
        avg_confidence = 0.0

    pattern_score = (avg_confidence / 5) * 60

    try:
        volume_score = min(float(leetcode_total_solved) / 200, 1.0) * 40
    except (TypeError, ValueError):
        volume_score = 0.0

    total_score = round(pattern_score + volume_score, 1)
    return max(0.0, min(100.0, total_score))

if __name__ == "__main__":
    from build_features import build_dataframe
    df = build_dataframe()
    score = calculate_readiness_score(df, leetcode_total_solved=115)
    print(f"Readiness Score: {score}/100")
