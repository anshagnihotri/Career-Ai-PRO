"""
utils/styles.py — Global CSS for CareerAI Pro (premium dark theme).
Injected once via st.markdown(GLOBAL_CSS, unsafe_allow_html=True).
"""

GLOBAL_CSS = """
<style>
/* ─── Google Fonts ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

/* ─── CSS Variables ─────────────────────────────────────── */
:root {
  --bg-base:     #0a0c10;
  --bg-card:     #12151c;
  --bg-hover:    #181c26;
  --bg-input:    #1a1e2a;
  --accent:      #4f8cff;
  --accent-2:    #a78bfa;
  --accent-3:    #34d399;
  --danger:      #f87171;
  --warn:        #fbbf24;
  --text-1:      #f0f2f8;
  --text-2:      #8b92a8;
  --text-3:      #555d75;
  --border:      rgba(255,255,255,0.07);
  --radius:      14px;
  --radius-sm:   8px;
  --shadow:      0 4px 32px rgba(0,0,0,0.45);
  --font-head:   'Syne', sans-serif;
  --font-body:   'DM Sans', sans-serif;
}

/* ─── Base Reset ────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: var(--bg-base) !important;
  color: var(--text-1) !important;
  font-family: var(--font-body) !important;
}
[data-testid="stSidebar"] {
  background: #0e1118 !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
button[kind="header"] { display: none; }

/* ─── Typography ────────────────────────────────────────── */
h1,h2,h3,h4,h5,h6 {
  font-family: var(--font-head) !important;
  color: var(--text-1) !important;
  letter-spacing: -0.02em;
}

/* ─── Brand Mark ────────────────────────────────────────── */
.brand-mark {
  width: 42px; height: 42px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-head); font-weight: 800; font-size: 16px;
  color: #fff; letter-spacing: -1px;
  box-shadow: 0 0 20px rgba(79,140,255,0.35);
  margin-bottom: 12px;
}

/* ─── Auth Shell ────────────────────────────────────────── */
.auth-shell {
  max-width: 460px;
  margin: 60px auto 0;
  padding: 0 16px;
}
.hero-title {
  font-family: var(--font-head);
  font-size: 2.4rem; font-weight: 800;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin: 8px 0 4px;
}
.hero-subtitle {
  color: var(--text-2); font-size: 0.95rem; line-height: 1.6;
  margin-bottom: 28px;
}

/* ─── Page Hero ─────────────────────────────────────────── */
.page-hero {
  padding: 32px 0 24px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 28px;
}
.hero-kicker {
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--accent);
  margin-bottom: 6px;
}
.hero-heading {
  font-family: var(--font-head);
  font-size: 2rem; font-weight: 800;
  color: var(--text-1); line-height: 1.15; margin-bottom: 8px;
}
.hero-body { color: var(--text-2); font-size: 0.95rem; max-width: 600px; line-height: 1.6; }

/* ─── Career Shell ──────────────────────────────────────── */
.career-shell { padding: 0 8px; }

/* ─── Cards ─────────────────────────────────────────────── */
.career-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  transition: border-color 0.2s;
}
.career-card:hover { border-color: rgba(79,140,255,0.2); }

.select-card {
  cursor: pointer; text-align: center;
  transition: transform 0.18s, border-color 0.18s, box-shadow 0.18s;
}
.select-card:hover {
  transform: translateY(-3px);
  border-color: rgba(79,140,255,0.4);
  box-shadow: 0 8px 40px rgba(79,140,255,0.18);
}
.select-icon { font-size: 2.6rem; margin-bottom: 10px; }
.select-title {
  font-family: var(--font-head); font-size: 1.25rem; font-weight: 700;
  color: var(--text-1); margin-bottom: 6px;
}
.role-card-title {
  font-family: var(--font-head); font-size: 1.05rem; font-weight: 700;
  color: var(--text-1); margin-bottom: 4px;
}
.section-copy { color: var(--text-2); font-size: 0.88rem; line-height: 1.5; }
.section-title {
  font-family: var(--font-head); font-size: 1.05rem; font-weight: 700;
  color: var(--text-1); margin-bottom: 14px;
}

/* ─── Metric Cards ──────────────────────────────────────── */
.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 20px;
  text-align: center; margin-bottom: 20px;
}
.metric-label { font-size: 0.8rem; color: var(--text-2); margin-bottom: 6px; }
.metric-value {
  font-family: var(--font-head); font-size: 2rem; font-weight: 800;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.metric-foot { font-size: 0.72rem; color: var(--text-3); margin-top: 4px; }

/* ─── Skill Badges ──────────────────────────────────────── */
.skill-badge {
  display: inline-block;
  background: rgba(79,140,255,0.12);
  color: var(--accent);
  border: 1px solid rgba(79,140,255,0.25);
  border-radius: 20px; padding: 3px 11px;
  font-size: 0.78rem; font-weight: 500;
  margin: 3px 3px 3px 0;
}
.skill-badge.missing {
  background: rgba(248,113,113,0.1);
  color: var(--danger);
  border-color: rgba(248,113,113,0.25);
}

/* ─── Filter Chips ──────────────────────────────────────── */
.filter-chip {
  display: inline-block;
  background: var(--bg-input);
  color: var(--text-2);
  border: 1px solid var(--border);
  border-radius: 20px; padding: 2px 10px;
  font-size: 0.78rem; margin: 2px 3px;
}
.filter-chip-active {
  background: rgba(79,140,255,0.15);
  color: var(--accent);
  border-color: rgba(79,140,255,0.35);
}

/* ─── Score Ring ────────────────────────────────────────── */
.score-ring {
  width: 140px; height: 140px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 18px auto;
}
.score-ring-inner {
  width: 110px; height: 110px;
  border-radius: 50%;
  background: var(--bg-card);
  display: flex; align-items: center; justify-content: center;
}
.score-number {
  font-family: var(--font-head); font-size: 2.1rem; font-weight: 800;
  color: var(--text-1); text-align: center;
}
.score-caption { font-size: 0.72rem; color: var(--text-2); text-align: center; }

/* ─── Suggestion Cards ──────────────────────────────────── */
.suggestion-card {
  background: var(--bg-input); border-left: 3px solid var(--accent);
  border-radius: var(--radius-sm); padding: 10px 14px;
  font-size: 0.88rem; color: var(--text-1);
  margin-bottom: 8px; line-height: 1.5;
}

/* ─── Alert Cards ───────────────────────────────────────── */
.alert-card {
  border-radius: var(--radius-sm); padding: 12px 16px;
  font-size: 0.88rem; margin-bottom: 14px;
}
.alert-card.info    { background: rgba(79,140,255,0.1);  border-left: 3px solid var(--accent);  color: var(--text-1); }
.alert-card.warning { background: rgba(251,191,36,0.1);  border-left: 3px solid var(--warn);    color: var(--text-1); }
.alert-card.success { background: rgba(52,211,153,0.1);  border-left: 3px solid var(--accent-3);color: var(--text-1); }
.alert-card.error   { background: rgba(248,113,113,0.1); border-left: 3px solid var(--danger);  color: var(--text-1); }

/* ─── Setup Pill ────────────────────────────────────────── */
.setup-pill {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(251,191,36,0.08);
  border: 1px solid rgba(251,191,36,0.25);
  border-radius: 24px; padding: 6px 16px;
  font-size: 0.82rem; color: var(--warn);
  margin-bottom: 20px;
}
.glow-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--warn);
  box-shadow: 0 0 8px var(--warn);
  animation: pulse 1.8s ease infinite;
}
@keyframes pulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.5; transform: scale(1.3); }
}

/* ─── Job Cards ─────────────────────────────────────────── */
.job-avatar {
  width: 46px; height: 46px; border-radius: 10px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-head); font-weight: 800; font-size: 14px;
  color: #fff; flex-shrink: 0;
}
.job-meta { margin: 10px 0 8px; }

/* ─── Chat ──────────────────────────────────────────────── */
.chat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px; height: 100%;
}
.chat-scroll { 
  max-height: 440px; overflow-y: auto;
  padding: 8px 0; margin-bottom: 12px;
  scrollbar-width: thin; scrollbar-color: var(--text-3) transparent;
}
.user-bubble {
  background: linear-gradient(135deg, rgba(79,140,255,0.2), rgba(167,139,250,0.15));
  border: 1px solid rgba(79,140,255,0.2);
  border-radius: 14px 14px 4px 14px;
  padding: 10px 14px; margin: 6px 0 6px 20%;
  font-size: 0.9rem; color: var(--text-1); line-height: 1.55;
}
.ai-bubble {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 14px 14px 14px 4px;
  padding: 10px 14px; margin: 6px 20% 6px 0;
  font-size: 0.9rem; color: var(--text-1); line-height: 1.55;
}
.ai-bubble.typing {
  color: var(--text-2); font-style: italic; opacity: 0.7;
  animation: blink 1.2s ease infinite;
}
@keyframes blink { 0%,100% { opacity: 0.7; } 50% { opacity: 0.3; } }
.chat-input-shell { margin-top: 8px; }
.helper-list {
  color: var(--text-2); font-size: 0.88rem; line-height: 1.6;
  background: var(--bg-input); border-radius: var(--radius-sm);
  padding: 12px 16px; margin-bottom: 12px;
}

/* ─── Tracker ───────────────────────────────────────────── */
.tracker-column-title {
  font-family: var(--font-head); font-weight: 700; font-size: 0.9rem;
  color: var(--text-2); text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* ─── Sidebar Nav ───────────────────────────────────────── */
[data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  background: transparent !important;
  border: none !important;
  text-align: left !important;
  color: var(--text-2) !important;
  padding: 8px 12px !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.9rem !important;
  transition: background 0.15s, color 0.15s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--bg-hover) !important;
  color: var(--text-1) !important;
}

/* ─── Streamlit Overrides ───────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-1) !important;
}
.stButton > button {
  border-radius: var(--radius-sm) !important;
  font-family: var(--font-body) !important;
  font-weight: 500 !important;
  transition: all 0.18s !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
  border: none !important; color: #fff !important;
}
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--accent), var(--accent-2)) !important;
  border-radius: 4px !important;
}
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-2) !important;
  font-family: var(--font-body) !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
}
.stDataFrame { border-radius: var(--radius) !important; }
div[data-testid="stDecoration"] { display: none; }
#MainMenu, footer, header { visibility: hidden; }

/* ─── Scrollbar ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--text-3); border-radius: 3px; }

/* ─── Job search card ───────────────────────────────────── */
.job-search-card { margin-bottom: 20px; }

/* ─── Small muted ───────────────────────────────────────── */
.small-muted { font-size: 0.82rem; color: var(--text-2); }

/* ─── Roadmap ───────────────────────────────────────────── */
.roadmap-step {
  display: flex; gap: 14px; align-items: flex-start;
  background: var(--bg-input); border-radius: var(--radius-sm);
  padding: 12px 16px; margin-bottom: 10px;
}
.roadmap-num {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  display: flex; align-items: center; justify-content: center;
  font-size: 0.78rem; font-weight: 700; color: #fff;
}
.roadmap-content .title { font-weight: 600; font-size: 0.9rem; color: var(--text-1); }
.roadmap-content .desc  { font-size: 0.82rem; color: var(--text-2); margin-top: 2px; }
</style>
"""
