"""
cluster_patterns.py (UPDATED)

Fix: this used to assume the input always has exactly 14 rows (the old
fixed pattern list), so hardcoding n_clusters=3 for K-Means was always
safe. Now that rows = however many real tags your LeetCode profile has
skill data for, a newer account with data on only 1-2 tags would crash
here with a "n_samples < n_clusters" error. Added a rule-based fallback
for that case instead of hard-failing.
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from build_features import build_dataframe

MIN_ROWS_FOR_KMEANS = 3


def _fallback_tier(confidence):
    """
    Rule-based tier assignment used only when there aren't enough real
    tags yet (fewer than MIN_ROWS_FOR_KMEANS) to form meaningful
    clusters. Same 1-5 confidence scale build_features.py already uses.
    """
    if confidence <= 2:
        return "Weak"
    elif confidence == 3:
        return "Moderate"
    else:
        return "Strong"


def cluster_patterns(df):
    df = df.copy()

    if df.empty:
        df["cluster"] = pd.Series(dtype="int64")
        df["tier"] = pd.Series(dtype="object")
        return df

    if len(df) < MIN_ROWS_FOR_KMEANS:
        # Not enough real tags to form 3 meaningful clusters yet -
        # K-Means needs at least as many samples as clusters. Fall back
        # to a simple, explainable rule instead of crashing.
        df["cluster"] = -1
        df["tier"] = df["confidence"].apply(_fallback_tier)
        return df

    X = df[["problems_solved", "confidence"]]

    # Scale first - problems_solved and confidence are on different ranges
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)

    # Cluster numbers (0,1,2) are meaningless on their own - K-Means doesn't know
    # which cluster is "strong" vs "weak". We sort clusters by their average
    # strength and assign human-readable labels ourselves.
    #
    # BUG FIX: this used to average the RAW problems_solved/confidence
    # columns to rank clusters. Those two columns live on wildly
    # different scales (problems_solved can run into the hundreds,
    # confidence only ever 1-5), so problems_solved silently dominated
    # the ranking. A high-volume "grind" tag (e.g. 180 Array solves at
    # only 3/5 confidence) would out-rank a genuinely mastered
    # low-volume tag (e.g. 8 DP solves at 5/5 confidence) and get
    # mislabeled "Strong" while the real strength got called
    # "Moderate" - which then flows straight into the revision plan
    # excluding/including the wrong tags. Ranking on the SAME scaled
    # values K-Means actually clustered on fixes this.
    X_scaled_df = pd.DataFrame(X_scaled, columns=["problems_solved", "confidence"], index=df.index)
    cluster_strength = X_scaled_df.groupby(df["cluster"]).mean().mean(axis=1).sort_values()
    label_map = {cluster_id: label for cluster_id, label in zip(cluster_strength.index, ["Weak", "Moderate", "Strong"])}
    df["tier"] = df["cluster"].map(label_map)

    return df


if __name__ == "__main__":
    df = build_dataframe()
    result = cluster_patterns(df)
    print(result.sort_values("tier"))

    print("\n--- sparse profile test (1 real tag) ---")
    sparse_df = pd.DataFrame([
        {"pattern": "Array", "group": "fundamental", "problems_solved": 3, "confidence": 3},
    ])
    print(cluster_patterns(sparse_df))