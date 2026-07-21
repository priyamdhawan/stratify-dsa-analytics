import time

import requests
import streamlit as st

BASE_URL = "https://leetcode-api-pied.vercel.app"


def _get_with_retry(url, params=None, timeout=20, retries=2, backoff_seconds=2):
    
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
            time.sleep(backoff_seconds * (attempt + 1)) 

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_solved_stats(username):

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

    response = _get_with_retry(f"{BASE_URL}/user/{username}/skills")
    if response is None:
        return None
    try:
        return response.json()
    except ValueError:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_recent_ac_submissions(username, limit=1000):
  
    response = _get_with_retry(f"{BASE_URL}/user/{username}/solved")
    if response is None:
        return None
    try:
        return response.json()
    except ValueError:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_problems_by_tag(tag_slug, limit=40, skip=0):
   
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
    import json
    data = get_skill_stats(username)
    print(json.dumps(data, indent=2))
    return data


def debug_print_ac_submission_shape(username):
    import json
    data = get_recent_ac_submissions(username)
    print(json.dumps(data, indent=2))
    return data


def debug_print_problems_by_tag_shape(tag_slug):
    import json
    data = get_problems_by_tag(tag_slug)
    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    test_username = "lee215" 
    print("=== SOLVED STATS ===")
    print(get_solved_stats(test_username))
    print("\n=== SKILL STATS ===")
    debug_print_skill_shape(test_username)
    print("\n=== SOLVED PROBLEMS + TIMESTAMPS ===")
    debug_print_ac_submission_shape(test_username)
    print("\n=== PROBLEMS BY TAG ===")
    debug_print_problems_by_tag_shape("two-pointers")
