"""
modules/resume_parser.py — Resume parsing engine for CareerAI Pro.
Supports PDF (pdfplumber + PyPDF2 fallback) and DOCX files.
Extracts: name, email, phone, skills, experience, education, projects.
"""

import io
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Skill / Section vocabulary ─────────────────────────────────────────────

KNOWN_SKILLS = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "r", "matlab", "scala", "dart",
    # Web
    "html", "css", "react", "vue", "angular", "node.js", "express",
    "django", "flask", "fastapi", "spring boot", "next.js", "tailwind",
    # Data / ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "matplotlib", "seaborn", "keras", "xgboost", "hugging face",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "ci/cd", "github actions", "linux",
    # DB
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "sqlite", "oracle", "dynamodb", "firebase",
    # Tools
    "git", "github", "jira", "confluence", "postman", "figma",
    "excel", "power bi", "tableau", "looker",
    # Soft / Business
    "agile", "scrum", "kanban", "project management", "communication",
    "leadership", "teamwork", "problem solving", "critical thinking",
    # Domain specific
    "rest api", "graphql", "microservices", "system design", "oop",
    "data structures", "algorithms", "unit testing", "seo", "crm",
    "salesforce", "hris", "six sigma", "lean", "erp",
}

SECTION_PATTERNS = {
    "experience": re.compile(
        r"(work\s*experience|professional\s*experience|experience|employment)", re.I
    ),
    "education": re.compile(r"(education|academic|qualification)", re.I),
    "skills": re.compile(r"(skills|technical\s*skills|core\s*competencies)", re.I),
    "projects": re.compile(r"(projects|portfolio|personal\s*projects)", re.I),
    "summary": re.compile(r"(summary|objective|profile|about)", re.I),
    "certifications": re.compile(r"(certifications?|certificates?|courses?)", re.I),
}


# ─── Text extraction ─────────────────────────────────────────────────────────

def _extract_text_pdf(file_bytes: bytes) -> str:
    """Try pdfplumber first, fallback to PyPDF2."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        text = "\n".join(pages)
        if len(text.strip()) > 100:
            return text
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")

    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}")
        return ""


def _extract_text_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.warning(f"DOCX parse failed: {e}")
        return ""


def _extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    uploaded_file.seek(0)  # reset for possible re-read

    if name.endswith(".pdf"):
        return _extract_text_pdf(raw)
    if name.endswith(".docx"):
        return _extract_text_docx(raw)
    raise ValueError(f"Unsupported file type: {uploaded_file.name}")


# ─── Field extractors ────────────────────────────────────────────────────────

def _extract_email(text: str) -> str:
    m = re.search(r"[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else ""


def _extract_phone(text: str) -> str:
    m = re.search(r"(\+?\d[\d\s\-().]{8,15}\d)", text)
    return m.group(0).strip() if m else ""


def _extract_name(text: str) -> str:
    """Heuristic: first non-empty line that looks like a person's name."""
    for line in text.split("\n")[:8]:
        line = line.strip()
        if 2 <= len(line.split()) <= 5 and re.match(r"^[A-Za-z\s'\-]+$", line):
            return line
    return ""


def _extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill.title() if len(skill.split()) == 1 else skill)
    return sorted(set(found))


def _split_sections(text: str) -> dict[str, str]:
    """Split resume text into named sections."""
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"_header": []}
    current = "_header"
    for line in lines:
        matched = False
        for sec_name, pattern in SECTION_PATTERNS.items():
            if pattern.match(line.strip()) and len(line.strip()) < 60:
                current = sec_name
                matched = True
                break
        if not matched:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v) for k, v in sections.items()}


def _extract_bullets(section_text: str, max_items: int = 8) -> list[str]:
    """Extract meaningful non-empty lines from a section."""
    items = []
    for line in section_text.split("\n"):
        line = line.strip().lstrip("•·-–*>").strip()
        if len(line) > 15:
            items.append(line)
        if len(items) >= max_items:
            break
    return items


def _count_pages(file_bytes: bytes, ext: str) -> int:
    if ext == "pdf":
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                return len(pdf.pages)
        except Exception:
            pass
    return 1


# ─── Main Entry Point ────────────────────────────────────────────────────────

def parse_resume(uploaded_file) -> dict:
    """
    Parse a resume file (PDF or DOCX).
    Returns a structured dict with all extracted fields.
    """
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        text = _extract_text_pdf(raw_bytes)
    elif ext == "docx":
        text = _extract_text_docx(raw_bytes)
    else:
        raise ValueError(f"Unsupported format: {ext}. Please upload PDF or DOCX.")

    if not text or len(text.strip()) < 50:
        raise ValueError("Could not extract text from this file. Ensure it is not a scanned image.")

    sections = _split_sections(text)
    words = text.split()

    return {
        "raw_text":    text,
        "name":        _extract_name(text),
        "email":       _extract_email(text),
        "phone":       _extract_phone(text),
        "skills":      _extract_skills(text),
        "experience":  _extract_bullets(sections.get("experience", ""), max_items=8),
        "education":   _extract_bullets(sections.get("education", ""), max_items=4),
        "projects":    _extract_bullets(sections.get("projects", ""), max_items=5),
        "summary":     sections.get("summary", "")[:500],
        "word_count":  len(words),
        "page_count":  _count_pages(raw_bytes, ext),
    }
