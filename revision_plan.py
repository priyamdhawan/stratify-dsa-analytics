"""
revision_plan.py (REWRITTEN v3 - merged "Smart Revision Engine")

Combines two things that were previously separate:

1. Real, unsolved LeetCode problems per pattern - fetched live and
   filtered against your real accepted-submission history, so the plan
   never recommends something you've already solved.
2. A behavioral diagnosis layer: reads solved-volume vs confidence to
   explain WHY a pattern is weak (cold start vs pattern-recognition gap
   vs "you've done the reps but the template hasn't clicked"), plus
   high-yield prioritization and Moderate-tier inclusion, capped so the
   plan stays focused instead of listing every imperfect pattern.

Note on the merge: an earlier draft of the diagnosis/high-yield logic
used a static PATTERN_LINKS / HIGH_YIELD_TOPICS dict keyed on the old
fixed 14-pattern names ("DP", "Trees", "Heaps"...). Real LeetCode tags
don't match those strings ("Dynamic Programming", "Binary Tree",
"Heap (Priority Queue)"...), so that version would have silently failed
to flag high-yield topics and fallen back to one generic link per
pattern. HIGH_YIELD_TAGS below is matched against real tag names
instead, and problem links come from the live /problems endpoint, not a
static dict.
"""

import re

from leetcode_api import get_problems_by_tag, get_recent_ac_submissions

MAX_PROBLEMS_PER_PATTERN = 4
MAX_PATTERNS_IN_PLAN = 6  # keep the plan focused instead of overwhelming
FETCH_POOL_SIZE = 40

DIFFICULTY_ORDER = {"EASY": 0, "MEDIUM": 1, "HARD": 2}

# Interview-frequent topics get prioritized ahead of niche ones at equal
# weakness. Matched case-insensitively against your REAL LeetCode tag
# names, so it keeps working no matter what tags your profile actually
# has (unlike a fixed pattern list).
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
    """
    Explains WHY a pattern is weak, not just that it is.

    Note: a pattern can land in "Moderate" tier purely by being relatively
    behind your strongest pattern (K-Means clusters relative to your own
    data, not against a fixed bar), so confidence itself can still be
    high (4-5) even for a Moderate-tier item. Checking confidence first
    avoids mislabeling an already-solid pattern as a "cold start".
    """
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
    """
    Pulls the set of solved problem slugs out of the /solved response so
    we can exclude already-solved problems from recommendations.

    Real shape (verified live): {"solved_slugs": [str, ...], "solved": [...]}
    - prefers the flat "solved_slugs" list directly when present (new
      provider), falls back to scanning individual submission dicts for
      older/alternate shapes so this doesn't silently break if the
      provider changes again.
    """
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
    """
    Pulls a flat list of {title, slug, difficulty} out of the
    /problems/tag/ response. Real shape (verified live):
      {"problems": [{"title", "title_slug", "difficulty", "paid_only"}]}
    Falls back to older key names too, defensively, in case the
    provider changes again.
    """
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
    """Real, unsolved problems for one tag, ranked easiest first."""
    raw = get_problems_by_tag(tag_slug, limit=FETCH_POOL_SIZE)
    candidates = _extract_problem_list(raw)

    unsolved = [p for p in candidates if p["slug"] not in solved_slugs]
    unsolved.sort(key=lambda p: DIFFICULTY_ORDER.get(p["difficulty"], 1))

    return unsolved[:MAX_PROBLEMS_PER_PATTERN]


def generate_plan(df, username):
    """
    Builds the revision plan:
      1. Includes Weak AND Moderate tiers (Strong is excluded).
      2. Sorts high-yield topics first, then lowest confidence, then
         lowest solved count.
      3. Caps at MAX_PATTERNS_IN_PLAN so it stays focused.
      4. Attaches a behavioral diagnosis + real unsolved problems to
         each pattern.

    Each plan item:
      {
        "pattern": str, "tier": "Weak"|"Moderate", "is_high_yield": bool,
        "problems_solved": int, "confidence": int,
        "diagnosis": str (html), "stats_summary": str,
        "problems": [{"title", "slug", "difficulty"}, ...],  # may be empty
        "tag_link": str,  # fallback if the live API returns nothing
      }
    """
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
        # Prefer the real slug the API gave us in build_features.py; only
        # guess if it's missing (e.g. older cached data / test fixtures).
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