import re
from typing import List

# RFC-5321 compliant email regex (balanced between strictness and real-world coverage)
_EMAIL_PATTERN = re.compile(
    r"(?<![='\"])([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
    re.IGNORECASE,
)

# Common no-reply / role-based / generic patterns to discard
_NOISE_PATTERNS = re.compile(
    r"^(noreply|no[-.]?reply|donotreply|do[-.]not[-.]reply|mailer[-.]?daemon|"
    r"postmaster|bounce|bounces|notifications?|alerts?|"
    r"webmaster|hostmaster|abuse|spam|example|test|unsubscribe|privacy|"
    r"legal|press|media|billing|invoice|security|"
    r"devnull|null|nobody|daemon|robot|bot|automated|automatic)@",
    re.IGNORECASE,
)

# Wider noise filter for job-board scraping (keeps school contacts like info@, admin@, hr@)
_JOB_BOARD_NOISE_PATTERNS = re.compile(
    r"^(noreply|no[-.]?reply|donotreply|do[-.]not[-.]reply|mailer[-.]?daemon|"
    r"postmaster|bounce|bounces|notifications?|alerts?|support|help|info|"
    r"hello|contact|admin|careers|jobs|recruitment|hr|hiring|talent|"
    r"webmaster|hostmaster|abuse|spam|example|test|unsubscribe|privacy|"
    r"legal|press|media|marketing|sales|billing|accounts?|invoice|finance|"
    r"security|devnull|null|nobody|daemon|robot|bot|automated|automatic)@",
    re.IGNORECASE,
)

# Well-known job-platform own domains — emails from these are the platform,
# not an actual recruiter.  Scrapers hit the page HTML which often embeds the
# platform's own contact address.
_PLATFORM_DOMAINS = re.compile(
    r"@(jobberman|myjobmag|ngcareers|hotnigerianjobs|teachingnigeria|"
    r"indeed|linkedin|glassdoor|monster|ziprecruiter|dice|careerbuilder|"
    r"simplyhired|weworkremotely|remoteok|remote\.africa|crossover|"
    r"wellfound|angel\.co|dynamitejobs|flexjobs|upwork|fiverr|toptal|"
    r"infolandia|naijatrends|lagosjobs|example|sentry)\.\w+",
    re.IGNORECASE,
)


def extract_emails(text: str) -> List[str]:
    """Extract unique recruiter-grade email addresses from arbitrary text.

    Discards:
    - Generic role addresses (noreply, support, info, hr, careers …)
    - Addresses belonging to job-platform domains themselves
    - Clearly invalid / example addresses
    """
    if not text:
        return []
    found = _EMAIL_PATTERN.findall(text)
    seen: set[str] = set()
    result: List[str] = []
    for email in found:
        normalized = email.lower().strip(".")
        if normalized in seen:
            continue
        if _JOB_BOARD_NOISE_PATTERNS.match(normalized):
            continue
        if _PLATFORM_DOMAINS.search(normalized):
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def extract_school_emails(text: str) -> List[str]:
    """Extract email addresses from school/institution contact pages.

    Uses a less aggressive filter than extract_emails() — keeps addresses like
    info@, admin@, registrar@, ict@, principal@ which are the intended contact
    points for Nigerian educational institutions.

    Still discards: noreply, bounce, mailer-daemon, example.com, etc.
    """
    if not text:
        return []
    found = _EMAIL_PATTERN.findall(text)
    seen: set[str] = set()
    result: List[str] = []
    for email in found:
        normalized = email.lower().strip(".")
        if normalized in seen:
            continue
        if _NOISE_PATTERNS.match(normalized):
            continue
        if _PLATFORM_DOMAINS.search(normalized):
            continue
        # Skip placeholder / example emails
        if "example" in normalized or "your-email" in normalized:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
