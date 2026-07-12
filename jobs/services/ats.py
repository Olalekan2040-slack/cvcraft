"""
ATS match-score calculator.
Compares a job listing against a user's resume data and returns 0-100.

Weights:
  Skills match          40 pts  (5 pts each, capped)
  Job-title relevance   25 pts  (8 pts per word hit, capped)
  Technologies          20 pts  (4 pts each, capped)
  Experience keywords   15 pts  (1 pt each, capped)
"""
import re
from typing import Tuple, Dict, Any


_NOISE = {
    'with', 'using', 'from', 'that', 'this', 'have', 'been', 'were',
    'their', 'about', 'into', 'which', 'these', 'those', 'there',
    'would', 'could', 'shall', 'should', 'where', 'while', 'after',
}


def _clean(text: str) -> str:
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower())


def _tokens(text: str) -> set:
    return {w for w in _clean(text).split() if len(w) > 2 and w not in _NOISE}


def calculate_ats_score(
    job_title: str,
    job_description: str,
    resume_data: dict,
) -> Tuple[int, Dict[str, Any]]:
    """Return (score_0_100, breakdown_dict)."""
    job_full = _clean(f"{job_title} {job_description}")
    job_tok = _tokens(job_full)

    breakdown: Dict[str, Any] = {}

    # ── 1. Skills ───────────────────────────────────────────────────────────
    skills = [
        (s.get('name', '') if isinstance(s, dict) else str(s)).lower()
        for s in resume_data.get('skills', [])
    ]
    matched_skills = [s for s in skills if s and s in job_full]
    skill_score = min(40, len(matched_skills) * 5)
    breakdown['skills'] = {
        'matched': matched_skills[:8],
        'total': len(skills),
        'score': skill_score,
        'max': 40,
    }

    # ── 2. Job-title relevance ───────────────────────────────────────────────
    title_words = [
        w for w in _clean(
            resume_data.get('personal', {}).get('job_title', '')
        ).split() if len(w) > 3
    ]
    title_hits = sum(1 for w in title_words if w in job_tok)
    title_score = min(25, title_hits * 8)
    breakdown['title'] = {'score': title_score, 'max': 25}

    # ── 3. Technologies ─────────────────────────────────────────────────────
    tech_terms: set = set()
    for proj in resume_data.get('projects', []):
        raw = proj.get('technologies', '') or proj.get('tech_stack', '')
        for t in raw.replace(',', ' ').split():
            t = t.strip().lower()
            if len(t) > 2:
                tech_terms.add(t)
    matched_tech = [t for t in tech_terms if t in job_full]
    tech_score = min(20, len(matched_tech) * 4)
    breakdown['technologies'] = {
        'matched': matched_tech[:6],
        'score': tech_score,
        'max': 20,
    }

    # ── 4. Experience keywords ───────────────────────────────────────────────
    exp_words: set = set()
    for exp in resume_data.get('experience', []):
        for bullet in exp.get('bullets', []):
            exp_words.update(
                w for w in _clean(bullet).split()
                if len(w) > 4 and w not in _NOISE
            )
    exp_hits = sum(1 for w in exp_words if w in job_tok)
    exp_score = min(15, exp_hits)
    breakdown['experience'] = {'score': exp_score, 'max': 15}

    total = min(100, skill_score + title_score + tech_score + exp_score)
    return total, breakdown


def score_label(score: int) -> str:
    if score >= 75:
        return 'Excellent'
    elif score >= 55:
        return 'Good'
    elif score >= 35:
        return 'Fair'
    return 'Low'


def score_css_class(score: int) -> str:
    if score >= 75:
        return 'ats-excellent'
    elif score >= 55:
        return 'ats-good'
    elif score >= 35:
        return 'ats-fair'
    return 'ats-low'
