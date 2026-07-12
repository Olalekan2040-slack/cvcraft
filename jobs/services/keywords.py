"""
Extract job search keywords from a user's resume data.
"""
from typing import List


# Generic stop-words to exclude from keyword lists
_STOP = {
    'with', 'using', 'from', 'that', 'this', 'have', 'been', 'were',
    'their', 'about', 'into', 'more', 'also', 'over', 'such', 'both',
}


def extract_keywords(resume_data: dict) -> List[str]:
    """Return deduplicated ordered list of keywords for job search + ATS."""
    seen = set()
    keywords = []

    def _add(term: str):
        t = term.strip().lower()
        if t and t not in seen and t not in _STOP and len(t) > 2:
            seen.add(t)
            keywords.append(t)

    personal = resume_data.get('personal', {})

    # Job title — highest signal
    job_title = personal.get('job_title', '')
    if job_title:
        _add(job_title)
        for word in job_title.split():
            _add(word)

    # Skills
    for skill in resume_data.get('skills', []):
        name = skill.get('name', '') if isinstance(skill, dict) else str(skill)
        _add(name)

    # Technologies from projects
    for proj in resume_data.get('projects', []):
        tech = proj.get('technologies', '') or proj.get('tech_stack', '')
        for t in tech.replace(',', ' ').split():
            _add(t)

    # Experience positions
    for exp in resume_data.get('experience', []):
        _add(exp.get('position', ''))

    # Education fields
    for edu in resume_data.get('education', []):
        _add(edu.get('field', ''))

    return keywords
