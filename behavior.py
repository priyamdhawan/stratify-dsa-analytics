"""
behavior.py

Reads your real accepted-submission timestamps (from
leetcode_api.get_recent_ac_submissions) and describes your solving
cadence over the last window_days. This is explicitly RULE-BASED date
math on real data - not a trained classifier - and it's labeled that
way in the UI on purpose rather than dressed up as "AI".
"""

from datetime import datetime, timedelta, timezone

WINDOW_DAYS = 30
CONSISTENT_ACTIVE_DAY_RATIO = 0.35  # active on >=35% of days in the window
BUSTY_GAP_DAYS = 10                 # a gap this long inside the window signals "bursty"


def _extract_timestamps(ac_submissions_json):
    """
    Pulls submission timestamps (as UTC datetimes) out of the
    acSubmission response. Defensive about field names/shape - same
    caveat as elsewhere in this codebase: confirm against the live
    response with leetcode_api.debug_print_ac_submission_shape() and
    adjust the key lookups below if your account's shape differs.
    """
    timestamps = []
    if not ac_submissions_json:
        return timestamps

    submissions = ac_submissions_json
    if isinstance(ac_submissions_json, dict):
        submissions = (
            ac_submissions_json.get("solved")
            or ac_submissions_json.get("submission")
            or ac_submissions_json.get("submissions")
            or ac_submissions_json.get("data")
            or []
        )

    if isinstance(submissions, list):
        for sub in submissions:
            raw_ts = sub.get("timestamp") or sub.get("time") or sub.get("date")
            if raw_ts is None:
                continue
            try:
                # LeetCode timestamps are typically Unix seconds, sometimes as strings
                ts = datetime.fromtimestamp(int(raw_ts), tz=timezone.utc)
                timestamps.append(ts)
            except (ValueError, TypeError, OSError):
                continue
    return timestamps


def analyze_learning_behavior(ac_submissions_json, window_days=WINDOW_DAYS):
    """
    Returns a dict describing your real solving cadence, honestly:
      {"label": str, "detail": str, "active_days": int, "longest_gap_days": int|None}
    """
    timestamps = _extract_timestamps(ac_submissions_json)
    if len(timestamps) < 3:
        return {
            "label": "Not enough data yet",
            "detail": "Need a handful of recent accepted submissions with timestamps to read a pattern.",
            "active_days": 0,
            "longest_gap_days": None,
        }

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    recent_days = sorted({ts.date() for ts in timestamps if ts >= cutoff})

    if len(recent_days) < 2:
        return {
            "label": "Not enough recent activity",
            "detail": f"Only one active day found in the last {window_days} days - not enough to read cadence yet.",
            "active_days": len(recent_days),
            "longest_gap_days": None,
        }

    gaps = [(recent_days[i + 1] - recent_days[i]).days for i in range(len(recent_days) - 1)]
    longest_gap = max(gaps)
    active_ratio = len(recent_days) / window_days

    if active_ratio >= CONSISTENT_ACTIVE_DAY_RATIO and longest_gap <= BUSTY_GAP_DAYS:
        label = "Consistent"
        detail = (
            f"Active on {len(recent_days)} of the last {window_days} days, no gap longer than "
            f"{longest_gap} days. Steady practice — the single best predictor of retention."
        )
    elif longest_gap > BUSTY_GAP_DAYS:
        label = "Bursty"
        detail = (
            f"Active on {len(recent_days)} of the last {window_days} days, but with a "
            f"{longest_gap}-day gap in there. You solve in clusters then go quiet — "
            f"smaller, more frequent sessions usually beat marathon-then-break."
        )
    else:
        label = "Light & steady"
        detail = (
            f"Active on {len(recent_days)} of the last {window_days} days — low volume but "
            f"no long gaps. Consider raising frequency, not just total solved."
        )

    return {
        "label": label,
        "detail": detail,
        "active_days": len(recent_days),
        "longest_gap_days": longest_gap,
    }


if __name__ == "__main__":
    import time
    now = int(time.time())
    day = 86400
    fake = {"submission": [
        {"timestamp": now - 1 * day},
        {"timestamp": now - 2 * day},
        {"timestamp": now - 3 * day},
        {"timestamp": now - 15 * day},
        {"timestamp": now - 16 * day},
    ]}
    print(analyze_learning_behavior(fake))