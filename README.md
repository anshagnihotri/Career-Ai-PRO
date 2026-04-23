# 🚀 CareerAI Pro

An AI-powered career platform built with Python + Streamlit.

**Features:** Resume Lab & ATS Scoring · Live Job Search · Kanban Job Tracker · AI Career Coach · Interview Prep · Skill Roadmaps

---

## ⚡ Quick Start (Local)

### 1. Clone / unzip the project
```bash
cd careerai
```

### 2. Create virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys
Rename `.env.example` to `.env` and fill in your real keys:
```env
OPENAI_API_KEY=sk-...your-real-openai-key...
SERPAPI_KEY=...your-real-serpapi-key...
SECRET_KEY=any-random-string-for-sessions
```

- **OpenAI key:** https://platform.openai.com/api-keys
- **SerpAPI key:** https://serpapi.com/manage-api-key (100 free searches/month)

> ⚠️ The app works **without** these keys — it uses smart fallback responses and demo jobs. Add keys only to unlock live AI + real job search.

### 5. Run the app
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 📁 Project Structure

```
careerai/
├── app.py                  # Main Streamlit application
├── requirements.txt
├── .env                    # API keys (never commit to git)
├── database.db             # SQLite database (auto-created)
│
├── modules/
│   ├── auth.py             # Login / signup with bcrypt
│   ├── ats_scorer.py       # ATS scoring engine
│   ├── resume_parser.py    # PDF + DOCX parser
│   ├── chatbot.py          # OpenAI chatbot + fallback
│   ├── job_finder.py       # SerpAPI job search + cache
│   ├── job_tracker.py      # Kanban tracker CRUD
│   └── dashboard.py        # Charts and metrics
│
└── utils/
    ├── db.py               # SQLite database layer
    ├── helpers.py          # Shared utility functions
    └── styles.py           # Global CSS (dark theme)
```

---

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push your project to a **GitHub repository**  
   (make sure `.env` is in `.gitignore`)

2. Go to https://share.streamlit.io → **New app**

3. Set **Repository**, **Branch**, **Main file path** = `app.py`

4. Under **Advanced settings → Secrets**, add:
   ```toml
   OPENAI_API_KEY = "sk-..."
   SERPAPI_KEY = "..."
   SECRET_KEY = "..."
   ```

5. Click **Deploy** — live in ~2 minutes!

---

## 🔒 Security Notes

- Passwords are hashed with **bcrypt** (12 rounds) — never stored in plain text
- API keys are loaded from `.env` into SQLite at startup — never exposed in UI
- Add `.env` and `database.db` to `.gitignore` before pushing to GitHub

---

## 🛠️ Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Chatbot not responding | Check `OPENAI_API_KEY` in `.env` — app uses fallback without it |
| Job search returns demo jobs | Add real `SERPAPI_KEY` to `.env` and restart |
| PDF parsing fails | Ensure file is text-based (not a scanned image) |
| Port already in use | `streamlit run app.py --server.port 8502` |

---

## 📊 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit + Custom CSS |
| AI / LLM | OpenAI GPT-3.5-turbo |
| Job Search | SerpAPI Google Jobs |
| Database | SQLite (WAL mode) |
| Auth | bcrypt password hashing |
| Charts | Plotly |
| PDF parsing | pdfplumber + PyPDF2 |
| DOCX parsing | python-docx |

---

Built with ❤️ using 100% Python.
