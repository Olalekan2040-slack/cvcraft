"""
send_schools_now.py
===================
Immediately sends the Tech / AI Instructor cover letter to the 16 Nigerian
private schools listed below.  Run once:

    python send_schools_now.py
"""
from app.services.email_service import send_manual_school_email
from app.database import SessionLocal
from dotenv import load_dotenv
import asyncio
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env before importing app modules
load_dotenv()


SCHOOLS = [
    # ── Osogbo / Osun ──────────────────────────────────────────────────────
    {"email": "info@daystarsprivateschools.org",
        "school_name": "Day Stars Private Schools",                 "location": "Osogbo, Osun"},
    {"email": "exceedinggraceacad@gmail.com",
        "school_name": "Exceeding Grace Academy",                   "location": "Osogbo, Osun"},
    {"email": "info@al-medinahinternationalcollege.com",
        "school_name": "Al-Medinah International College",          "location": "Osogbo, Osun"},
    {"email": "ebunoluwaintsch@gmail.com",
        "school_name": "Ebunoluwa International School",            "location": "Osogbo, Osun"},
    {"email": "goodtidingsedu@gmail.com",
        "school_name": "Good Tidings Schools",                      "location": "Osogbo, Osun"},
    {"email": "info@destinyinternationalcollege.org",
        "school_name": "Destiny International College",             "location": "Osogbo, Osun"},
    {"email": "info@kunike.sch.ng",
        "school_name": "Kunike International School",               "location": "Osogbo, Osun"},
    {"email": "admin@ahsosogboportal.com",
        "school_name": "Adventist High School",                     "location": "Osogbo, Osun"},
    {"email": "info@lbis.org",                            "school_name":
        "LBIS Osogbo Campus",                        "location": "Osogbo, Osun"},
    # ── Akure / Ondo ───────────────────────────────────────────────────────
    {"email": "office@preston-international.com",
        "school_name": "Preston International School",              "location": "Akure, Ondo"},
    {"email": "info@modelsecondaryschool.com",
        "school_name": "Model Secondary School",                    "location": "Akure, Ondo"},
    {"email": "info@waterspringsschool.com.ng",
        "school_name": "Watersprings International School",         "location": "Akure, Ondo"},
    {"email": "info@myseabacollege.org",
        "school_name": "Seaba Model Christian College",             "location": "Akure, Ondo"},
    {"email": "info@impactschools.org.ng",
        "school_name": "Impact High School Akure",                  "location": "Akure, Ondo"},
    {"email": "crissakure@gmail.com",
        "school_name": "Christ the Redeemer's Int'l Secondary School", "location": "Akure, Ondo"},
    {"email": "info.homajhighschool@gmail.com",
        "school_name": "Homaj High School",                         "location": "Akure, Ondo"},
]

DELAY_SECONDS = 5  # polite delay between sends


async def main():
    db = SessionLocal()
    total_sent = 0
    total_skipped = 0
    total_failed = 0

    print(f"\n{'='*60}")
    print(f"  JobRadar — School Outreach (Tech / AI Instructor)")
    print(f"  Sending to {len(SCHOOLS)} schools")
    print(f"{'='*60}\n")

    try:
        for school in SCHOOLS:
            name = school["school_name"]
            email = school["email"]
            print(f"→ {name}")
            print(f"  {email}  ({school['location']})")
            try:
                result = await send_manual_school_email(db=db, **school)
            except BaseException as raw_exc:
                result = {"email": email, "status": "failed",
                          "reason": str(raw_exc) or type(raw_exc).__name__}
            status = result["status"]
            note = result.get("reason", "")
            symbol = "✅" if status == "sent" else (
                "⏭" if status == "skipped" else "❌")
            print(f"  {symbol} {status.upper()}{(': ' + note) if note else ''}\n")

            if status == "sent":
                total_sent += 1
                await asyncio.sleep(DELAY_SECONDS)
            elif status == "skipped":
                total_skipped += 1
            else:
                total_failed += 1

    finally:
        db.close()

    print(f"{'='*60}")
    print(
        f"  Results: {total_sent} sent | {total_skipped} skipped | {total_failed} failed")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
