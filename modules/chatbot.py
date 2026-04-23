"""
modules/chatbot.py — AI Career Coach for CareerAI Pro.

FIXES applied:
  • Uses openai >= 1.0.0 client (client.chat.completions.create)
  • Maintains full conversation context passed from session state
  • Robust fallback responses when API is unavailable
  • Timeout handling and graceful error recovery
  • Persists messages to DB via utils.db
"""

import logging
import time
from typing import Optional

from utils import db

logger = logging.getLogger(__name__)

# ─── System Prompt Builder ───────────────────────────────────────────────────

def _build_system_prompt(profile: dict) -> str:
    skills_str  = ", ".join(profile.get("skills", [])[:10]) or "not provided"
    missing_str = ", ".join(profile.get("missing_keywords", [])[:6]) or "none detected"
    return f"""You are CareerAI Coach, an expert career advisor inside the CareerAI Pro platform.

USER PROFILE:
- Name: {profile.get("name", "the user")}
- Target Role: {profile.get("role", "not set")}
- Domain: {profile.get("domain", "not set")}
- ATS Score: {profile.get("ats_score", 0)}/100
- Current Skills: {skills_str}
- Skill Gaps: {missing_str}

YOUR RESPONSIBILITIES:
1. Provide personalized, actionable career advice for the user's target role
2. Help rewrite and improve resume sections when asked
3. Generate role-specific interview questions and model answers
4. Create detailed skill-gap learning roadmaps
5. Offer job search strategy and LinkedIn profile tips
6. Always be encouraging, specific, and practical

RESPONSE STYLE:
- Be conversational but professional
- Use bullet points for lists, keep responses focused
- Always reference the user's specific role and skills when relevant
- If ATS score is below 60, proactively suggest improvements
- Keep responses under 400 words unless asked for detailed content

Never say you cannot help. Always provide value in every response."""


# ─── Fallback Response Engine ────────────────────────────────────────────────

FALLBACK_RESPONSES = {
    "ats": (
        "To improve your ATS score, focus on three areas:\n\n"
        "**1. Keywords** — Mirror the job description's exact terms in your resume.\n"
        "**2. Format** — Use standard section headers: Experience, Education, Skills, Projects.\n"
        "**3. Impact** — Quantify achievements: '30% efficiency gain', '$50K cost saved'.\n\n"
        "Upload your resume in Resume Lab for a detailed breakdown."
    ),
    "skills": (
        "Building in-demand skills for your role:\n\n"
        "• Start with the fundamentals specific to your domain\n"
        "• Build 2–3 portfolio projects that solve real problems\n"
        "• Contribute to open-source or document your learning publicly\n"
        "• Platforms like Coursera, freeCodeCamp, and Kaggle are great starting points\n\n"
        "Consistency beats intensity — 30 focused minutes daily outperforms 4-hour weekend sessions."
    ),
    "interview": (
        "Strong interview preparation strategy:\n\n"
        "**Behavioral (STAR format):** Situation, Task, Action, Result\n"
        "• Prepare 5–7 stories that cover leadership, failure, conflict, impact\n\n"
        "**Technical:** Practice fundamentals + role-specific scenarios\n"
        "• Use LeetCode, HackerRank, or System Design Primer\n\n"
        "**Research:** Know the company's product, tech stack, recent news\n\n"
        "Ask smart questions at the end — it shows genuine interest."
    ),
    "resume": (
        "Resume improvement essentials:\n\n"
        "• **Summary** — 2–3 lines showing your value proposition\n"
        "• **Experience** — Use 'Action Verb + Task + Measurable Result' format\n"
        "• **Skills** — List technologies that match your target role's JD\n"
        "• **Projects** — Include GitHub links + quantify impact where possible\n"
        "• **Education** — Keep brief unless you're a fresh graduate\n\n"
        "Tailor your resume to each job posting for best results."
    ),
    "default": (
        "I'm here to help with your career journey! I can assist with:\n\n"
        "• Resume rewriting and ATS optimization\n"
        "• Interview question preparation\n"
        "• Skill gap analysis and learning roadmaps\n"
        "• Job search strategy and LinkedIn tips\n"
        "• Role-specific career advice\n\n"
        "What would you like to work on today?"
    ),
}


def _get_fallback(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["ats", "score", "keyword", "scan"]):
        return FALLBACK_RESPONSES["ats"]
    if any(w in prompt_lower for w in ["skill", "learn", "course", "roadmap", "gap"]):
        return FALLBACK_RESPONSES["skills"]
    if any(w in prompt_lower for w in ["interview", "question", "prepare", "answer"]):
        return FALLBACK_RESPONSES["interview"]
    if any(w in prompt_lower for w in ["resume", "cv", "rewrite", "improve", "summary"]):
        return FALLBACK_RESPONSES["resume"]
    return FALLBACK_RESPONSES["default"]


# ─── OpenAI Client ───────────────────────────────────────────────────────────

def _get_openai_client():
    """Build and return an OpenAI client using the DB-stored API key."""
    api_key = db.get_env_value("OPENAI_API_KEY") or ""
    placeholder_fragments = ["your_openai", "sk-placeholder", "your_key"]
    if not api_key or any(frag in api_key.lower() for frag in placeholder_fragments):
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, timeout=25.0)
    except ImportError:
        logger.error("openai package not installed. Run: pip install openai>=1.0.0")
        return None


# ─── Main API Call ───────────────────────────────────────────────────────────

def get_chat_response(profile: dict, conversation: list[dict]) -> str:
    """
    Generate an AI coaching response.

    Args:
        profile: dict with user details (role, domain, ats_score, skills, etc.)
        conversation: full message history as list of {role, content} dicts

    Returns:
        AI-generated response string (never empty).
    """
    if not conversation:
        return _get_fallback("")

    # Sanitize conversation — keep only role/content, filter empties
    clean_msgs = [
        {"role": m["role"], "content": m["content"]}
        for m in conversation
        if m.get("role") in ("user", "assistant") and m.get("content", "").strip()
    ]

    # Keep last 20 turns to stay within context limits
    clean_msgs = clean_msgs[-20:]

    last_user_msg = next(
        (m["content"] for m in reversed(clean_msgs) if m["role"] == "user"),
        "",
    )

    client = _get_openai_client()
    if client is None:
        logger.info("No valid OpenAI key — using fallback response.")
        return _get_fallback(last_user_msg)

    system_prompt = _build_system_prompt(profile)
    messages = [{"role": "system", "content": system_prompt}] + clean_msgs

    # Retry logic: up to 2 attempts
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=600,
                temperature=0.72,
                presence_penalty=0.1,
                frequency_penalty=0.1,
            )
            text = response.choices[0].message.content
            if text and text.strip():
                return text.strip()
        except Exception as exc:
            err_str = str(exc).lower()
            if "rate limit" in err_str and attempt == 0:
                logger.warning("Rate limited, retrying in 3s...")
                time.sleep(3)
                continue
            if "invalid api key" in err_str or "authentication" in err_str:
                logger.error("Invalid OpenAI API key.")
                return (
                    "⚠️ Your OpenAI API key appears to be invalid. "
                    "Please update it in your `.env` file and restart the app."
                )
            logger.exception(f"OpenAI API error (attempt {attempt + 1}): {exc}")
            break

    # Final fallback
    return _get_fallback(last_user_msg)


# ─── DB Persistence Helpers ──────────────────────────────────────────────────

def persist_chat_message(user_id: str, role: str, content: str) -> None:
    """Save a single chat message to the database."""
    try:
        db.save_chat_message(user_id, role, content)
    except Exception as exc:
        logger.error(f"Failed to persist chat message: {exc}")


# ─── Advanced Features ───────────────────────────────────────────────────────

def generate_interview_questions(role: str, num: int = 8) -> str:
    """Generate role-specific interview questions."""
    profile = {"role": role, "domain": "", "ats_score": 0, "skills": [], "missing_keywords": []}
    conversation = [
        {
            "role": "user",
            "content": (
                f"Generate exactly {num} interview questions for a {role} position. "
                "Include a mix of: behavioral (STAR), technical, and situational questions. "
                "For each question, provide a brief model answer outline. "
                "Format clearly with question number, the question, and 'Model Answer:' hint."
            ),
        }
    ]
    return get_chat_response(profile, conversation)


def generate_resume_improvement(role: str, resume_section: str, section_name: str) -> str:
    """Rewrite/improve a resume section for a given role."""
    profile = {"role": role, "domain": "", "ats_score": 0, "skills": [], "missing_keywords": []}
    conversation = [
        {
            "role": "user",
            "content": (
                f"Rewrite and improve the following {section_name} section for a {role} resume. "
                "Make it ATS-optimized, impact-driven, and compelling. "
                "Use action verbs and quantify achievements where possible.\n\n"
                f"Original content:\n{resume_section}"
            ),
        }
    ]
    return get_chat_response(profile, conversation)


def generate_skill_roadmap(role: str, missing_skills: list[str]) -> str:
    """Generate a learning roadmap to address skill gaps."""
    skills_str = ", ".join(missing_skills[:8]) if missing_skills else "general skills"
    profile = {"role": role, "domain": "", "ats_score": 0, "skills": [], "missing_keywords": []}
    conversation = [
        {
            "role": "user",
            "content": (
                f"Create a 3-month skill development roadmap for someone targeting a {role} role. "
                f"Focus on these gaps: {skills_str}. "
                "Structure it as: Month 1 (Foundation), Month 2 (Practice), Month 3 (Portfolio). "
                "Include specific resources, projects, and milestones for each phase."
            ),
        }
    ]
    return get_chat_response(profile, conversation)
