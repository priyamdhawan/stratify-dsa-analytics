import re

from leetcode_api import get_problems_by_tag, get_recent_ac_submissions

MAX_PROBLEMS_PER_PATTERN = 4
MAX_PATTERNS_IN_PLAN = 6
FETCH_POOL_SIZE = 40

DIFFICULTY_ORDER = {"EASY": 0, "MEDIUM": 1, "HARD": 2}


HIGH_YIELD_TAGS = {
    "array", "string", "hash table", "two pointers", "sliding window",
    "binary search", "tree", "binary tree", "graph", "dynamic programming",
    "backtracking", "greedy", "heap (priority queue)", "linked list",
    "stack", "depth-first search", "breadth-first search", "matrix",
    "recursion", "sorting", "union find", "trie", "monotonic stack",
    "topological sort", "prefix sum",
}


def slugify_tag(tag_name):
    """'Two Pointers' -> 'two-pointers' (LeetCode's own tag slug format)."""
    return re.sub(r"[^a-z0-9]+", "-", tag_name.lower()).strip("-")


def _is_high_yield(pattern):
    return pattern.strip().lower() in HIGH_YIELD_TAGS


def _diagnose(solved, confidence):

    if confidence >= 4:
        return (
            "✅ <b>Solid, just relatively behind:</b> your confidence here "
            "is already high — this only shows up because it's weaker than "
            "your strongest pattern, not because it's an actual problem "
            "area. Light maintenance practice is enough."
        )
    elif solved >= 10 and confidence <= 3:
        return (
            "⚠️ <b>Learning gap:</b> high solve volume but low confidence "
            "usually means the core template hasn't clicked yet. Stop doing "
            "new problems here — re-derive 2–3 you've already solved from "
            "scratch on paper first."
        )
    elif solved > 3 and confidence <= 3:
        return (
            "🧠 <b>Pattern-recognition gap:</b> you know the basics but "
            "variations trip you up. Sort this tag by acceptance rate "
            "(descending) and do 3 high-acceptance mediums back to back."
        )
    else:
        return (
            "🚀 <b>Cold start:</b> not enough exposure yet. Skim a short "
            "conceptual explainer, then solve 2 easy problems before "
            "attempting a medium."
        )


def _extract_solved_slugs(ac_submissions_json):
  
    solved = set()
    if not ac_submissions_json:
        return solved

    if isinstance(ac_submissions_json, dict) and isinstance(ac_submissions_json.get("solved_slugs"), list):
        return set(ac_submissions_json["solved_slugs"])

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
            slug = sub.get("title_slug") or sub.get("titleSlug")
            if slug:
                solved.add(slug)
    return solved


def _extract_problem_list(problems_json):
 
    if not problems_json:
        return []

    problems = problems_json
    if isinstance(problems_json, dict):
        problems = (
            problems_json.get("problems")
            or problems_json.get("problemsetQuestionList")
            or problems_json.get("problemset_question_list")
            or problems_json.get("data")
            or []
        )

    result = []
    if isinstance(problems, list):
        for p in problems:
            title = p.get("title")
            slug = p.get("title_slug") or p.get("titleSlug")
            difficulty = (p.get("difficulty") or "MEDIUM").upper()
            is_paid = p.get("paid_only") or p.get("isPaidOnly") or p.get("paidOnly") or False
            if title and slug and not is_paid:
                result.append({"title": title, "slug": slug, "difficulty": difficulty})
    return result


def _recommend_problems_for_tag(tag_slug, solved_slugs):
   
    raw = get_problems_by_tag(tag_slug, limit=FETCH_POOL_SIZE)
    candidates = _extract_problem_list(raw)

    unsolved = [p for p in candidates if p["slug"] not in solved_slugs]
    unsolved.sort(key=lambda p: DIFFICULTY_ORDER.get(p["difficulty"], 1))

    return unsolved[:MAX_PROBLEMS_PER_PATTERN]


def generate_plan(df, username):
   
    if df.empty:
        return []

    needs_work = df[df["tier"].isin(["Weak", "Moderate"])].copy()
    if needs_work.empty:
        return []

    needs_work["is_high_yield"] = needs_work["pattern"].apply(_is_high_yield)
    needs_work = needs_work.sort_values(
        by=["is_high_yield", "confidence", "problems_solved"],
        ascending=[False, True, True],
    ).head(MAX_PATTERNS_IN_PLAN)

    solved_slugs = _extract_solved_slugs(get_recent_ac_submissions(username, limit=1000))

    plan = []
    for _, row in needs_work.iterrows():
        pattern = row["pattern"]
        solved = int(row["problems_solved"])
        confidence = int(row["confidence"])
      
        tag_slug = row.get("tag_slug") or slugify_tag(pattern)

        plan.append({
            "pattern": pattern,
            "tier": row["tier"],
            "is_high_yield": bool(row["is_high_yield"]),
            "problems_solved": solved,
            "confidence": confidence,
            "diagnosis": _diagnose(solved, confidence),
            "stats_summary": f"{solved} solved · {confidence}/5 confidence",
            "problems": _recommend_problems_for_tag(tag_slug, solved_slugs),
            "tag_link": f"https://leetcode.com/tag/{tag_slug}/",
        })

    return plan
