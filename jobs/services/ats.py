"""
ATS match-score calculator.
Compares a job listing against a user's resume data and returns 0-100.

Weights:
  Skills match          40 pts  (5 pts each, capped)
  Job-title relevance   25 pts  (8 pts per word hit, capped)
  Technologies          20 pts  (4 pts each, capped)
  Experience keywords   15 pts  (1 pt each, capped)

Stack intelligence layer adds a fit classification (match / partial / mismatch)
so users can instantly see when a job requires a different language stack.
"""
import re
from typing import Tuple, Dict, Any, List


_NOISE = {
    'with', 'using', 'from', 'that', 'this', 'have', 'been', 'were',
    'their', 'about', 'into', 'which', 'these', 'those', 'there',
    'would', 'could', 'shall', 'should', 'where', 'while', 'after',
}

# ── Backend language groups ────────────────────────────────────────────────────
# Each group is a set of tokens that strongly signal a specific primary language.
# Jobs or resumes hitting multiple tokens from one group → that group is active.
_LANG_GROUPS: Dict[str, List[str]] = {
    'python':     ['python', 'django', 'flask', 'fastapi', 'celery', 'asyncio', 'pydantic'],
    'java':       ['java', 'spring', 'springboot', 'hibernate', 'maven', 'gradle', 'jvm', 'kotlin'],
    'javascript': ['javascript', 'nodejs', 'express', 'nestjs', 'nextjs', 'nuxtjs', 'typescript', 'node.js'],
    'go':         ['golang', 'go', 'goroutine', 'gorm'],
    'ruby':       ['ruby', 'rails', 'sinatra', 'rspec'],
    'php':        ['php', 'laravel', 'symfony', 'wordpress', 'drupal'],
    'csharp':     ['c#', '.net', 'asp.net', 'dotnet', 'blazor', 'unity'],
    'rust':       ['rust', 'cargo', 'tokio', 'actix'],
    'scala':      ['scala', 'akka', 'play framework', 'spark'],
    'swift':      ['swift', 'swiftui', 'ios', 'xcode', 'objective-c'],
    'cpp':        ['c++', 'cpp', 'qt', 'boost', 'cmake'],
    'r':          ['rstats', 'shiny', 'tidyverse', 'ggplot'],
}

# Languages that are front-end-only and should not conflict with backend langs
_FRONTEND_ONLY = {'react', 'vue', 'angular', 'svelte', 'html', 'css', 'tailwind', 'jquery'}


def _clean(text: str) -> str:
    return re.sub(r'[^a-z0-9#.+ ]', ' ', text.lower())


def _tokens(text: str) -> set:
    return {w for w in _clean(text).split() if len(w) > 2 and w not in _NOISE}


def _detect_langs(text: str) -> Dict[str, int]:
    """Return {lang: hit_count} for each language group detected in text."""
    tl = ' ' + text.lower() + ' '
    hits: Dict[str, int] = {}
    for lang, patterns in _LANG_GROUPS.items():
        count = sum(1 for p in patterns if p in tl)
        if count:
            hits[lang] = count
    return hits


def _primary_langs(lang_hits: Dict[str, int], top_n: int = 3) -> List[str]:
    return [k for k, _ in sorted(lang_hits.items(), key=lambda x: -x[1])][:top_n]


def stack_fit_analysis(resume_data: dict, job_text: str) -> Dict[str, Any]:
    """
    Compare user's tech stack against job requirements.
    Returns a dict with: user_langs, job_langs, fit ('match'|'partial'|'mismatch')
    """
    # Build a text blob from user's resume
    skills_text = ' '.join(
        (s.get('name', '') if isinstance(s, dict) else str(s))
        for s in resume_data.get('skills', [])
    )
    tech_text = ' '.join(
        proj.get('technologies', '') or proj.get('tech_stack', '')
        for proj in resume_data.get('projects', [])
    )
    job_title = resume_data.get('personal', {}).get('job_title', '')
    resume_blob = f"{job_title} {skills_text} {tech_text}"

    user_lang_hits = _detect_langs(resume_blob)
    job_lang_hits = _detect_langs(job_text)

    user_langs = _primary_langs(user_lang_hits)
    job_langs = _primary_langs(job_lang_hits)

    if not user_langs or not job_langs:
        fit = 'unknown'
    else:
        # Direct overlap
        overlap = set(user_langs) & set(job_langs)
        if overlap:
            fit = 'match'
        else:
            # Check if job langs are a superset (polyglot job, user covers some)
            all_job_langs = set(job_lang_hits.keys())
            partial_hit = set(user_langs) & all_job_langs
            if partial_hit:
                fit = 'partial'
            else:
                # Clear mismatch — job strongly signals a different lang family
                dominant_job_lang = _primary_langs(job_lang_hits, top_n=1)
                if dominant_job_lang and dominant_job_lang[0] not in user_langs:
                    fit = 'mismatch'
                else:
                    fit = 'partial'

    return {
        'user_langs': user_langs,
        'job_langs': job_langs,
        'fit': fit,
    }


def calculate_ats_score(
    job_title: str,
    job_description: str,
    resume_data: dict,
) -> Tuple[int, Dict[str, Any]]:
    """Return (score_0_100, breakdown_dict)."""
    job_full = _clean(f"{job_title} {job_description}")
    job_tok = _tokens(job_full)

    breakdown: Dict[str, Any] = {}

    # ── 1. Skills ─────────────────────────────────────────────────────────────
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

    # ── 2. Job-title relevance ─────────────────────────────────────────────────
    title_words = [
        w for w in _clean(
            resume_data.get('personal', {}).get('job_title', '')
        ).split() if len(w) > 3
    ]
    title_hits = sum(1 for w in title_words if w in job_tok)
    title_score = min(25, title_hits * 8)
    breakdown['title'] = {'score': title_score, 'max': 25}

    # ── 3. Technologies (skills + projects) ───────────────────────────────────
    tech_terms: set = set()
    for proj in resume_data.get('projects', []):
        raw = proj.get('technologies', '') or proj.get('tech_stack', '')
        for t in raw.replace(',', ' ').split():
            t = t.strip().lower()
            if len(t) > 1:
                tech_terms.add(t)
    # Also include skills as tech terms (Python is both a skill and a technology)
    for s in skills:
        if s:
            tech_terms.add(s)

    matched_tech = [t for t in tech_terms if t and t in job_full]
    tech_score = min(20, len(matched_tech) * 4)
    breakdown['technologies'] = {
        'matched': matched_tech[:6],
        'score': tech_score,
        'max': 20,
    }

    # ── 4. Experience keywords ─────────────────────────────────────────────────
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

    # ── 5. Stack intelligence (no score impact — advisory only) ───────────────
    breakdown['stack'] = stack_fit_analysis(
        resume_data, f"{job_title} {job_description}"
    )

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
