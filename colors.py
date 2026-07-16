"""
colors.py

Single source of truth for every color in the app. Before this file,
app.py had a SECOND, slightly different red/amber/green trio
(#e74c3c/#f39c12/#2ecc71, "flat-ui" palette) hardcoded for the
difficulty donut and difficulty badges, separate from TIER_COLORS
(#EF4444/#F59E0B/#10B981). Both trios mean the exact same thing
(bad/medium/good) but don't match pixel-for-pixel, so the tier badges
and difficulty badges looked like they belonged to two different apps
sitting next to each other. DIFFICULTY_COLORS below just reuses
TIER_COLORS instead of duplicating a near-identical palette.

BG_COLOR/CARD_BG_COLOR/TEXT_COLOR are shared with .streamlit/config.toml
and theme.py, so the actual Streamlit theme and the custom
CSS/Plotly styling can't silently drift out of sync with each other.
"""

TIER_COLORS = {
    "Weak": "#EF4444",      # red
    "Moderate": "#F59E0B",  # amber
    "Strong": "#10B981",    # green
}

TIER_BG = {
    "Weak": "rgba(239, 68, 68, 0.1)",
    "Moderate": "rgba(245, 158, 11, 0.1)",
    "Strong": "rgba(16, 185, 129, 0.1)",
}

# Difficulty badges reuse the SAME semantic colors as tiers
# (Easy = the "good" green, Medium = the "medium" amber, Hard = the
# "bad" red) instead of a second, almost-but-not-quite-matching trio.
DIFFICULTY_COLORS = {
    "EASY": TIER_COLORS["Strong"],
    "MEDIUM": TIER_COLORS["Moderate"],
    "HARD": TIER_COLORS["Weak"],
}

# Non-semantic accent colors - for things that aren't "good/bad/medium"
# (a trend line, a behavioral-insight card), so they never fight with
# the tier/difficulty meaning above.
ACCENT_BLUE = "#3B82F6"
ACCENT_INDIGO = "#6366F1"

# Base surface colors. Mirrored in .streamlit/config.toml - if you
# change the look, change both places together.
BG_COLOR = "#0E1117"
CARD_BG_COLOR = "#161A23"
BORDER_COLOR = "rgba(255, 255, 255, 0.08)"
TEXT_COLOR = "#E5E7EB"
MUTED_TEXT_COLOR = "rgba(229, 231, 235, 0.65)"
