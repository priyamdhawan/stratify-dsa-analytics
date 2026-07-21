import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from build_features import build_dataframe

MIN_ROWS_FOR_KMEANS = 3


def _fallback_tier(confidence):
    
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
        
        df["cluster"] = -1
        df["tier"] = df["confidence"].apply(_fallback_tier)
        return df

    X = df[["problems_solved", "confidence"]]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)

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
