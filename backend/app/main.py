import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

# for poller_listener
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine
from app.services.poller_listener import process_staging_rows

from .firebase_auth import initialize_firebase
from .routes.auth import router as auth_router
from .routes.customer import router as customer_router
from .routes.guide import router as guide_router
from .routes.health import router as health_router
from .routes.issue import router as issue_router
from .routes.mock import router as mock_router
from .routes.notification import router as notification_router
from .routes.reservation import router as reservation_router
from .routes.schedule import router as schedule_router
from .routes.stats import router as stats_router
from .routes.tour import router as tour_router

logger = logging.getLogger(__name__)

# Default to production to ensure the safest behavior when ENV is not explicitly set.
ENV = os.getenv("ENV", "production").lower()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    if ENV != "development":
        initialize_firebase()
    else:
        try:
            initialize_firebase()
        except Exception as exc:
            # Allow startup to succeed in development even if Firebase initialization
            # fails (e.g. missing credentials), but log so misconfiguration is visible.
            logger.warning("Firebase initialization failed in development mode: %s", exc)
    yield


app = FastAPI(title="My Project API", lifespan=lifespan)


app.include_router(health_router)
app.include_router(customer_router)
app.include_router(reservation_router)
app.include_router(guide_router)
app.include_router(tour_router)
app.include_router(schedule_router)
app.include_router(notification_router)
app.include_router(issue_router)
app.include_router(stats_router)
app.include_router(mock_router)
app.include_router(auth_router)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://cpsy301-small-prototype.vercel.app",
    "https://oceanarium.duckdns.org",
    "https://main.d29u7miusl8fw9.amplifyapp.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up background scheduler for poller listener
scheduler = BackgroundScheduler()


def run_listener():

    with engine.begin() as conn:
        processed = process_staging_rows(conn)

        if processed > 0:
            print(f"Processed {processed} staging rows")


scheduler.add_job(run_listener, "interval", seconds=5)

scheduler.start()
