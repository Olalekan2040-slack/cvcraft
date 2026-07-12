import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends

from app.models.user import User
from app.services.scheduler import run_scrape_cycle
from app.utils.auth import get_current_user

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("/run", status_code=202)
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_user),
):
    """Trigger an immediate scrape run without waiting for the schedule."""
    background_tasks.add_task(run_scrape_cycle)
    return {"detail": "Scrape run started in background"}
