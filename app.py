"""
app.py — CareerAI Pro (Production-Grade)
AI-powered career platform: Resume Lab, Job Search, Tracker, AI Coach.

Run:
    streamlit run app.py

Requirements:
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
"""

import io
import logging
import math

import pandas as pd
import plotly.express as px
import streamlit as st

from modules import ats_scorer, auth, chatbot, dashboard, job_finder, job_tracker, resume_parser
from utils import db
from utils.helpers import chunk_list, format_chat_export, initials, sanitize_text
from utils.styles import GLOBAL_CSS

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────

ROLES = {
    "IT": [
        ("💻", "Software Developer",  "Algorithms, OOP, system design"),
        ("🌐", "Web Developer",        "HTML, CSS, JS, React, Node"),
        ("📊", "Data Scientist",       "Python, ML, statistics, visualization"),
        ("🤖", "AI/ML Engineer",       "Deep learning, NLP, MLOps"),
        ("🔐", "Cybersecurity",        "Networks, ethical hacking, compliance"),
        ("☁️", "Cloud Engineer",       "AWS, Azure, GCP, DevOps"),
    ],
    "Non-IT": [
        ("📣", "Marketing",   "SEO, campaigns, analytics, branding"),
        ("👥", "HR",          "Recruitment, HRIS, L&D, compliance"),
        ("💰", "Sales",       "CRM, negotiation, pipeline, revenue"),
        ("📈", "Finance",     "Accounting, forecasting, Excel, risk"),
        ("⚙️", "Operations",  "Supply chain, process improvement, ERP"),
    ],
}

PAGES = ["Dashboard", "Resume Lab", "Find Jobs", "Job Tracker", "AI Coach"]


# ─── Page Config & Styles ────────────────────────────────────────────────────

def _page_config():
    st.set_page_config(
        page_title="CareerAI Pro",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "logged_in":     False,
        "user_id":       "",
        "name":          "",
        "email":         "",
        "domain":        "",
        "role":          "",
        "page":          "Dashboard",
        "resume_data":   None,
        "ats_result":    None,
        "job_results":   [],
        "job_page":      1,
        "chat_messages": [],
        # Advanced feature flags
        "show_interview_gen":  False,
        "show_resume_improver": False,
        "show_roadmap":        False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _has_valid_key(env_key: str, placeholder: str) -> bool:
    val = (db.get_env_value(env_key) or "").strip()
    return bool(val) and placeholder.lower() not in val.lower()


def _setup_notice():
    missing = []
    if not _has_valid_key("OPENAI_API_KEY", "your_openai"):
        missing.append("OpenAI")
    if not _has_valid_key("SERPAPI_KEY", "your_serpapi"):
        missing.append("SerpAPI")
    if missing:
        keys_str = " &amp; ".join(missing)
        st.markdown(
            f'<div class="setup-pill"><span class="glow-dot"></span>'
            f'Connect {keys_str} in <code>.env</code> to unlock live AI + job search.</div>',
            unsafe_allow_html=True,
        )


def _page_hero(kicker: str, heading: str, body: str):
    st.markdown(
        f"""<div class="page-hero">
          <div class="hero-kicker">{sanitize_text(kicker)}</div>
          <div class="hero-heading">{sanitize_text(heading)}</div>
          <div class="hero-body">{sanitize_text(body)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ─── Auth ─────────────────────────────────────────────────────────────────────

def render_auth():
    st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
    st.markdown('<div class="brand-mark">CA</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">CareerAI Pro</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Your AI-powered career workspace for resume upgrades, '
        'live jobs, application tracking, and coaching.</div>',
        unsafe_allow_html=True,
    )

    login_tab, signup_tab = st.tabs(["🔑 Login", "✨ Sign Up"])

    with login_tab:
        with st.form("login_form"):
            email    = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Your password")
            submit   = st.form_submit_button("Log In", type="primary", use_container_width=True)
        if submit:
            ok, msgs, user = auth.login_user(email, password)
            for msg in msgs:
                (st.success if ok else st.error)(msg)
            if ok and user:
                st.session_state.update({
                    "logged_in":     True,
                    "user_id":       user["id"],
                    "name":          user["name"],
                    "email":         user["email"],
                    "chat_messages": db.get_chat_history(user["id"]),
                })
                st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            name     = st.text_input("Full Name", placeholder="Your name")
            email    = st.text_input("Email Address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="At least 8 characters")
            submit   = st.form_submit_button("Create Account", type="primary", use_container_width=True)
        if submit:
            ok, msgs = auth.signup_user(name, email, password)
            for msg in msgs:
                (st.success if ok else st.error)(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="brand-mark">CA</div>', unsafe_allow_html=True)
        st.markdown("## CareerAI Pro")
        st.caption(f"{st.session_state.name}  ·  {st.session_state.role or 'Choose role →'}")
        st.markdown("---")

        for page in PAGES:
            icon_map = {
                "Dashboard":   "📊",
                "Resume Lab":  "📄",
                "Find Jobs":   "🔍",
                "Job Tracker": "📌",
                "AI Coach":    "🤖",
            }
            label = f"{icon_map.get(page, '')} {page}"
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state.page = page
                st.rerun()

        st.markdown("---")
        if st.button("🔄 Change Domain / Role", use_container_width=True):
            st.session_state.domain = ""
            st.session_state.role   = ""
            st.rerun()
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ─── Domain Selection ─────────────────────────────────────────────────────────

def render_domain_selection():
    _page_hero(
        "Career Path Setup",
        "Choose your lane",
        "Pick the world you want CareerAI Pro to optimise for — this shapes role recommendations, "
        "ATS checks, job search, and AI coaching.",
    )
    cols = st.columns(2, gap="large")
    cards = [
        ("IT",     "💻", "Tech-first roles: software, data, cloud, security, AI."),
        ("Non-IT", "🏢", "Growth, business, operations, finance, HR, customer-facing."),
    ]
    for col, (domain, icon, desc) in zip(cols, cards):
        with col:
            st.markdown(
                f"""<div class="career-card select-card">
                  <div class="select-icon">{icon}</div>
                  <div class="select-title">{domain}</div>
                  <div class="section-copy">{desc}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(f"Select {domain}", key=f"domain_{domain}", use_container_width=True):
                st.session_state.domain = domain
                st.rerun()


# ─── Role Selection ───────────────────────────────────────────────────────────

def render_role_selection():
    _page_hero(
        st.session_state.domain,
        f"Pick your {st.session_state.domain} role",
        "Choose a target role so the platform can personalise resume feedback, "
        "live job matches, coaching prompts, and skills guidance.",
    )
    roles = ROLES.get(st.session_state.domain, [])
    for row in chunk_list(roles, 3):
        cols = st.columns(3, gap="large")
        for col, (icon, title, desc) in zip(cols, row):
            with col:
                tags_html = "".join(
                    f'<span class="skill-badge">{t.strip()}</span>'
                    for t in desc.split(",")
                )
                st.markdown(
                    f"""<div class="career-card select-card">
                      <div class="select-icon">{icon}</div>
                      <div class="role-card-title">{title}</div>
                      <div class="section-copy">{desc}</div>
                      <div style="margin-top:8px">{tags_html}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button(f"Choose {title}", key=f"role_{title}", use_container_width=True):
                    st.session_state.role = title
                    st.rerun()


# ─── Dashboard ────────────────────────────────────────────────────────────────

def render_dashboard():
    _page_hero(
        "Dashboard",
        f"Welcome back, {st.session_state.name} 👋",
        "Track your ATS strength, application momentum, coaching activity, "
        "and next actions — all from one polished workspace.",
    )
    data         = dashboard.get_dashboard_data(st.session_state.user_id)
    resume_data  = st.session_state.resume_data or {}
    role_kw      = ats_scorer.KEYWORDS.get(st.session_state.role, [])

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    metrics = [
        ("🎯 ATS Score",  data["latest_ats"],         "Latest upload"),
        ("💼 Jobs Saved", data["breakdown"]["Saved"],  "In tracker"),
        ("📤 Applied",    data["breakdown"]["Applied"], "Applications sent"),
        ("🤖 AI Chats",   data["chats"],               "Career coaching"),
    ]
    for col, (label, value, foot) in zip([m1, m2, m3, m4], metrics):
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div>'
                f'<div class="metric-foot">{foot}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Charts row
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Skill Match")
        st.plotly_chart(
            dashboard.build_skill_chart(resume_data.get("skills", []), role_kw),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Application Funnel")
        st.plotly_chart(
            dashboard.build_funnel_chart(data["breakdown"]),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Lower row
    ll, lr = st.columns(2, gap="large")
    with ll:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Recent Applications")
        jobs_df = pd.DataFrame(data["jobs"][:5]) if data["jobs"] else pd.DataFrame(
            columns=["job_title", "company", "status", "applied_date"]
        )
        if jobs_df.empty:
            st.markdown(
                '<div class="alert-card info">No applications yet. Save jobs from <strong>Find Jobs</strong>.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.dataframe(
                jobs_df[["job_title", "company", "status", "applied_date"]],
                use_container_width=True, hide_index=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with lr:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### 📈 ATS Score Timeline")
        st.plotly_chart(
            dashboard.build_ats_timeline(data["ats_history"]),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    qa1, qa2, qa3, qa4 = st.columns(4)
    for col, (label, target) in zip(
        [qa1, qa2, qa3, qa4],
        [("📄 Upload Resume", "Resume Lab"), ("🔍 Find Jobs", "Find Jobs"),
         ("🤖 AI Coach", "AI Coach"), ("📌 Tracker", "Job Tracker")],
    ):
        with col:
            if st.button(label, key=f"qa_{target}", use_container_width=True):
                st.session_state.page = target
                st.rerun()


# ─── Resume Lab ───────────────────────────────────────────────────────────────

def render_resume_lab():
    _page_hero(
        "Resume Lab",
        "Upload & stress-test your resume",
        "Parse your resume, score it for ATS readiness, and get focused improvement tips "
        "tailored to your selected role.",
    )

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF or DOCX, max 5 MB)", type=["pdf", "docx"]
    )
    if uploaded_file and uploaded_file.size > 5 * 1024 * 1024:
        st.error("File size exceeds 5 MB. Please upload a smaller file.")
        return

    if uploaded_file and st.button("🔍 Parse & Score Resume", type="primary"):
        progress = st.progress(0)
        status   = st.empty()
        try:
            status.info("📂 Reading file…")
            progress.progress(20)
            status.info("🔍 Extracting text…")
            progress.progress(40)
            resume_data = resume_parser.parse_resume(uploaded_file)
            status.info("🧠 Scoring against ATS criteria…")
            progress.progress(70)
            ats_result = ats_scorer.score_resume(resume_data, st.session_state.role)
            progress.progress(95)
            db.save_ats_score(st.session_state.user_id, st.session_state.role, ats_result["total_score"])
            progress.progress(100)
            status.success("✅ Done! Scroll down for your full report.")
            st.session_state.resume_data = resume_data
            st.session_state.ats_result  = ats_result
        except Exception as exc:
            progress.empty()
            status.error(f"Unable to parse resume: {exc}")
            return

    resume_data = st.session_state.resume_data
    ats_result  = st.session_state.ats_result
    if not resume_data or not ats_result:
        st.markdown(
            '<div class="alert-card info">Upload a resume above to unlock the full ATS insights panel.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Score ring + breakdown + gaps ──
    c1, c2, c3 = st.columns([1, 1, 1.2], gap="large")
    with c1:
        score = ats_result["total_score"]
        color = "#41d17d" if score >= 75 else "#f8c146" if score >= 55 else "#ff6b6b"
        grade = "Excellent" if score >= 75 else "Good" if score >= 55 else "Needs Work"
        st.markdown(
            f"""<div class="career-card" style="text-align:center">
              <div class="section-title">ATS Score</div>
              <div class="score-ring" style="background:conic-gradient({color} {score*3.6}deg,rgba(255,255,255,0.06) 0deg);">
                <div class="score-ring-inner">
                  <div>
                    <div class="score-number">{score}</div>
                    <div class="score-caption">out of 100</div>
                  </div>
                </div>
              </div>
              <div style="color:{color};font-weight:700;margin-top:4px">{grade}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown('<div class="career-card"><div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)
        max_map = {
            "Keyword Match": 35, "Action Verbs": 15, "Quantified Impact": 15,
            "Section Structure": 15, "Resume Length": 10,
        }
        for label, val in ats_result["breakdown"].items():
            mx = max_map.get(label, 10)
            pct = min(val / mx, 1.0)
            st.caption(f"{label}  {val}/{mx}")
            st.progress(pct)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="career-card"><div class="section-title">Skills & Gaps</div>', unsafe_allow_html=True)
        st.markdown("**✅ Extracted Skills**")
        skill_html = "".join(
            f'<span class="skill-badge">{sanitize_text(s)}</span>'
            for s in resume_data["skills"][:18]
        )
        st.markdown(skill_html or "<em>No skills detected</em>", unsafe_allow_html=True)
        st.markdown("<br>**⚠️ Missing Keywords**", unsafe_allow_html=True)
        if ats_result["missing_keywords"]:
            missing_html = "".join(
                f'<span class="skill-badge missing">{sanitize_text(s)}</span>'
                for s in ats_result["missing_keywords"]
            )
            st.markdown(missing_html, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="alert-card success">Great coverage! Your resume matches role keywords well.</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Profile + Tips ──
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### 👤 Extracted Profile")
        st.write({
            "Name":        resume_data["name"],
            "Email":       resume_data["email"],
            "Phone":       resume_data["phone"],
            "Education":   resume_data["education"][:4],
            "Experience":  resume_data["experience"][:5],
            "Projects":    resume_data["projects"][:4],
            "Word Count":  resume_data["word_count"],
            "Pages":       resume_data["page_count"],
        })
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### 💡 Improvement Tips")
        icons = ["⚠️", "✅", "💡", "⚠️", "💡", "✅"]
        for icon, tip in zip(icons, ats_result["suggestions"]):
            st.markdown(
                f'<div class="suggestion-card">{icon} {sanitize_text(tip)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Advanced Features ──
    st.markdown("---")
    st.markdown("### 🚀 Advanced Tools")
    t1, t2, t3 = st.tabs(["✍️ AI Resume Improver", "🎤 Interview Prep", "🗺️ Skill Roadmap"])

    with t1:
        st.markdown("Select a section from your resume and get an AI-powered rewrite.")
        section_choice = st.selectbox(
            "Which section to improve?",
            ["Experience", "Summary", "Projects", "Skills"],
        )
        section_text_map = {
            "Experience": "\n".join(resume_data.get("experience", [])),
            "Summary":    resume_data.get("summary", ""),
            "Projects":   "\n".join(resume_data.get("projects", [])),
            "Skills":     ", ".join(resume_data.get("skills", [])),
        }
        section_text = st.text_area(
            "Current content (auto-filled, edit as needed):",
            value=section_text_map.get(section_choice, ""),
            height=130,
        )
        if st.button("✨ Improve with AI", key="improve_btn", type="primary"):
            if not section_text.strip():
                st.warning("Please add some content to improve.")
            else:
                with st.spinner("CareerAI is crafting improvements…"):
                    improved = chatbot.generate_resume_improvement(
                        st.session_state.role, section_text, section_choice
                    )
                st.markdown(
                    f'<div class="career-card"><strong>Improved {section_choice}:</strong><br><br>{sanitize_text(improved)}</div>',
                    unsafe_allow_html=True,
                )

    with t2:
        st.markdown(f"Role-specific interview questions for **{st.session_state.role}**.")
        num_q = st.slider("Number of questions", 4, 15, 8)
        if st.button("🎤 Generate Questions", key="interview_btn", type="primary"):
            with st.spinner("Generating interview questions…"):
                questions = chatbot.generate_interview_questions(st.session_state.role, num_q)
            st.markdown(
                f'<div class="career-card">{sanitize_text(questions)}</div>',
                unsafe_allow_html=True,
            )

    with t3:
        st.markdown("Build a personalised 3-month learning roadmap based on your skill gaps.")
        missing = ats_result.get("missing_keywords", [])
        if missing:
            st.markdown("**Identified gaps:** " + ", ".join(
                f'<span class="skill-badge missing">{sanitize_text(s)}</span>' for s in missing[:6]
            ), unsafe_allow_html=True)
        if st.button("🗺️ Generate Roadmap", key="roadmap_btn", type="primary"):
            with st.spinner("Building your learning roadmap…"):
                roadmap = chatbot.generate_skill_roadmap(st.session_state.role, missing)
            st.markdown(
                f'<div class="career-card">{sanitize_text(roadmap)}</div>',
                unsafe_allow_html=True,
            )


# ─── Job Finder ───────────────────────────────────────────────────────────────

def render_job_finder():
    _page_hero(
        "Find Jobs",
        "Search live roles and build your pipeline",
        "Look for fresh opportunities, filter by fit, and save promising openings "
        "directly into your tracker.",
    )

    st.markdown('<div class="career-card job-search-card">', unsafe_allow_html=True)
    with st.form("job_search_form"):
        col1, col2, col3 = st.columns([1.5, 1.2, 0.8], gap="large")
        with col1:
            role = st.text_input("Role", value=st.session_state.role, placeholder="e.g. Data Scientist")
        with col2:
            location = st.text_input("Location", value="India", placeholder="e.g. Bangalore")
        with col3:
            num_results = st.selectbox("Results", [10, 20, 30], index=1)

        f1, f2, f3, f4 = st.columns(4)
        with f1: last_24h  = st.toggle("Last 24h")
        with f2: last_week = st.toggle("Last week")
        with f3: remote    = st.toggle("Remote")
        with f4: onsite    = st.toggle("On-site")
        submitted = st.form_submit_button("🔍 Search Jobs", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    active_filters = [
        item for item, flag in [
            ("Last 24h", last_24h), ("Last week", last_week),
            ("Remote", remote), ("On-site", onsite),
        ] if flag
    ]
    if active_filters:
        chips = "".join(
            f'<span class="filter-chip filter-chip-active">{f}</span>' for f in active_filters
        )
        st.markdown(chips, unsafe_allow_html=True)

    if submitted:
        with st.spinner("Searching live opportunities…"):
            try:
                results = job_finder.search_jobs(
                    role=role,
                    location=location,
                    num_results=num_results,
                    filters={"last_24h": last_24h, "last_week": last_week,
                             "remote": remote, "onsite": onsite},
                )
                st.session_state.job_results = results
                st.session_state.job_page    = 1
                if results:
                    st.success(f"Found {len(results)} jobs.")
            except Exception as exc:
                st.markdown(
                    f'<div class="alert-card warning"><strong>Search unavailable:</strong> {sanitize_text(str(exc))}</div>',
                    unsafe_allow_html=True,
                )
                if not _has_valid_key("SERPAPI_KEY", "your_serpapi"):
                    st.info("Add your real SerpAPI key to `.env` and restart the app.")

    jobs = st.session_state.job_results
    if not jobs:
        st.markdown(
            '<div class="alert-card info"><strong>No results yet.</strong> Run a search above. '
            'Demo jobs will appear if your SerpAPI key is not configured.</div>',
            unsafe_allow_html=True,
        )
        return

    per_page    = 10
    total_pages = max(1, math.ceil(len(jobs) / per_page))
    cur_page    = min(st.session_state.job_page, total_pages)
    start       = (cur_page - 1) * per_page
    cur_jobs    = jobs[start : start + per_page]

    for row in chunk_list(cur_jobs, 2):
        cols = st.columns(2, gap="large")
        for col, job in zip(cols, row):
            with col:
                avatar   = initials(job["company"])
                wfh_chip = "Remote" if job["work_from_home"] else "On-site"
                st.markdown(
                    f"""<div class="career-card">
                      <div style="display:flex;gap:14px;align-items:center">
                        <div class="job-avatar">{avatar}</div>
                        <div>
                          <div style="font-size:18px;font-weight:800">{sanitize_text(job["title"])}</div>
                          <div class="small-muted">{sanitize_text(job["company"])} · {sanitize_text(job["location"])}</div>
                        </div>
                      </div>
                      <div class="job-meta" style="margin-top:10px">
                        <span class="filter-chip">{wfh_chip}</span>
                        <span class="filter-chip">{sanitize_text(job["schedule_type"])}</span>
                        <span class="small-muted">Posted: {sanitize_text(job["posted_date"])}</span>
                      </div>
                      <div class="section-copy" style="margin-top:8px">{sanitize_text(job["description_snippet"])}…</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("💾 Save", key=f"save_{job['title']}_{job['company']}", use_container_width=True):
                        ok, msg = job_tracker.add_job(st.session_state.user_id, job)
                        (st.success if ok else st.info)(msg)
                with btn_col2:
                    link = job.get("apply_link", "")
                    if link and link.startswith("http"):
                        st.link_button("Apply →", link, use_container_width=True)
                    else:
                        st.button("Apply →", key=f"apply_dis_{job['title']}", disabled=True, use_container_width=True)

    # Pagination
    p1, p2, p3 = st.columns([1, 1, 2])
    with p1:
        if st.button("◀ Prev", disabled=cur_page <= 1):
            st.session_state.job_page -= 1
            st.rerun()
    with p2:
        if st.button("Next ▶", disabled=cur_page >= total_pages):
            st.session_state.job_page += 1
            st.rerun()
    with p3:
        st.caption(f"Page {cur_page} of {total_pages}  ·  {len(jobs)} total results")


# ─── Job Tracker ──────────────────────────────────────────────────────────────

def render_job_tracker():
    _page_hero(
        "Job Tracker",
        "Manage your application flow",
        "Keep every role organised from saved to offer — update status, add notes, "
        "and monitor conversion rates at a glance.",
    )

    jobs = job_tracker.list_jobs(st.session_state.user_id)
    total_saved     = len(jobs)
    total_applied   = sum(1 for j in jobs if j["status"] == "Applied")
    total_interview = sum(1 for j in jobs if j["status"] == "Interview")
    total_offer     = sum(1 for j in jobs if j["status"] == "Offer")

    i_rate = round((total_interview / max(total_saved, 1)) * 100)
    o_rate = round((total_offer     / max(total_saved, 1)) * 100)

    s1, s2, s3, s4 = st.columns(4)
    for col, (title, val) in zip(
        [s1, s2, s3, s4],
        [("Total Saved", total_saved), ("Applied", total_applied),
         ("Interview Rate", f"{i_rate}%"), ("Offer Rate", f"{o_rate}%")],
    ):
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{title}</div>'
                f'<div class="metric-value">{val}</div></div>',
                unsafe_allow_html=True,
            )

    if not jobs:
        st.markdown(
            '<div class="alert-card info" style="margin-top:20px">No saved jobs yet. '
            'Head to <strong>Find Jobs</strong> and save some positions.</div>',
            unsafe_allow_html=True,
        )
        return

    columns  = job_tracker.STATUSES
    trk_cols = st.columns(5, gap="medium")
    for col, status in zip(trk_cols, columns):
        with col:
            st.markdown(
                f'<div class="tracker-column-title">{status}</div>',
                unsafe_allow_html=True,
            )
            for job in [j for j in jobs if j["status"] == status]:
                st.markdown(
                    f'<div class="career-card"><strong>{sanitize_text(job["job_title"])}</strong>'
                    f'<br><span class="small-muted">{sanitize_text(job["company"])}</span></div>',
                    unsafe_allow_html=True,
                )
                new_status = st.selectbox(
                    "Status", job_tracker.STATUSES,
                    index=job_tracker.STATUSES.index(job["status"]),
                    key=f"status_{job['id']}", label_visibility="collapsed",
                )
                notes = st.text_area(
                    "Notes", value=job.get("notes", ""),
                    key=f"notes_{job['id']}", height=80,
                    label_visibility="collapsed", placeholder="Add notes…",
                )
                u1, u2 = st.columns(2)
                with u1:
                    if st.button("Update", key=f"upd_{job['id']}", use_container_width=True):
                        ok, msg = job_tracker.update_job(job["id"], new_status, notes)
                        (st.success if ok else st.error)(msg)
                        st.rerun()
                with u2:
                    if st.button("Delete", key=f"del_{job['id']}", use_container_width=True):
                        ok, msg = job_tracker.delete_job(job["id"])
                        (st.success if ok else st.error)(msg)
                        st.rerun()


# ─── AI Coach (Chatbot) ───────────────────────────────────────────────────────

def render_chatbot():
    _page_hero(
        "AI Coach",
        "Get role-aware career guidance",
        "Ask for resume rewrites, interview prep, skill-gap plans, and job-search strategy "
        "tailored to your latest profile.",
    )

    ats_result  = st.session_state.ats_result  or {"total_score": 0, "missing_keywords": []}
    resume_data = st.session_state.resume_data or {"skills": []}

    profile = {
        "name":             st.session_state.name,
        "role":             st.session_state.role,
        "domain":           st.session_state.domain,
        "ats_score":        ats_result["total_score"],
        "skills":           resume_data.get("skills", []),
        "missing_keywords": ats_result.get("missing_keywords", []),
    }

    left, right = st.columns([1, 1.5], gap="large")

    # ── Left: context panel ──
    with left:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Coaching Snapshot")
        st.markdown(f"**Target role:** {st.session_state.role or '—'}")
        st.markdown(f"**Domain:** {st.session_state.domain or '—'}")
        st.markdown(f"**ATS score:** {ats_result['total_score']}/100")

        st.markdown("**Top skills**")
        skills_html = "".join(
            f'<span class="skill-badge">{sanitize_text(s)}</span>'
            for s in resume_data.get("skills", [])[:8]
        )
        st.markdown(
            skills_html or '<span class="small-muted">Upload a resume to personalise coaching.</span>',
            unsafe_allow_html=True,
        )

        st.markdown("**Focus gaps**")
        gaps_html = "".join(
            f'<span class="skill-badge missing">{sanitize_text(s)}</span>'
            for s in ats_result.get("missing_keywords", [])[:6]
        )
        st.markdown(
            gaps_html or '<span class="small-muted">No major gaps detected yet.</span>',
            unsafe_allow_html=True,
        )

        if not _has_valid_key("OPENAI_API_KEY", "your_openai"):
            st.markdown(
                '<div class="alert-card warning" style="margin-top:12px">'
                '<strong>OpenAI key needed for full AI chat.</strong> '
                'Until then, the coach answers with smart fallback responses.</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Quick prompts
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Quick Prompts")
        quick_qs = [
            "How can I improve my ATS score?",
            f"What skills should I learn for {st.session_state.role}?",
            "Write me a strong resume summary",
            f"Prepare me for a {st.session_state.role} interview",
            "Give me a 30-60-90 day job search plan",
        ]
        for q in quick_qs:
            if st.button(q, key=f"qq_{q}", use_container_width=True):
                _handle_chat_turn(q, profile)

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "💾 Export Chat",
                data=format_chat_export(st.session_state.chat_messages),
                file_name="careerai_chat.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_b:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                db.clear_chat_history(st.session_state.user_id)
                st.session_state.chat_messages = []
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Right: chat interface ──
    with right:
        st.markdown('<div class="chat-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Conversation")

        if not st.session_state.chat_messages:
            st.markdown(
                '<div class="helper-list">'
                "Hi! I'm CareerAI Coach. I can help you with:<br>"
                "• Resume rewrites and ATS optimisation<br>"
                "• Interview question prep<br>"
                "• Skill gap analysis and learning roadmaps<br>"
                "• Job search strategy and LinkedIn tips<br><br>"
                "Type a message or pick a quick prompt →"
                "</div>",
                unsafe_allow_html=True,
            )

        # Render chat history
        st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
        for msg in st.session_state.chat_messages:
            css_class = "user-bubble" if msg["role"] == "user" else "ai-bubble"
            st.markdown(
                f'<div class="{css_class}">{sanitize_text(msg["content"])}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Input
        st.markdown('<div class="chat-input-shell">', unsafe_allow_html=True)
        with st.form("chat_form", clear_on_submit=True):
            prompt = st.text_area(
                "Message",
                placeholder="Ask for resume edits, interview questions, or a study plan…",
                height=100, label_visibility="collapsed",
            )
            send = st.form_submit_button("📨 Send", type="primary", use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

        if send and prompt.strip():
            _handle_chat_turn(prompt.strip(), profile)


def _handle_chat_turn(prompt: str, profile: dict):
    """Add user message, call AI, append response, persist both."""
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    chatbot.persist_chat_message(st.session_state.user_id, "user", prompt)

    # Call AI
    with st.spinner("CareerAI is thinking…"):
        try:
            ai_text = chatbot.get_chat_response(
                profile=profile,
                conversation=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_messages
                ],
            )
        except Exception as exc:
            logger.exception("Chat error")
            ai_text = f"Sorry, I encountered an issue: {exc}. Please try again."

    # Add AI response
    st.session_state.chat_messages.append({"role": "assistant", "content": ai_text})
    chatbot.persist_chat_message(st.session_state.user_id, "assistant", ai_text)
    st.rerun()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    _page_config()
    db.init_db()
    _init_state()

    if not st.session_state.logged_in:
        render_auth()
        return

    render_sidebar()
    st.markdown('<div class="career-shell">', unsafe_allow_html=True)
    _setup_notice()

    if not st.session_state.domain:
        render_domain_selection()
    elif not st.session_state.role:
        render_role_selection()
    else:
        page = st.session_state.page
        dispatch = {
            "Dashboard":   render_dashboard,
            "Resume Lab":  render_resume_lab,
            "Find Jobs":   render_job_finder,
            "Job Tracker": render_job_tracker,
            "AI Coach":    render_chatbot,
        }
        dispatch.get(page, render_dashboard)()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
