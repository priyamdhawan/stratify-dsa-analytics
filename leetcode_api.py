"""
leetcode_api.py (REWRITTEN v2 - switched provider)

Why: alfa-leetcode-api is hosted on Render's free tier, which sleeps
after ~15 minutes of no traffic and can take 30-60+ seconds (sometimes
longer/fails outright) to wake back up - that's the "API is at rest"
error.

Switched to noworneverev/leetcode-api (FastAPI, hosted on Vercel
serverless - https://github.com/noworneverev/leetcode-api). Vercel
functions don't sleep the same way; there's no persistent container to
wake up, so cold start is a couple seconds at most instead of a minute.

All four response shapes below were fetched and verified live against
the real API on 2026-07-15 (using a known public profile) - not
guessed this time. If the API ever changes shape, the debug_print_*
helpers at the bottom still work the same way as before to re-verify.

Also added: a generic retry-with-backoff wrapper. This isn't
provider-specific insurance - any free hosted API can have an
occasional transient timeout, so it's worth having regardless of who's
serving the data.
"""

import time

import requests
import streamlit as st

BASE_URL = "https://leetcode-api-pied.vercel.app"


def _get_with_retry(url, params=None, timeout=20, retries=2, backoff_seconds=2):
    """
    Retries on timeout or server error before giving up, instead of
    failing on the first hiccup. Returns None (not an exception) if all
    attempts fail - callers already treat None as "couldn't fetch".
    """
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code == 200:
                return response
            last_error = f"HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            last_error = str(e)

        if attempt < retries:
            time.sleep(backoff_seconds * (attempt + 1))  # 2s, then 4s

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_solved_stats(username):
    """
    Total solved + Easy/Medium/Hard breakdown, normalized to the shape
    the rest of the app already expects:
      {"solvedProblem": int, "easySolved": int, "mediumSolved": int, "hardSolved": int}

    Real source shape (verified live against /user/{username}):
      {"submitStats": {"acSubmissionNum": [
          {"difficulty": "All", "count": N}, {"difficulty": "Easy", "count": N}, ...
      ]}}
    """
    response = _get_with_retry(f"{BASE_URL}/user/{username}")
    if response is None:
        return None
    try:
        data = response.json()
    except ValueError:
        return None

    counts = {"All": 0, "Easy": 0, "Medium": 0, "Hard": 0}
    for entry in data.get("submitStats", {}).get("acSubmissionNum", []):
        difficulty = entry.get("difficulty")
        if difficulty in counts:
            counts[difficulty] = entry.get("count", 0)

    return {
        "solvedProblem": counts["All"],
        "easySolved": counts["Easy"],
        "mediumSolved": counts["Medium"],
        "hardSolved": counts["Hard"],
    }


@st.cache_data(ttl=3600, show_spinner=False)
def get_skill_stats(username):
    """
    Real per-topic solved counts. Shape verified live against
    /user/{username}/skills - matches build_features.py's parsing
    directly, and includes a real tagSlug per tag (no more guessing
    slugs for the /problems/tag/ lookups):
      {"fundamental": [{"tagName", "tagSlug", "problemsSolved"}, ...],
       "intermediate": [...], "advanced": [...]}
    """
    response = _get_with_retry(f"{BASE_URL}/user/{username}/skills")
    if response is None:
        return None
    try:
        return response.json()
    except ValueError:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_recent_ac_submissions(username, limit=1000):
    """
    Real solved-problem history with real timestamps. Name kept for
    compatibility with revision_plan.py/behavior.py, but the underlying
    endpoint actually returns your FULL solved list (not just recent
    ones like the old provider did) - `limit` is accepted but unused,
    kept as a no-op so callers don't need to change.

    Real source shape (verified live against /user/{username}/solved):
      {"total_solved": int, "solved_slugs": [str, ...],
       "solved": [{"title_slug", "title", "timestamp"}, ...]}
    """
    response = _get_with_retry(f"{BASE_URL}/user/{username}/solved")
    if response is None:
        return None
    try:
        return response.json()
    except ValueError:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_problems_by_tag(tag_slug, limit=40, skip=0):
    """
    Real problems for a single LeetCode topic tag. Shape verified live
    against /problems/tag/{slug}:
      {"tag", "total", "limit", "skip",
       "problems": [{"id","frontend_id","title","title_slug","url",
                      "difficulty","paid_only","has_solution"}]}
    """
    response = _get_with_retry(
        f"{BASE_URL}/problems/tag/{tag_slug}",
        params={"limit": limit, "skip": skip},
    )
    if response is None:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def debug_print_skill_shape(username):
    """Run once, standalone, to see the RAW skill-stats response."""
    import json
    data = get_skill_stats(username)
    print(json.dumps(data, indent=2))
    return data


def debug_print_ac_submission_shape(username):
    """Run once, standalone, to see the RAW solved-history response."""
    import json
    data = get_recent_ac_submissions(username)
    print(json.dumps(data, indent=2))
    return data


def debug_print_problems_by_tag_shape(tag_slug):
    """Run once, standalone, to see the RAW /problems/tag/ response."""
    import json
    data = get_problems_by_tag(tag_slug)
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    test_username = "lee215"  # known-public profile, good for a quick smoke test
    print("=== SOLVED STATS ===")
    print(get_solved_stats(test_username))
    print("\n=== SKILL STATS ===")
    debug_print_skill_shape(test_username)
    print("\n=== SOLVED PROBLEMS + TIMESTAMPS ===")
    debug_print_ac_submission_shape(test_username)
    print("\n=== PROBLEMS BY TAG ===")
    debug_print_problems_by_tag_shape("two-pointers")