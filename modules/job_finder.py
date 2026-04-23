"""
modules/job_finder.py — Job search engine for CareerAI Pro.
Uses SerpAPI Google Jobs endpoint with caching to avoid redundant calls.
Falls back to curated demo jobs when API key is unavailable.
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Optional

import requests

from utils import db

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search.json"
CACHE_TTL    = 30  # minutes


# ─── Cache Helpers ───────────────────────────────────────────────────────────

def _make_cache_key(role: str, location: str, filters: dict) -> str:
    raw = f"{role.lower()}|{location.lower()}|{json.dumps(filters, sort_keys=True)}"
    return hashlib.md5(raw.encode()).hexdigest()


# ─── Job normaliser ──────────────────────────────────────────────────────────

def _normalise(raw: dict) -> dict:
    """Convert a SerpAPI job result into our standard format."""
    detected_ext = raw.get("detected_extensions", {})
    return {
        "title":            raw.get("title", "Unknown Role"),
        "company":          raw.get("company_name", "Unknown Company"),
        "location":         raw.get("location", "Not specified"),
        "posted_date":      raw.get("detected_extensions", {}).get("posted_at", "Recent"),
        "description_snippet": (raw.get("description") or "")[:200],
        "apply_link":       raw.get("related_links", [{}])[0].get("link", "") if raw.get("related_links") else "",
        "work_from_home":   detected_ext.get("work_from_home", False),
        "schedule_type":    detected_ext.get("schedule_type", "Full-time"),
    }


# ─── Demo Jobs (fallback) ────────────────────────────────────────────────────

def _demo_jobs(role: str, location: str) -> list[dict]:
    templates = [
        ("Senior {role}", "TechCorp Solutions", location, "2 days ago",
         "Join our growing team. Strong problem-solving skills required.", True, "Full-time",
         "https://linkedin.com"),
        ("{role} – Mid Level", "InnovateTech", location, "Today",
         "Exciting opportunity for a motivated professional. Hybrid work available.", False, "Full-time",
         "https://naukri.com"),
        ("Junior {role}", "StartupHub", location, "1 week ago",
         "Great learning environment. Mentorship provided. Competitive salary.", False, "Full-time",
         "https://indeed.com"),
        ("Remote {role}", "GlobalTech Inc", "Remote", "3 days ago",
         "100% remote role with flexible hours. Strong communication skills needed.", True, "Contract",
         "https://remoteok.io"),
        ("{role} Specialist", "Enterprise Corp", location, "5 days ago",
         "Drive key initiatives and collaborate with cross-functional teams.", False, "Full-time",
         "https://glassdoor.com"),
    ]
    return [
        {
            "title":            t[0].format(role=role),
            "company":          t[1],
            "location":         t[2],
            "posted_date":      t[3],
            "description_snippet": t[4],
            "work_from_home":   t[5],
            "schedule_type":    t[6],
            "apply_link":       t[7],
        }
        for t in templates
    ]


# ─── Main Search ─────────────────────────────────────────────────────────────

def search_jobs(
    role: str,
    location: str = "India",
    num_results: int = 20,
    filters: Optional[dict] = None,
) -> list[dict]:
    """
    Search for jobs using SerpAPI or return demo data.

    Args:
        role:        Job title / keyword
        location:    Location string
        num_results: Number of results to request
        filters:     Dict with keys: last_24h, last_week, remote, onsite

    Returns:
        List of normalised job dicts.
    """
    filters = filters or {}
    cache_key = _make_cache_key(role, location, filters)

    # Check cache first
    cached_raw = db.get_cached_jobs(cache_key)
    if cached_raw:
        try:
            return json.loads(cached_raw)
        except Exception:
            pass

    api_key = db.get_env_value("SERPAPI_KEY") or ""
    placeholder_fragments = ["your_serpapi", "your_key", "placeholder"]
    if not api_key or any(f in api_key.lower() for f in placeholder_fragments):
        logger.info("No SerpAPI key — returning demo jobs.")
        return _demo_jobs(role, location)

    # Build query
    query_parts = [role, location]
    if filters.get("remote"):
        query_parts.append("remote")
    if filters.get("onsite"):
        query_parts.append("onsite")
    query = " ".join(query_parts)

    params: dict = {
        "engine":   "google_jobs",
        "q":        query,
        "api_key":  api_key,
        "num":      min(num_results, 30),
        "hl":       "en",
    }

    if filters.get("last_24h"):
        params["chips"] = "date_posted:today"
    elif filters.get("last_week"):
        params["chips"] = "date_posted:week"

    try:
        resp = requests.get(SERPAPI_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise ValueError(f"SerpAPI error: {data['error']}")

        raw_jobs = data.get("jobs_results", [])
        jobs = [_normalise(j) for j in raw_jobs]

        # Cache the results
        db.set_cached_jobs(cache_key, json.dumps(jobs), ttl_minutes=CACHE_TTL)
        db.cleanup_expired_cache()

        return jobs if jobs else _demo_jobs(role, location)

    except requests.Timeout:
        logger.error("SerpAPI request timed out.")
        raise TimeoutError("Job search timed out. Please try again.")
    except requests.HTTPError as e:
        logger.error(f"SerpAPI HTTP error: {e}")
        raise ValueError(f"Job search failed: {e.response.status_code} {e.response.reason}")
    except Exception as exc:
        logger.exception(f"Job search error: {exc}")
        raise
