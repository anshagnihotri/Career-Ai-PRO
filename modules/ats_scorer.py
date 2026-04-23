"""
modules/ats_scorer.py — ATS scoring engine for CareerAI Pro.
Scores a parsed resume against role-specific keywords and best practices.
"""

import re
from typing import Optional

# ─── Role Keyword Bank ──────────────────────────────────────────────────────

KEYWORDS: dict[str, list[str]] = {
    "Software Developer": [
        "python", "java", "c++", "algorithms", "data structures", "oop",
        "rest api", "git", "agile", "sql", "docker", "unit testing",
        "design patterns", "microservices", "ci/cd", "linux",
    ],
    "Web Developer": [
        "html", "css", "javascript", "react", "node.js", "typescript",
        "responsive design", "rest api", "git", "webpack", "sass",
        "vue", "angular", "mongodb", "express", "graphql",
    ],
    "Data Scientist": [
        "python", "machine learning", "statistics", "pandas", "numpy",
        "scikit-learn", "tensorflow", "sql", "data visualization",
        "feature engineering", "a/b testing", "deep learning",
        "matplotlib", "jupyter", "regression", "classification",
    ],
    "AI/ML Engineer": [
        "python", "tensorflow", "pytorch", "deep learning", "nlp",
        "computer vision", "mlops", "docker", "kubernetes", "llm",
        "transformer", "fine-tuning", "model deployment", "cuda",
        "hugging face", "langchain", "rag", "openai api",
    ],
    "Cybersecurity": [
        "network security", "penetration testing", "ethical hacking",
        "firewalls", "siem", "vulnerability", "cryptography",
        "incident response", "owasp", "compliance", "linux",
        "wireshark", "metasploit", "risk assessment", "soc",
    ],
    "Cloud Engineer": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "ci/cd", "linux", "devops", "infrastructure as code",
        "serverless", "load balancing", "monitoring", "ansible",
        "cloud architecture", "cost optimization",
    ],
    "Marketing": [
        "seo", "sem", "google analytics", "content marketing",
        "social media", "email campaigns", "a/b testing",
        "brand strategy", "crm", "hubspot", "conversion rate",
        "market research", "paid ads", "kpi", "copywriting",
    ],
    "HR": [
        "recruitment", "talent acquisition", "onboarding", "hris",
        "performance management", "l&d", "compensation", "compliance",
        "employee engagement", "succession planning", "payroll",
        "labor law", "hr analytics", "diversity", "workforce planning",
    ],
    "Sales": [
        "crm", "salesforce", "lead generation", "pipeline management",
        "negotiation", "account management", "b2b", "revenue",
        "cold calling", "consultative selling", "forecasting",
        "quota", "upselling", "customer success", "demo",
    ],
    "Finance": [
        "excel", "financial modeling", "forecasting", "accounting",
        "risk management", "financial reporting", "budgeting",
        "valuation", "ifrs", "gaap", "power bi", "variance analysis",
        "cash flow", "p&l", "investment analysis", "audit",
    ],
    "Operations": [
        "supply chain", "process improvement", "erp", "six sigma",
        "lean", "project management", "logistics", "vendor management",
        "kpi", "capacity planning", "inventory", "sla",
        "root cause analysis", "cost reduction", "procurement",
    ],
}

ACTION_VERBS = [
    "achieved", "built", "created", "delivered", "designed",
    "developed", "drove", "engineered", "established", "executed",
    "implemented", "improved", "increased", "launched", "led",
    "managed", "optimized", "reduced", "scaled", "shipped",
    "spearheaded", "streamlined", "transformed", "architected",
]

SECTION_HEADERS = [
    "experience", "education", "skills", "projects",
    "summary", "objective", "certifications", "achievements",
]


# ─── Scoring Functions ───────────────────────────────────────────────────────

def _keyword_score(text: str, role: str) -> tuple[int, list[str], list[str]]:
    """Returns (score/35, matched_keywords, missing_keywords)."""
    keywords = KEYWORDS.get(role, [])
    if not keywords:
        return 20, [], []
    text_lower = text.lower()
    matched = [kw for kw in keywords if kw in text_lower]
    missing = [kw for kw in keywords if kw not in text_lower]
    ratio = len(matched) / len(keywords)
    score = round(ratio * 35)
    return min(score, 35), matched, missing


def _action_verb_score(text: str) -> int:
    """Returns score/15."""
    text_lower = text.lower()
    found = sum(1 for v in ACTION_VERBS if v in text_lower)
    ratio = min(found / 8, 1.0)
    return round(ratio * 15)


def _quantification_score(text: str) -> int:
    """Returns score/15 based on presence of numbers/percentages."""
    patterns = [
        r"\d+%",
        r"\$\d+",
        r"\d+x\b",
        r"\d+\+\s*(users|customers|clients|projects|features|team)",
        r"(increased|reduced|improved|saved|grew).*\d+",
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(hits * 3, 15)


def _section_score(text: str) -> int:
    """Returns score/15 based on presence of standard resume sections."""
    text_lower = text.lower()
    found = sum(1 for s in SECTION_HEADERS if s in text_lower)
    return min(round((found / 5) * 15), 15)


def _length_score(word_count: int) -> int:
    """Returns score/10 based on resume word count."""
    if 400 <= word_count <= 800:
        return 10
    if 300 <= word_count < 400 or 800 < word_count <= 1000:
        return 7
    if 200 <= word_count < 300 or 1000 < word_count <= 1200:
        return 4
    return 2


def _generate_suggestions(
    breakdown: dict,
    missing_keywords: list[str],
    word_count: int,
    role: str,
) -> list[str]:
    tips = []
    if breakdown["Keyword Match"] < 20:
        tips.append(f"Add more role-specific keywords. Missing: {', '.join(missing_keywords[:4])}.")
    if breakdown["Action Verbs"] < 10:
        tips.append("Start bullet points with strong action verbs: 'Developed', 'Optimized', 'Led'.")
    if breakdown["Quantified Impact"] < 9:
        tips.append("Quantify achievements: 'Increased efficiency by 30%', 'Saved $50K annually'.")
    if breakdown["Section Structure"] < 10:
        tips.append("Ensure your resume includes: Summary, Experience, Skills, Education, Projects.")
    if word_count < 350:
        tips.append("Resume is too brief. Expand each role with 3–5 bullet points of measurable impact.")
    if word_count > 950:
        tips.append("Resume is too long. Aim for 1 page (400–800 words) for roles under 10 years.")
    if breakdown["Keyword Match"] >= 28:
        tips.append("Strong keyword coverage! Tailor your summary to reinforce these matches.")
    if not tips:
        tips.append("Excellent resume! Consider adding a LinkedIn URL and GitHub profile link.")
    return tips[:6]


# ─── Main Entry Point ────────────────────────────────────────────────────────

def score_resume(resume_data: dict, role: str) -> dict:
    """
    Score a parsed resume dict against the given role.
    Returns a dict with total_score, breakdown, suggestions, missing_keywords.
    """
    full_text = " ".join([
        resume_data.get("raw_text", ""),
        " ".join(resume_data.get("skills", [])),
        " ".join(resume_data.get("experience", [])),
        " ".join(resume_data.get("projects", [])),
        " ".join(resume_data.get("education", [])),
    ])

    kw_score, matched_kw, missing_kw = _keyword_score(full_text, role)
    av_score  = _action_verb_score(full_text)
    qi_score  = _quantification_score(full_text)
    ss_score  = _section_score(full_text)
    len_score = _length_score(resume_data.get("word_count", 0))

    breakdown = {
        "Keyword Match":     kw_score,
        "Action Verbs":      av_score,
        "Quantified Impact": qi_score,
        "Section Structure": ss_score,
        "Resume Length":     len_score,
    }
    total = sum(breakdown.values())
    suggestions = _generate_suggestions(breakdown, missing_kw, resume_data.get("word_count", 0), role)

    return {
        "total_score":      total,
        "breakdown":        breakdown,
        "matched_keywords": matched_kw,
        "missing_keywords": missing_kw[:12],
        "suggestions":      suggestions,
    }
