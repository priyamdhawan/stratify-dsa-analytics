
import concurrent.futures

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from leetcode_api import get_solved_stats, get_skill_stats, get_recent_ac_submissions
from build_features import build_dataframe_from_api
from cluster_patterns import cluster_patterns
from readiness_score import calculate_readiness_score
from revision_plan import generate_plan
from colors import TIER_COLORS, TIER_BG, DIFFICULTY_COLORS, ACCENT_BLUE, ACCENT_INDIGO, TEXT_COLOR
import history_store
from forecast import forecast_readiness, forecast_metric, MIN_POINTS_FOR_FORECAST
from behavior import analyze_learning_behavior
from theme import inject_custom_css

def main():
    
    st.set_page_config(page_title="Stratify | DSA Analytics", layout="wide")
    inject_custom_css() 

    st.title("Stratify")
    st.markdown("Pulls your real LeetCode data and tells you exactly what to practice next.")
    st.markdown("---")

  
    st.sidebar.markdown("### Enter your LeetCode profile")
    username = st.sidebar.text_input(
        "LeetCode Username", placeholder="e.g., neetcode", autocomplete="username"
    )

    if st.sidebar.button("Refresh Data", width="stretch"):
        get_solved_stats.clear()
        get_skill_stats.clear()
        get_recent_ac_submissions.clear()

    st.sidebar.caption("Data is pulled automatically from your public LeetCode profile.")

 
    landing_placeholder = st.empty()
    
    if not username:
        with landing_placeholder.container():
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Paste your LeetCode username. See what's actually weak — not a guess.")
            st.write(
                "Stratify reads your real per-tag solve history and tells you what to practice "
                "next. No sliders, no self-rating — just your actual data."
            )

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### Where you're actually weak")
                st.caption("Grouped from your real per-tag solve counts — not a checklist you fill in yourself.")

            with col2:
                st.markdown("#### Problems you haven't solved yet")
                st.caption("Pulled live from LeetCode for each weak pattern, checked against your real solve history first.")

            with col3:
                st.markdown("#### Whether your pace is enough")
                st.caption("Tracks your real solve rate over time and projects it forward, so you find out before it's too late.")

            st.markdown("<br><br>", unsafe_allow_html=True)
            st.info("👈 **Enter your LeetCode username in the sidebar to generate your live dashboard.**")
            
        st.stop()
        

    landing_placeholder.empty()


    with st.spinner("Fetching your LeetCode stats..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_solved = executor.submit(get_solved_stats, username)
            future_skill = executor.submit(get_skill_stats, username)
            solved_data = future_solved.result()
            skill_data = future_skill.result()

    if not solved_data:
        st.error(
            "Couldn't fetch data for that username. Double-check it matches your exact "
            "LeetCode profile URL, or the API may be temporarily asleep."
        )
        st.stop()


    df = build_dataframe_from_api(skill_data)
    df = cluster_patterns(df)

    leetcode_total = solved_data.get("solvedProblem", 0)
    easy = solved_data.get("easySolved", 0)
    med = solved_data.get("mediumSolved", 0)
    hard = solved_data.get("hardSolved", 0)
    score = calculate_readiness_score(df, leetcode_total)


    history_store.log_snapshot(
        username=username,
        total_solved=leetcode_total,
        easy_solved=easy,
        medium_solved=med,
        hard_solved=hard,
        readiness_score=score,
    )


    tab1, tab2, tab3, tab4 = st.tabs(
        ["Overview & Bias", "Pattern Analytics", "Strategic Revision Plan", "Progress & Behavior"]
    )

    with tab1:
        st.markdown("#### Global LeetCode Statistics")
        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Solved", leetcode_total)
        c2.metric("Easy", easy)
        c3.metric("Medium", med)
        c4.metric("Hard", hard)

        st.divider()

        col_score, col_chart = st.columns(2)

        with col_score:
            st.markdown("#### Algorithmic Readiness Score")
            st.caption("A weighted composite score based on volume and pattern mastery.")
            st.progress(min(score / 100, 1.0))

            score_color = TIER_COLORS["Strong"] if score >= 70 else TIER_COLORS["Moderate"] if score >= 40 else TIER_COLORS["Weak"]
            st.markdown(f"""
            <div class="stratify-score-panel">
              <div class="stratify-score-value" style="color:{score_color};">{score}<span style="font-size:22px; opacity:0.5;">/100</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col_chart:
            st.markdown("#### Difficulty Bias Analysis")
            st.caption("Identifies if you are over-indexing on Easy problems.")
            if leetcode_total > 0:
                fig_donut = px.pie(
                    names=["Easy", "Medium", "Hard"],
                    values=[easy, med, hard],
                    hole=0.6,
                    color_discrete_sequence=[TIER_COLORS["Strong"], TIER_COLORS["Moderate"], TIER_COLORS["Weak"]]
                )
                fig_donut.update_traces(textinfo='percent+label', textfont_size=12, textfont_color="white")
                fig_donut.update_layout(
                    height=250,
                    margin=dict(l=0, r=0, t=10, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False
                )
                st.plotly_chart(fig_donut, width="stretch")

    with tab2:
        st.subheader("Pattern Confidence Heatmap")
        st.caption("Derived from your real solved counts per LeetCode tag.")

        df_sorted = df.sort_values("confidence")
        fig = go.Figure(data=go.Heatmap(
            z=[[c] for c in df_sorted["confidence"]],
            x=["Confidence"],
            y=df_sorted["pattern"],
            colorscale="RdYlGn",
            zmin=1, zmax=5,
            xgap=2, ygap=3,
            text=[[c] for c in df_sorted["confidence"]],
            texttemplate="%{text}",
            textfont={"size": 13},
            hovertemplate="<b>%{y}</b><br>Confidence: %{z}/5<extra></extra>",
            colorbar=dict(title="Level", thickness=15),
        ))
        fig.update_layout(
            height=max(450, 26 * len(df_sorted)),
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_COLOR),
        )
        st.plotly_chart(fig, width="stretch")

        st.divider()

        st.subheader("Problems Solved by Pattern")
        st.caption("Real solved counts per pattern, clustered by tier (Weak / Moderate / Strong).")

        bar_df = df.sort_values("problems_solved")
        fig2 = px.bar(
            bar_df,
            x="problems_solved",
            y="pattern",
            color="tier",
            orientation="h",
            color_discrete_map=TIER_COLORS,
            category_orders={"tier": ["Weak", "Moderate", "Strong"]},
            text="problems_solved",
            hover_data={"pattern": False, "problems_solved": True, "confidence": True, "tier": False},
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            height=max(400, 32 * len(bar_df)),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_COLOR),
            xaxis=dict(title="Problems Solved", gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(title=""),
            legend=dict(title="Tier"),
            margin=dict(l=10, r=40, t=10, b=10),
        )
        st.plotly_chart(fig2, width="stretch")

    with tab3:
        st.subheader("Actionable Revision Plan")
        st.caption("Weak + Moderate patterns, prioritized by interview frequency, with behavioral diagnosis.")

        with st.spinner("Pulling fresh practice problems for your weak patterns..."):
            plan = generate_plan(df, username)

        if not plan:
            st.success("No weak or moderate patterns detected — you're in good shape!")
        else:
            for i, item in enumerate(plan):
                color = TIER_COLORS.get(item["tier"], TIER_COLORS["Weak"])
                bg = TIER_BG.get(item["tier"], TIER_BG["Weak"])
                star = " ⭐ HIGH-YIELD" if item["is_high_yield"] else ""

                st.markdown(f"""
                <div class="stratify-plan-card" style="border-left: 4px solid {color}; background-color: {bg}; padding: 12px 16px; border-radius: 6px 6px 0 0; margin-bottom: 0;">
                  <span style="background-color:{color}; color:white; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600;">{item['tier'].upper()}{star}</span>
                  <h4 style="margin:8px 0 4px 0;">{item['pattern']}</h4>
                  <p style="margin:0 0 8px 0; opacity:0.7; font-size:12px;">{item['stats_summary']}</p>
                  <p style="margin:0; font-size:13px; line-height:1.5;">{item['diagnosis']}</p>
                </div>
                """, unsafe_allow_html=True)

                if item["problems"]:
                    cols = st.columns(len(item["problems"]))
                    for col, prob in zip(cols, item["problems"]):
                        pcolor = DIFFICULTY_COLORS.get(prob["difficulty"], "#999")
                        with col:
                            st.markdown(f"""
                            <a class="stratify-problem-card" href="https://leetcode.com/problems/{prob['slug']}/" target="_blank" style="text-decoration:none;">
                              <div style="border:1px solid {pcolor}; border-radius:6px; padding:10px 8px; text-align:center; height:100%;">
                                <div style="font-size:11px; color:{pcolor}; font-weight:700; letter-spacing:0.5px;">{prob['difficulty'].title()}</div>
                                <div style="font-size:13px; color:{TEXT_COLOR}; margin-top:4px;">{prob['title']}</div>
                              </div>
                            </a>
                            """, unsafe_allow_html=True)
                    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
                else:
                    st.caption(
                        f"Couldn't pull specific unsolved problems for **{item['pattern']}** right now — "
                        f"[browse the full tag list on LeetCode →]({item['tag_link']})"
                    )
                    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

    with tab4:
        st.subheader("Progress Over Time")
        st.caption(
            "Real logged history, not a guess. Stratify logs one snapshot per day, "
            "so this fills in as you keep using it."
        )

        history_df = history_store.get_history(username)

        if len(history_df) < 2:
            st.info(
                f"Logged today's snapshot ({len(history_df)} data point so far). "
                "Come back on a different day to start seeing a real trend line — "
                "this needs actual history, not a simulation."
            )
        else:
          
            st.markdown("##### Total Problems Solved")
            fig_solved = px.line(history_df, x="snapshot_date", y="total_solved", markers=True)
            fig_solved.update_traces(line_color=ACCENT_BLUE, marker=dict(size=8))
            fig_solved.update_layout(
                height=320,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT_COLOR),
                xaxis=dict(title="Date", gridcolor="rgba(255,255,255,0.1)"),
                yaxis=dict(title="Total Solved", gridcolor="rgba(255,255,255,0.1)"),
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_solved, width="stretch")

            solved_result = forecast_metric(history_df, "total_solved", days_ahead=30)
            if solved_result:
                current_total = int(history_df["total_solved"].iloc[-1])
                st.markdown(
                    f"**Projected in 30 days:** ~{int(solved_result['projected_value'])} problems solved "
                    f"<span style='opacity:0.6; font-size:12px;'>"
                    f"(currently {current_total}, based on your real solve rate over your "
                    f"{solved_result['num_points']} logged sessions)</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption(
                    f"Need at least {MIN_POINTS_FOR_FORECAST} logged sessions on different "
                    f"days for a forecast — currently have {len(history_df)}."
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.divider()

            
            st.markdown("##### Readiness Score (moves slowly on purpose)")
            st.caption(
                "This is an average across ALL your patterns, capped 0-100 - a couple of "
                "solves in one tag won't visibly move it. That's expected, not a problem. "
                "Check this over weeks, not days."
            )
            fig_trend = px.line(history_df, x="snapshot_date", y="readiness_score", markers=True)
            fig_trend.update_traces(line_color=TIER_COLORS["Strong"], marker=dict(size=6))
            fig_trend.update_layout(
                height=220,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT_COLOR, size=11),
                xaxis=dict(title="", gridcolor="rgba(255,255,255,0.1)"),
                yaxis=dict(title="Score", range=[0, 100], gridcolor="rgba(255,255,255,0.1)"),
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_trend, width="stretch")

            readiness_result = forecast_readiness(history_df, days_ahead=30)
            if readiness_result:
                st.caption(
                    f"At this pace: ~{readiness_result['projected_score']}/100 in 30 days "
                    f"(based on your {readiness_result['num_points']} logged sessions)."
                )

        st.divider()

        st.subheader("Learning Behavior")
        st.caption(
            "Read from your real accepted-submission timestamps over the last 30 days — "
            "rule-based date math on real data, not a trained model."
        )

        with st.spinner("Reading your recent submission activity..."):
            ac_data = get_recent_ac_submissions(username, limit=1000)
        behavior_result = analyze_learning_behavior(ac_data)

        st.markdown(f"""
        <div class="stratify-behavior-card" style="border-left: 4px solid {ACCENT_INDIGO}; background-color: rgba(99,102,241,0.1); padding: 12px 16px; border-radius: 6px;">
          <span style="background-color:{ACCENT_INDIGO}; color:white; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600;">{behavior_result['label'].upper()}</span>
          <p style="margin:8px 0 0 0; font-size:13px; line-height:1.5;">{behavior_result['detail']}</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
