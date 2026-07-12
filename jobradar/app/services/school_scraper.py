"""
school_scraper.py
=================
Scrapes Nigerian schools (universities, polytechnics, secondary schools) across
Southwest, Southeast, Lagos, Abuja, and Ilorin — extracts email addresses from
their contact/about pages and builds job-listing rows that integrate with the
standard email dispatch pipeline.

Each school becomes a synthetic "job listing" with:
  title    = "Tech / AI Instructor"
  company  = school name
  location = city, state
  url      = school website
  raw_emails = emails extracted from the school's contact page
"""
import asyncio
import logging
import random
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.utils.email_extractor import extract_school_emails

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Curated PRIVATE SECONDARY SCHOOL database
# Format: (name, city_state, website)
# ---------------------------------------------------------------------------
NIGERIAN_SCHOOLS: List[tuple] = [

    # ── LAGOS ──────────────────────────────────────────────────────────────
    ("Atlantic Hall School", "Epe, Lagos", "https://atlantichall.edu.ng"),
    ("Dowen College", "Lekki, Lagos", "https://dowencollege.com"),
    ("Chrisland High School", "Victoria Island, Lagos",
     "https://chrislandschools.org"),
    ("Greensprings School", "Anthony Village, Lagos",
     "https://greenspringsschool.com"),
    ("Corona Secondary School", "Agbara, Lagos", "https://coronaschools.org"),
    ("Grange School", "Maryland, Lagos", "https://grangeschool.com"),
    ("Whiteplains British School", "Lekki, Lagos", "https://whiteplainsbriitsh.com"),
    ("Vivian Fowler Memorial College", "Lagos, Lagos", "https://vfmclagos.com"),
    ("Caleb British International School", "Lagos, Lagos", "https://caleb.edu.ng"),
    ("Capital Science Academy", "Ikeja, Lagos",
     "https://capitalscienceacademy.com"),
    ("Olashore International School", "Iloko-Ijesa, Osun", "https://olashore.com"),
    ("Nigerian Turkish International College Lagos",
     "Lagos, Lagos", "https://ntic.edu.ng"),
    ("Lead British International School",
     "Lekki, Lagos", "https://leadbritishschool.com"),
    ("Rainbow College", "Ogba, Lagos", "https://rainbowcollege.edu.ng"),
    ("Genevieve School", "Surulere, Lagos", "https://genevieveschool.com"),
    ("Birchfield College", "Ikorodu, Lagos", "https://birchfieldcollege.edu.ng"),
    ("Covenant Daughters College", "Ikorodu, Lagos",
     "https://covendaughterscolg.edu.ng"),
    ("Lifeforte International School", "Ibadan, Oyo", "https://lifeforte.com"),
    ("Harvard Group of Schools", "Isolo, Lagos", "https://harvardgroupschools.com"),
    ("Westside High School", "Lekki, Lagos", "https://westsidehighschool.edu.ng"),
    ("Meadow Hall School Lagos", "Lekki, Lagos", "https://meadowhall.edu.ng"),
    ("Day Waterman College", "Abeokuta, Ogun", "https://daywatermancollege.com"),
    ("Tenstrings Music Institute International School",
     "Lagos, Lagos", "https://tenstrings.edu.ng"),
    ("Sovereign Hill Schools", "Lagos, Lagos", "https://sovereignhillschools.com"),
    ("Lekki British International High School",
     "Lekki, Lagos", "https://lekkibritishschool.com"),

    # ── ABUJA / FCT ────────────────────────────────────────────────────────
    ("Loyola Jesuit College", "Abuja, FCT", "https://loyolajesuitcollege.edu.ng"),
    ("Premiere Academy", "Lugbe, Abuja", "https://premiereacademy.edu.ng"),
    ("Meadow Hall School Abuja", "Abuja, FCT", "https://meadowhall.edu.ng"),
    ("Corona Secondary School Abuja", "Abuja, FCT", "https://coronaschools.org"),
    ("Whiteplains British School Abuja", "Abuja, FCT", "https://whiteplains.edu.ng"),
    ("Harvestfield International School",
     "Abuja, FCT", "https://harvestfield.edu.ng"),
    ("Bethel Science Academy", "Abuja, FCT", "https://bethelscience.edu.ng"),
    ("Standard Bearers School", "Abuja, FCT", "https://standardbearers.edu.ng"),
    ("Nigerian Turkish International College Abuja",
     "Abuja, FCT", "https://ntic.edu.ng"),
    ("Lead British International School Abuja",
     "Abuja, FCT", "https://leadbritishschool.com"),
    ("Hill Crest School Abuja", "Abuja, FCT", "https://hillcrestabuja.edu.ng"),
    ("Regent Secondary School Abuja", "Abuja, FCT", "https://regentschool.edu.ng"),
    ("Noble Hall Leadership Academy", "Abuja, FCT", "https://noblehall.edu.ng"),
    ("Scholars' International College Abuja",
     "Abuja, FCT", "https://scholarsinternational.edu.ng"),
    ("De Covenant British School", "Abuja, FCT", "https://decovenantschool.edu.ng"),
    ("Starlite College Abuja", "Abuja, FCT", "https://starlitecollege.edu.ng"),
    ("Gwagwalada International Secondary School",
     "Gwagwalada, Abuja", "https://gissprivate.edu.ng"),

    # ── ILORIN / KWARA ─────────────────────────────────────────────────────
    ("Standard Global Academy", "Ilorin, Kwara",
     "https://standardglobalacademy.com"),
    ("Harmony International School", "Ilorin, Kwara",
     "https://harmonyintlschool.edu.ng"),
    ("Cherubim & Seraphim College Ilorin",
     "Ilorin, Kwara", "https://cscollege-ilorin.com"),
    ("St. Anthony's College Ilorin", "Ilorin, Kwara",
     "https://stanthonyilorin.edu.ng"),
    ("Babs Fafunwa Millennium Schools",
     "Ilorin, Kwara", "https://babsfafunwa.edu.ng"),
    ("Crown International College Ilorin",
     "Ilorin, Kwara", "https://crownilorin.edu.ng"),
    ("Bright Future International School Ilorin",
     "Ilorin, Kwara", "https://brightfutureilorin.edu.ng"),
    ("Oyun Baptist High School", "Offa, Kwara", "https://oyunbaptisths.edu.ng"),
    ("De Learners Academy Ilorin", "Ilorin, Kwara", "https://delearnersacademy.com"),
    ("Graceland International School Ilorin",
     "Ilorin, Kwara", "https://gracelandilorin.edu.ng"),

    # ── SOUTHWEST — OYO (IBADAN) ─────────────────────────────────────────
    ("Lifeforte International School Ibadan",
     "Ibadan, Oyo", "https://lifeforte.com"),
    ("International School Ibadan", "Ibadan, Oyo", "https://isiui.edu.ng"),
    ("Loyola College Ibadan", "Ibadan, Oyo", "https://loyolacollegeibadan.edu.ng"),
    ("Educare Trust School", "Ibadan, Oyo", "https://educare-trust.edu.ng"),
    ("Base Life Schools", "Ibadan, Oyo", "https://baselifeschools.com"),
    ("St. Anne's School Ibadan", "Ibadan, Oyo", "https://stannesibadan.edu.ng"),
    ("Hillcrest School Ibadan", "Ibadan, Oyo", "https://hillcrestibadan.edu.ng"),
    ("Emmanuel High School Ibadan", "Ibadan, Oyo",
     "https://emmanuelhighschool-ibadan.edu.ng"),
    ("Christ Apostolic Church Grammar School Ibadan",
     "Ibadan, Oyo", "https://cacgrammar.edu.ng"),
    ("New Era High School Ibadan", "Ibadan, Oyo",
     "https://newerahighschoolibadan.edu.ng"),
    ("Nigerian Turkish Nile College Ibadan",
     "Ibadan, Oyo", "https://nilecollege-ibadan.edu.ng"),

    # ── SOUTHWEST — OSUN ─────────────────────────────────────────────────
    ("Olashore International School", "Iloko-Ijesa, Osun", "https://olashore.com"),
    ("BOWEN Schools Iwo", "Iwo, Osun", "https://bowenschools.edu.ng"),
    ("Immaculate Conception College Osogbo",
     "Osogbo, Osun", "https://iccollegeosogbo.edu.ng"),
    ("Obafemi Awolowo University International School",
     "Ile-Ife, Osun", "https://oauintlschool.edu.ng"),
    ("Oduduwa College Ile-Ife", "Ile-Ife, Osun", "https://oduduwacollege.edu.ng"),
    ("Adventist Grammar School Ile-Ife",
     "Ile-Ife, Osun", "https://adventistgrammar.edu.ng"),
    ("Wesley College Ilesa", "Ilesa, Osun", "https://wesleycollege-ilesa.edu.ng"),
    ("Joseph Ayo Babalola International School",
     "Ikeji-Arakeji, Osun", "https://jabuintlschool.edu.ng"),
    ("Redeemers High School Osogbo", "Osogbo, Osun",
     "https://redeemershighschool-osogbo.edu.ng"),
    ("Deeper Life High School Osogbo", "Osogbo, Osun", "https://dls-osogbo.edu.ng"),

    # ── SOUTHWEST — ONDO ─────────────────────────────────────────────────
    ("Aquinas College Akure", "Akure, Ondo", "https://aquinascollege.edu.ng"),
    ("Bethlehem Girls College Akure", "Akure, Ondo",
     "https://bethlehemcollege.edu.ng"),
    ("Nigerian Turkish Nile College Akure",
     "Akure, Ondo", "https://nilecollege-akure.edu.ng"),
    ("Ikogosi Model School", "Ikogosi, Ondo", "https://ikogosischool.edu.ng"),
    ("Excel International College Akure",
     "Akure, Ondo", "https://excelintlcollege.edu.ng"),
    ("Hallmark International School Akure",
     "Akure, Ondo", "https://hallmarkintl-akure.edu.ng"),
    ("Day Secondary School Akure", "Akure, Ondo",
     "https://daysecondaryschoakure.edu.ng"),
    ("Redeemers High School Akure", "Akure, Ondo",
     "https://redeemershighschool-akure.edu.ng"),
    ("Elizade International School", "Ilara-Mokin, Ondo",
     "https://elizadeintlschool.edu.ng"),

    # ── SOUTHWEST — EKITI ────────────────────────────────────────────────
    ("Christ's School Ado-Ekiti", "Ado-Ekiti, Ekiti",
     "https://christsschoolekiti.edu.ng"),
    ("Bishop Phillips Academy", "Ado-Ekiti, Ekiti", "https://bpaekiti.edu.ng"),
    ("Nigerian Turkish Nile College Ekiti",
     "Ado-Ekiti, Ekiti", "https://nilecollege-ekiti.edu.ng"),
    ("Hallmark International School Ekiti",
     "Ado-Ekiti, Ekiti", "https://hallmarkintl-ekiti.edu.ng"),
    ("Redeemers International School Ekiti",
     "Ado-Ekiti, Ekiti", "https://redeemersintl-ekiti.edu.ng"),
    ("Daystar High School Ado-Ekiti", "Ado-Ekiti, Ekiti",
     "https://daystarhighschool-ekiti.edu.ng"),

    # ── SOUTHWEST — OGUN ─────────────────────────────────────────────────
    ("Mayflower School Ikenne", "Ikenne, Ogun", "https://mayflowerschool.edu.ng"),
    ("Day Waterman College Abeokuta", "Abeokuta, Ogun",
     "https://daywatermancollege.com"),
    ("Nigerian Turkish Nile College Sagamu",
     "Sagamu, Ogun", "https://nilecollege-ogun.edu.ng"),
    ("Hillcrest Secondary School Sagamu",
     "Sagamu, Ogun", "https://hillcrestsagamu.edu.ng"),
    ("Gateway International School Abeokuta",
     "Abeokuta, Ogun", "https://gatewayintlschool.edu.ng"),
    ("Excel International College Sagamu",
     "Sagamu, Ogun", "https://excelintlsagamu.edu.ng"),
    ("Deeper Life High School Sagamu", "Sagamu, Ogun", "https://dls-sagamu.edu.ng"),
    ("Fountain Heights Secondary School",
     "Abeokuta, Ogun", "https://fountainheights.edu.ng"),

    # ── SOUTHEAST — ANAMBRA ──────────────────────────────────────────────
    ("Fidelity High School Onitsha", "Onitsha, Anambra",
     "https://fidelityhighschoolonitsha.edu.ng"),
    ("Dennis Memorial Grammar School Onitsha",
     "Onitsha, Anambra", "https://dmgsonitsha.edu.ng"),
    ("Christ the King College Onitsha",
     "Onitsha, Anambra", "https://ckcschool.edu.ng"),
    ("All Saints Secondary School Onitsha",
     "Onitsha, Anambra", "https://allsaintsonitsha.edu.ng"),
    ("Saint Joseph's Secondary School Awka",
     "Awka, Anambra", "https://stjosephawka.edu.ng"),
    ("Hillcrest Secondary School Awka",
     "Awka, Anambra", "https://hillcrestawka.edu.ng"),
    ("Christ the King International School Nnewi",
     "Nnewi, Anambra", "https://ctkintlnnewi.edu.ng"),
    ("Our Lady of Lourdes College Onitsha",
     "Onitsha, Anambra", "https://ollconitsha.edu.ng"),
    ("Nigerian Turkish Nile College Onitsha",
     "Onitsha, Anambra", "https://nilecollege-onitsha.edu.ng"),
    ("Greater Evangelism Schools Awka", "Awka, Anambra",
     "https://gevangelismschoolsawka.edu.ng"),

    # ── SOUTHEAST — ENUGU ────────────────────────────────────────────────
    ("Holy Ghost College Enugu", "Enugu, Enugu", "https://holyghostcollege.edu.ng"),
    ("Presentation High School Enugu", "Enugu, Enugu",
     "https://presentationhighschool.edu.ng"),
    ("Hillcrest School Enugu", "Enugu, Enugu", "https://hillcrestenugu.edu.ng"),
    ("Madonna Girls College Enugu", "Enugu, Enugu", "https://madonnagirls.edu.ng"),
    ("Nigerian Turkish Nile College Enugu",
     "Enugu, Enugu", "https://nilecollege-enugu.edu.ng"),
    ("Prime Academy Enugu", "Enugu, Enugu", "https://primeacademyenugu.edu.ng"),
    ("Achievers Christian School Enugu", "Enugu, Enugu",
     "https://achieverschristiansch.edu.ng"),
    ("Greater Evangelism Schools Enugu", "Enugu, Enugu",
     "https://gevangelismschoolsenugu.edu.ng"),

    # ── SOUTHEAST — IMO ──────────────────────────────────────────────────
    ("St. Augustine's College Nkwerre", "Nkwerre, Imo",
     "https://staugustinenkwerre.edu.ng"),
    ("Assumpta Secondary School Owerri",
     "Owerri, Imo", "https://assumptasec.edu.ng"),
    ("Stella Maris College Owerri", "Owerri, Imo",
     "https://stellamarisowerri.edu.ng"),
    ("Nigerian Turkish Nile College Owerri",
     "Owerri, Imo", "https://nilecollege-owerri.edu.ng"),
    ("Greenland International School Owerri",
     "Owerri, Imo", "https://greenlandintl-owerri.edu.ng"),
    ("Goodhope Secondary School Owerri",
     "Owerri, Imo", "https://goodhopesec.edu.ng"),
    ("Deeper Life High School Owerri", "Owerri, Imo", "https://dls-owerri.edu.ng"),

    # ── SOUTHEAST — ABIA ─────────────────────────────────────────────────
    ("St. Michael's Secondary School Aba",
     "Aba, Abia", "https://stmichaelbaba.edu.ng"),
    ("Ngwa High School Aba", "Aba, Abia", "https://ngwahighschool.edu.ng"),
    ("Greater Evangelism Schools Aba", "Aba, Abia",
     "https://gevangelismschoolsaba.edu.ng"),
    ("Deeper Life High School Aba", "Aba, Abia", "https://dls-aba.edu.ng"),
    ("Nigerian Turkish Nile College Aba",
     "Aba, Abia", "https://nilecollege-aba.edu.ng"),

    # ── SOUTH-SOUTH — RIVERS ─────────────────────────────────────────────
    ("Stella Maris College Port Harcourt",
     "Port Harcourt, Rivers", "https://stellamarisph.edu.ng"),
    ("Nigerian Turkish Nile College Port Harcourt",
     "Port Harcourt, Rivers", "https://nilecollege-ph.edu.ng"),
    ("St. John Bosco's College Rumueme",
     "Port Harcourt, Rivers", "https://stjohnbosco-ph.edu.ng"),
    ("Hillcrest International School Port Harcourt",
     "Port Harcourt, Rivers", "https://hillcrestsph.edu.ng"),
    ("Rainbow International School Port Harcourt",
     "Port Harcourt, Rivers", "https://rainbowintlph.edu.ng"),
    ("Deeper Life High School Port Harcourt",
     "Port Harcourt, Rivers", "https://dls-ph.edu.ng"),
    ("Greater Evangelism Schools Port Harcourt",
     "Port Harcourt, Rivers", "https://gevangelismph.edu.ng"),
    ("Whitesand School Port Harcourt", "Port Harcourt, Rivers",
     "https://whitesandschool-ph.edu.ng"),
    ("Standard International School Port Harcourt",
     "Port Harcourt, Rivers", "https://standardintlph.edu.ng"),
    ("Graceland Academy Port Harcourt", "Port Harcourt, Rivers",
     "https://gracelandacademy-ph.edu.ng"),

    # ── SOUTH-SOUTH — DELTA ──────────────────────────────────────────────
    ("Nana College of Commerce Warri", "Warri, Delta", "https://nanacollege.edu.ng"),
    ("Nigerian Turkish Nile College Warri",
     "Warri, Delta", "https://nilecollege-warri.edu.ng"),
    ("St. Patrick's College Asaba", "Asaba, Delta", "https://stpatrickasaba.edu.ng"),
    ("Deeper Life High School Warri", "Warri, Delta", "https://dls-warri.edu.ng"),
    ("Hillcrest International School Warri",
     "Warri, Delta", "https://hillcrestwarri.edu.ng"),
    ("Christ the King College Asaba", "Asaba, Delta",
     "https://ctkcollege-asaba.edu.ng"),
    ("Holy Rosary College Ubiaja", "Ubiaja, Edo",
     "https://holyrosary-ubiaja.edu.ng"),

    # ── SOUTH-SOUTH — EDO ────────────────────────────────────────────────
    ("Immaculate Conception College Benin City",
     "Benin City, Edo", "https://iccbenin.edu.ng"),
    ("Emotan College Benin City", "Benin City, Edo", "https://emotancollege.edu.ng"),
    ("Nigerian Turkish Nile College Benin City",
     "Benin City, Edo", "https://nilecollege-benin.edu.ng"),
    ("Deeper Life High School Benin City",
     "Benin City, Edo", "https://dls-benin.edu.ng"),
    ("Hillcrest Secondary School Benin City",
     "Benin City, Edo", "https://hillcrestbenin.edu.ng"),
    ("Greater Evangelism Schools Benin", "Benin City, Edo",
     "https://gevangelismschools-benin.edu.ng"),

    # ── SOUTH-SOUTH — CROSS RIVER ────────────────────────────────────────
    ("Immaculate Conception College Calabar",
     "Calabar, Cross River", "https://icccalabar.edu.ng"),
    ("Mount Saint Gabriel's Secondary School",
     "Calabar, Cross River", "https://mountstgabriel.edu.ng"),
    ("Holy Family College Abak", "Abak, Akwa Ibom", "https://holyfamilyabak.edu.ng"),
    ("Nigerian Turkish Nile College Calabar",
     "Calabar, Cross River", "https://nilecollege-calabar.edu.ng"),
    ("Hillcrest Secondary School Calabar",
     "Calabar, Cross River", "https://hillcrestcalabar.edu.ng"),
    ("Deeper Life High School Calabar",
     "Calabar, Cross River", "https://dls-calabar.edu.ng"),

    # ── SOUTH-SOUTH — AKWA IBOM ──────────────────────────────────────────
    ("Ibom High School", "Uyo, Akwa Ibom", "https://ibomhighschool.edu.ng"),
    ("Nigerian Turkish Nile College Uyo",
     "Uyo, Akwa Ibom", "https://nilecollege-uyo.edu.ng"),
    ("Deeper Life High School Uyo", "Uyo, Akwa Ibom", "https://dls-uyo.edu.ng"),
    ("Greater Evangelism Schools Uyo", "Uyo, Akwa Ibom",
     "https://gevangelismschoolsuyo.edu.ng"),
    ("Hillcrest Secondary School Uyo",
     "Uyo, Akwa Ibom", "https://hillcrestuyo.edu.ng"),

    # ── NORTH CENTRAL — PLATEAU ──────────────────────────────────────────
    ("Hill Crest School Jos", "Jos, Plateau", "https://hillcrestjos.edu.ng"),
    ("Nigerian Turkish Nile College Jos",
     "Jos, Plateau", "https://nilecollege-jos.edu.ng"),
    ("Deeper Life High School Jos", "Jos, Plateau", "https://dls-jos.edu.ng"),
    ("Hillcrest Secondary School Jos", "Jos, Plateau",
     "https://hillcrestsecjos.edu.ng"),
    ("Rainbow International School Jos",
     "Jos, Plateau", "https://rainbowintljos.edu.ng"),

    # ── NORTH CENTRAL — KOGI / BENUE ─────────────────────────────────────
    ("Good Shepherd Secondary School Gboko",
     "Gboko, Benue", "https://goodshepherdgboko.edu.ng"),
    ("Deeper Life High School Makurdi",
     "Makurdi, Benue", "https://dls-makurdi.edu.ng"),
    ("St. Augustine's College Kabba", "Kabba, Kogi",
     "https://staugustineskabba.edu.ng"),
    ("Nigerian Turkish Nile College Lokoja",
     "Lokoja, Kogi", "https://nilecollege-lokoja.edu.ng"),

    # ── NORTH WEST — KADUNA / KANO ───────────────────────────────────────
    ("Nigerian Turkish International College Kaduna",
     "Kaduna, Kaduna", "https://ntic-kaduna.edu.ng"),
    ("Nigerian Turkish Nile College Kano",
     "Kano, Kano", "https://nilecollege-kano.edu.ng"),
    ("Deeper Life High School Kaduna", "Kaduna, Kaduna", "https://dls-kaduna.edu.ng"),
    ("Hillcrest Secondary Kano", "Kano, Kano", "https://hillcrestkano.edu.ng"),
    ("Rainbow International School Kano",
     "Kano, Kano", "https://rainbowintlkano.edu.ng"),
    ("Barewa College Zaria", "Zaria, Kaduna", "https://barewacollege.edu.ng"),
    ("Kano State School for the Gifted", "Kano, Kano",
     "https://kanoschoolofgifted.edu.ng"),

]

# Contact-page paths to try on each school website
_CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contacts",
    "/about",
    "/about-us",
    "/administration",
    "/principal",
    "/staff",
    "/school-info",
    "/ict",
    "/",
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def _fetch_page(client: httpx.AsyncClient, url: str) -> Optional[str]:
    try:
        resp = await client.get(url, timeout=15.0, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception as exc:
        logger.debug("Failed to fetch %s: %s", url, exc)
    return None


async def _extract_emails_from_school(client: httpx.AsyncClient, base_url: str) -> List[str]:
    """Try several contact/about paths on a school's domain and extract emails."""
    domain = urlparse(base_url).scheme + "://" + urlparse(base_url).netloc
    found_emails: List[str] = []

    for path in _CONTACT_PATHS:
        url = urljoin(domain, path)
        html = await _fetch_page(client, url)
        if not html:
            continue

        soup = BeautifulSoup(html, "lxml")
        # Remove script/style noise
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        emails = extract_school_emails(text)
        found_emails.extend(emails)

        if found_emails:
            break  # got emails from first successful page — stop

        await asyncio.sleep(random.uniform(0.3, 0.8))

    return list(dict.fromkeys(found_emails))  # deduplicate, preserve order


async def scrape_nigerian_schools() -> List[Dict[str, Any]]:
    """
    Scrape all known Nigerian schools, extract contact emails, and return
    synthetic job-listing dicts with title='Tech / AI Instructor'.
    """
    results: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True) as client:
        for name, location, website in NIGERIAN_SCHOOLS:
            try:
                emails = await _extract_emails_from_school(client, website)
            except Exception as exc:
                logger.warning("School '%s' scrape error: %s", name, exc)
                emails = []

            if not emails:
                # Still add a stub with no email — won't trigger outreach but
                # records it was visited so the UI shows coverage.
                logger.debug("No emails found for %s (%s)", name, website)
                continue

            # Use the school website as the unique URL
            results.append({
                "title": "Tech / AI Instructor",
                "company": name,
                "location": location,
                "url": website,
                "description": (
                    f"Outreach to {name} for a Tech / AI Instructor role. "
                    f"Location: {location}."
                ),
                "raw_emails": emails,
            })

            logger.info("School '%s' → %d email(s): %s",
                        name, len(emails), emails)
            await asyncio.sleep(random.uniform(1.0, 2.5))  # polite delay

    logger.info("School scraper complete — %d schools with emails", len(results))
    return results
