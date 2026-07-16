"""
theme.py

Two separate concerns split into two separate places, on purpose:

1. .streamlit/config.toml sets STREAMLIT'S OWN base theme (background,
   text, primary color). That's the file that actually decides whether
   the app looks intentionally dark or like white-background-with-
   invisible-white-text, depending on the viewer's default theme - it
   was missing entirely before this pass.
2. inject_custom_css() below adds the polish config.toml can't reach:
   a real font instead of the browser default, tighter/consistent
   spacing, subtle hover states on cards, and a nicer score panel.
   Called once at the top of main().

Nothing here is required for the app to function - if this import or
call ever fails for some reason, the dashboard still works, just
plainer. Keep it that way; a cosmetic layer should never be able to
break the actual data pipeline.
"""

import streamlit as st

from colors import CARD_BG_COLOR


def inject_custom_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Manrope', -apple-system, sans-serif;
        }}

        /* Stop Streamlit from dimming/fading the screen during reruns.
           Two selectors because Streamlit has renamed this test-id
           across versions - harmless if only one matches. */
        [data-testid="stAppViewBlockContainer"],
        [data-testid="stMainBlockContainer"] {{
            filter: none !important;
            opacity: 1 !important;
        }}

        h1, h2, h3 {{
            letter-spacing: -0.02em;
        }}

        /* Give Streamlit's built-in metric widgets an actual card look
           instead of bare numbers floating on the background. */
        [data-testid="stMetric"] {{
            background-color: {CARD_BG_COLOR};
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px;
            padding: 12px 16px 8px 16px;
        }}

        /* Revision-plan pattern cards: a bit of lift on hover so the
           list doesn't read as one static wall of boxes. */
        .stratify-plan-card {{
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            transition: box-shadow 0.15s ease;
        }}
        .stratify-plan-card:hover {{
            box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        }}

        /* Individual practice-problem link cards */
        .stratify-problem-card {{
            display: block;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .stratify-problem-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.35);
        }}

        .stratify-behavior-card {{
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }}

        /* Readiness score panel - a soft card instead of bare
           floating text in the middle of a column. */
        .stratify-score-panel {{
            text-align: center;
            padding: 20px 20px 24px 20px;
            background: linear-gradient(180deg, {CARD_BG_COLOR} 0%, rgba(22,26,35,0.35) 100%);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.06);
        }}
        .stratify-score-panel .stratify-score-value {{
            font-size: 48px;
            font-weight: 800;
            line-height: 1.1;
        }}
        .stratify-score-panel .stratify-score-caption {{
            opacity: 0.65;
            font-size: 13px;
            margin-top: 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
