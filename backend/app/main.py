import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

from .jobs.sync_scheduler import init_sync_service, run_sync_job
from .routers import (
    assignments,
    bookings,
    costs,
    customers,
    guides,
    health,
    issues,
    notifications,
    resources,
    schedules,
    stats,
    surveys,
    sync,
    tours,
    users,
)


def _create_clorian_client():
    env = os.getenv("APP_ENV", "development")
    if env == "production":
        from .adapters.clorian_client import ClorianClientBase

        raise NotImplementedError(
            "Production Clorian client not yet implemented. "
            "Set APP_ENV=development to use the mock client."
        )
    from .adapters.clorian_mock import ClorianMockClient

    return ClorianMockClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    client = _create_clorian_client()
    init_sync_service(client)
    scheduler.add_job(run_sync_job, "interval", minutes=15, id="clorian_sync")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="Oceanarium Tour Scheduling API", lifespan=lifespan)

    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(guides.router)
    app.include_router(tours.router)
    app.include_router(assignments.router)
    app.include_router(bookings.router)
    app.include_router(costs.router)
    app.include_router(customers.router)
    app.include_router(resources.router)
    app.include_router(schedules.router)
    app.include_router(surveys.router)
    app.include_router(users.router)
    app.include_router(issues.router)
    app.include_router(stats.router)
    app.include_router(notifications.router)
    app.include_router(sync.router)

    return app


app = create_app()
