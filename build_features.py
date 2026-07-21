import pandas as pd


def parse_skill_data(skill_json):
    tags = []
    if not skill_json or not isinstance(skill_json, dict):
        return tags

    for group in ["fundamental", "intermediate", "advanced"]:
        entries = skill_json.get(group, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            tag_name = entry.get("tagName")
            tag_slug = entry.get("tagSlug")
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

    tags = parse_skill_data(skill_json)

    rows = []
    for t in tags:
        solved = t["problems_solved"]
        
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
            "tag_slug": t.get("tag_slug"), 
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
