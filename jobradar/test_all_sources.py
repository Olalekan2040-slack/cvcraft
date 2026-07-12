"""
Full test of all active NIGERIAN_SOURCES.
Tests fast sources (json_api + bs4) first, then Playwright sources.
"""
from app.services.scraper import scrape_source, NIGERIAN_SOURCES
from dotenv import load_dotenv
import asyncio
import sys
import time
sys.path.insert(0, ".")
load_dotenv()


async def main():
    grand_total = 0
    results = []

    # Split sources by type
    fast = [s for s in NIGERIAN_SOURCES if s["scraper_type"]
            in ("bs4", "json_api")]
    slow = [s for s in NIGERIAN_SOURCES if s["scraper_type"] == "playwright"]

    print("=" * 60)
    print("  FAST SOURCES (BS4 + JSON API)")
    print("=" * 60)
    tasks = [scrape_source(s) for s in fast]
    job_lists = await asyncio.gather(*tasks)
    for src, jobs in zip(fast, job_lists):
        n = len(jobs)
        grand_total += n
        results.append((src["name"], src["scraper_type"], n))
        status = "✓" if n > 0 else "✗"
        print(
            f"  {status} {src['name']:<22} [{src['scraper_type']:<8}] → {n} jobs")

    print()
    print("=" * 60)
    print("  PLAYWRIGHT SOURCES (sequential)")
    print("=" * 60)
    for src in slow:
        t0 = time.time()
        jobs = await scrape_source(src)
        n = len(jobs)
        grand_total += n
        elapsed = time.time() - t0
        results.append((src["name"], src["scraper_type"], n))
        status = "✓" if n > 0 else "✗"
        print(
            f"  {status} {src['name']:<22} [{src['scraper_type']:<8}] → {n} jobs  ({elapsed:.1f}s)")

    print()
    print("=" * 60)
    print(f"  TOTAL JOBS: {grand_total}")
    print("=" * 60)
    print("\nSummary:")
    for name, stype, n in sorted(results, key=lambda x: -x[2]):
        print(f"  {name:<25} {stype:<10} {n}")

asyncio.run(main())
