"""
Quick scraper test — run with:  python test_scraper.py
Tests all BS4/JSON sources first (fast), then one Playwright source.
"""
from app.services.scraper import scrape_source, NIGERIAN_SOURCES
from dotenv import load_dotenv
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()


async def main():
    fast_sources = [
        s for s in NIGERIAN_SOURCES if s["scraper_type"] in ("json_api", "bs4")]
    pw_sources = [
        s for s in NIGERIAN_SOURCES if s["scraper_type"] == "playwright"]

    print("\n══ BS4 / JSON API Sources ══════════════════════════════════════")
    total_fast = 0
    for src in fast_sources:
        try:
            jobs = await scrape_source(src)
            total_fast += len(jobs)
            status = f"{len(jobs)} jobs"
            if jobs:
                status += f"  |  sample: {jobs[0]['title'][:60]}"
            print(f"  {'✓' if jobs else '○'}  {src['name']:<25} {status}")
        except Exception as exc:
            print(f"  ✗  {src['name']:<25} ERROR: {exc}")

    print(f"\n  Total fast-source jobs: {total_fast}")

    print("\n══ Playwright Sources (testing first one only) ══════════════════")
    # Only test the first Playwright source to keep the test quick
    src = pw_sources[0]
    try:
        jobs = await scrape_source(src)
        status = f"{len(jobs)} jobs"
        if jobs:
            status += f"  |  sample: {jobs[0]['title'][:60]}"
        print(f"  {'✓' if jobs else '○'}  {src['name']:<25} {status}")
    except Exception as exc:
        print(f"  ✗  {src['name']:<25} ERROR: {exc}")

    print(f"\n  Playwright sources (remaining, not tested here):")
    for s in pw_sources[1:]:
        print(f"     - {s['name']}")

    print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())
