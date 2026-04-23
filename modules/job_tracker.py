"""
modules/job_tracker.py — Job application tracker for CareerAI Pro.
"""

import logging
from typing import Optional

from utils import db

logger = logging.getLogger(__name__)

STATUSES = ["Saved", "Applied", "Interview", "Offer", "Rejected"]


def add_job(user_id: str, job: dict) -> tuple[bool, str]:
    try:
        db.save_job(user_id, job)
        return True, f"✅ '{job.get('title', 'Job')}' saved to your tracker!"
    except ValueError as e:
        return False, f"ℹ️ {e}"
    except Exception as exc:
        logger.exception("Failed to save job")
        return False, f"Failed to save job: {exc}"


def list_jobs(user_id: str) -> list[dict]:
    try:
        return db.list_jobs(user_id)
    except Exception as exc:
        logger.exception("Failed to list jobs")
        return []


def update_job(job_id: str, status: str, notes: str) -> tuple[bool, str]:
    if status not in STATUSES:
        return False, f"Invalid status: {status}"
    try:
        db.update_job(job_id, status, notes)
        return True, f"✅ Updated to {status}."
    except Exception as exc:
        logger.exception("Failed to update job")
        return False, f"Update failed: {exc}"


def delete_job(job_id: str) -> tuple[bool, str]:
    try:
        db.delete_job(job_id)
        return True, "🗑️ Job removed from tracker."
    except Exception as exc:
        logger.exception("Failed to delete job")
        return False, f"Delete failed: {exc}"


def get_pipeline_stats(user_id: str) -> dict:
    """Returns counts per status for the funnel chart."""
    jobs = list_jobs(user_id)
    counts = {s: 0 for s in STATUSES}
    for job in jobs:
        st = job.get("status", "Saved")
        if st in counts:
            counts[st] += 1
    return counts
