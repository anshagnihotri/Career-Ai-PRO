"""
modules/dashboard.py — Dashboard data and chart builders for CareerAI Pro.
"""

import logging

import plotly.express as px
import plotly.graph_objects as go

from utils import db
from modules.job_tracker import STATUSES

logger = logging.getLogger(__name__)

# ─── Shared Plotly theme ─────────────────────────────────────────────────────

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b92a8", family="DM Sans, sans-serif"),
    margin=dict(l=10, r=10, t=10, b=10),
    showlegend=False,
)


def get_dashboard_data(user_id: str) -> dict:
    ats_history = db.get_ats_history(user_id)
    jobs        = db.list_jobs(user_id)
    chats       = db.get_chat_history(user_id, limit=500)
    stats       = db.get_job_stats(user_id)

    latest_ats = ats_history[0]["score"] if ats_history else 0

    return {
        "latest_ats":  latest_ats,
        "ats_history": list(reversed(ats_history)),  # chronological
        "jobs":        jobs,
        "chats":       len(chats),
        "breakdown":   {s: stats.get(s, 0) for s in STATUSES},
    }


def build_skill_chart(skills: list[str], role_keywords: list[str]) -> go.Figure:
    """Radar/bar chart showing skill coverage vs role requirements."""
    if not role_keywords:
        fig = go.Figure()
        fig.add_annotation(
            text="Select a role to see skill coverage",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(color="#555d75", size=13),
        )
        fig.update_layout(**_LAYOUT)
        return fig

    skills_lower = [s.lower() for s in skills]
    matched  = [kw for kw in role_keywords if kw.lower() in skills_lower]
    missing  = [kw for kw in role_keywords if kw.lower() not in skills_lower]

    categories = matched[:6] + missing[:4]
    values     = [1] * len(matched[:6]) + [0] * len(missing[:4])
    colors     = ["#4f8cff"] * len(matched[:6]) + ["rgba(248,113,113,0.6)"] * len(missing[:4])

    if not categories:
        categories = ["No data"]
        values     = [0]
        colors     = ["#555d75"]

    fig = go.Figure(go.Bar(
        x=[c.title() for c in categories],
        y=values,
        marker_color=colors,
        marker_line_width=0,
    ))
    fig.update_layout(
        **_LAYOUT,
        xaxis=dict(tickangle=-30, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(visible=False),
    )
    return fig


def build_funnel_chart(breakdown: dict) -> go.Figure:
    statuses = [s for s in STATUSES if breakdown.get(s, 0) > 0]
    values   = [breakdown.get(s, 0) for s in statuses]

    if not any(values):
        fig = go.Figure()
        fig.add_annotation(
            text="Save jobs to see your application funnel",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(color="#555d75", size=13),
        )
        fig.update_layout(**_LAYOUT)
        return fig

    fig = go.Figure(go.Funnel(
        y=statuses,
        x=values,
        marker=dict(
            color=["#4f8cff", "#a78bfa", "#34d399", "#fbbf24", "#f87171"][: len(statuses)]
        ),
        textinfo="value+percent initial",
        connector=dict(line=dict(color="rgba(255,255,255,0.08)")),
    ))
    fig.update_layout(**_LAYOUT)
    return fig


def build_ats_timeline(ats_history: list[dict]) -> go.Figure:
    if not ats_history:
        fig = go.Figure()
        fig.add_annotation(
            text="Upload resumes to track your ATS score over time",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(color="#555d75", size=13),
        )
        fig.update_layout(**_LAYOUT)
        return fig

    dates  = [h["created_at"] for h in ats_history]
    scores = [h["score"] for h in ats_history]

    fig = go.Figure(go.Scatter(
        x=dates, y=scores,
        mode="lines+markers",
        line=dict(color="#4f8cff", width=2.5),
        marker=dict(color="#a78bfa", size=8, line=dict(color="#4f8cff", width=2)),
        fill="tozeroy",
        fillcolor="rgba(79,140,255,0.08)",
    ))
    fig.update_layout(
        **_LAYOUT,
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(range=[0, 105], gridcolor="rgba(255,255,255,0.05)"),
    )
    return fig
