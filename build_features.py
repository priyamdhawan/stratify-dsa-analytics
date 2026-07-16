"""
build_features.py (REWRITTEN v3 - Stricter Confidence Thresholds)

Fix applied: The previous version gave a 5/5 confidence rating for solving 
just 10 problems in a tag. This heavily inflated the Readiness Score. 
The new thresholds are much stricter and more realistic for interview prep.
"""

import pandas as pd


def parse_skill_data(skill_json):
    """
    Flattens the raw skill API response into a list of
    {tag_name, group, problems_solved} - one entry per REAL tag LeetCode
    has skill data for on this profile.
    """
    tags = []
    if not skill_json or not isinstance(skill_json, dict):
        return tags

    for group in ["fundamental", "intermediate", "advanced"]:
        entries = skill_json.get(group, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            tag_name = entry.get("tagName")
            tag_slug = entry.get("tagSlug")  # real slug from the API, when available
            solved = entry.get("problemsSolved", 0)
            if tag_name:
                tags.append({
                    "tag_name": tag_name,
                    "tag_slug": tag_slug,
                    "group": group,
                    "problems_solved": solved,
                })
    return tags


def build_dataframe_from_api(skill_json):
    """
    Builds the pattern DataFrame using REAL solved counts per REAL LeetCode tag.
    Confidence is derived from solve count using STRICT interview-ready thresholds:
        0 solved    -> 1 (Cold)
        1-4 solved  -> 2 (Beginner)
        5-14 solved -> 3 (Moderate - knows basics)
        15-29 solved-> 4 (Strong - recognizes patterns)
        30+ solved  -> 5 (Mastery)
    """
    tags = parse_skill_data(skill_json)

    rows = []
    for t in tags:
        solved = t["problems_solved"]
        
        # STRICTER THRESHOLDS APPLIED HERE
        if solved == 0:
            confidence = 1
        elif solved <= 4:
            confidence = 2
        elif solved <= 14:
            confidence = 3
        elif solved <= 29:
            confidence = 4
        else:
            confidence = 5

        rows.append({
            "pattern": t["tag_name"],
            "tag_slug": t.get("tag_slug"),  # real slug from the API, may be None for old test fixtures
            "group": t["group"],  
            "problems_solved": solved,
            "confidence": confidence,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["pattern", "tag_slug", "group", "problems_solved", "confidence"])
    return df


def build_dataframe(skill_json=None):
    """Backward-compatible wrapper for older imports and scripts."""
    if skill_json is None:
        skill_json = {
            "fundamental": [
                {"tagName": "Array", "problemsSolved": 40},
                {"tagName": "Two Pointers", "problemsSolved": 5},
                {"tagName": "Sliding Window", "problemsSolved": 2},
                {"tagName": "Stack", "problemsSolved": 0},
            ],
            "intermediate": [{"tagName": "Binary Tree", "problemsSolved": 8}],
            "advanced": [{"tagName": "Dynamic Programming", "problemsSolved": 1}],
        }
    return build_dataframe_from_api(skill_json)


if __name__ == "__main__":
    df = build_dataframe()
    print(df)