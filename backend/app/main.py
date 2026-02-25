from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.clorian_mock import ClorianMockClient
from .jobs.sync_scheduler import init_sync_service, run_sync_job
from .routers import (
    assignments,
    bookings,
    guides,
    health,
    issues,
    notifications,
    stats,
    sync,
    tours,
)

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_sync_service(ClorianMockClient())
    scheduler.add_job(run_sync_job, "interval", minutes=15, id="clorian_sync")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="Oceanarium Tour Scheduling API", lifespan=lifespan)

    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(guides.router)
    app.include_router(tours.router)
    app.include_router(assignments.router)
    app.include_router(bookings.router)
    app.include_router(issues.router)
    app.include_router(stats.router)
    app.include_router(notifications.router)
    app.include_router(sync.router)

    return app


app = create_app()
