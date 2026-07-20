# Stratify

**A DSA interview-readiness dashboard built on your real LeetCode data — no manual input, no fake AI.**

🔗 **Live app:** [stratify-dsa-analytics.streamlit.app](https://stratify-dsa-analytics.streamlit.app/)

---

## What it does

Most "DSA tracker" tools ask you to manually rate your own confidence per topic — which is just self-flattery with extra steps. Stratify pulls your **real, public LeetCode profile data** and builds everything from that:

- **Pattern confidence, derived, not guessed.** Per-tag confidence (1–5) is computed from your actual solved counts per topic — not a slider you fill in.
- **K-Means clustering** groups your patterns into Weak / Moderate / Strong tiers relative to *your own* profile, with a rule-based fallback for newer accounts that don't have enough tags yet for clustering to make sense.
- **A revision plan that isn't generic.** Weak/Moderate patterns are prioritized (high-yield topics first), each with a plain-English diagnosis of *why* it's weak (cold start vs. pattern-recognition gap vs. "you've done the reps but the template hasn't clicked"), plus real unsolved problems pulled live and filtered against your accepted-submission history.
- **Honest progress forecasting.** A local history log + linear regression on your *actual* logged solve counts over time — it refuses to show a forecast until there's enough real history to back it up, rather than faking a trend line from one data point.
- **Rule-based solving-behavior detection.** Reads your real submission timestamps to describe your practice cadence (consistent / bursty / light) — labeled honestly as date-math on real data, not dressed up as "AI."

## Why it's built this way

It would be easy to bolt on things like "AI-predicted interview readiness: 78%" or "predicted contest rating." I didn't, on purpose: with a single user's LeetCode snapshot as the only input, there's no real ground truth to train or validate a prediction like that against — it would just be a made-up number wearing a machine-learning costume. Everything in this app is either **real data** (your actual solve counts, timestamps, submissions) or **transparent rule-based logic** . That trade-off — informative over impressive — is the actual design decision behind this project.

## Tech stack

| Piece | Tool |
|---|---|
| UI / app framework | [Streamlit](https://streamlit.io/) |
| Data wrangling | pandas, numpy |
| Clustering | scikit-learn (K-Means + StandardScaler) |
| Charts | Plotly |
| LeetCode data | Live public API calls (`requests`) |
| Progress history | Local SQLite |

## Project structure

```
stratify/
├── app.py                 # Streamlit entry point — all 4 tabs (Overview, Pattern Analysis, Revision Plan, Progress & Behavior)
├── leetcode_api.py         # Fetches real stats/skills/submissions from a username, with retry + caching
├── build_features.py       # Turns raw skill data into a per-pattern DataFrame with derived confidence
├── cluster_patterns.py     # K-Means tiering (Weak/Moderate/Strong) with a rule-based fallback for sparse profiles
├── readiness_score.py      # Combines pattern confidence + real solve volume into one score
├── revision_plan.py        # Builds the prioritized, diagnosed revision plan with live unsolved problems
├── behavior.py              # Rule-based solving-cadence analysis from real submission timestamps
├── history_store.py         # Local SQLite persistence for daily snapshots
├── forecast.py              # Linear-regression forecasting on real logged history
├── colors.py                 # Centralized color palette (tiers, difficulty, theme surfaces)
├── theme.py                  # Custom CSS injection (fonts, spacing, card styling)
├── .streamlit/config.toml    # Streamlit's dark theme config — required for the charts to render correctly
└── requirements.txt
```

## Running it locally

```bash
git clone https://github.com/priyamdhawan/stratify-dsa-analytics.git
cd stratify-dsa-analytics
pip install -r requirements.txt
streamlit run app.py
```

Then enter any public LeetCode username in the sidebar.

> **Note:** the app expects a `.streamlit/config.toml` file (dark theme) in the project root for the charts and cards to display correctly — make sure it's present alongside `app.py` after cloning.

## Roadmap / honest limitations

- Progress history is local to whatever machine runs the app — not synced across devices.
- Submission-history lookups depend on a free third-party LeetCode API; if it's asleep, the first request can be slow.
- Forecasts need multiple days of logged history before they'll show anything — by design, not a bug.

---

Built by [@priyamdhawan](https://github.com/priyamdhawan)
