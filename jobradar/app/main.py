import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import auth, emails, jobs, scrape, sources, templates
from app.routers import dashboard
from app.routers import school_outreach
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# Optional Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("JobRadar starting up — N-TECH Info Systems Ltd")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("JobRadar shut down cleanly")


limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="JobRadar",
    description="Automated Job Scraping & Email Outreach Platform — Nigeria Edition",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(jobs.router)
app.include_router(templates.router)
app.include_router(emails.router)
app.include_router(scrape.router)
app.include_router(dashboard.router)
app.include_router(school_outreach.router)

# Static files (frontend)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/ui", include_in_schema=False)
def serve_ui():
    return FileResponse("app/static/index.html")


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/ui")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "JobRadar", "org": "N-TECH Info Systems Ltd"}
