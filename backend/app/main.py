from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.guide import router as guide_router
from .routes.health import router as health_router
from .routes.issue import router as issue_router
from .routes.mock import router as mock_router
from .routes.notification import router as notification_router
from .routes.reservation import router as reservation_router
from .routes.stats import router as stats_router
from .routes.tour import router as tour_router

app = FastAPI(title="My Project API")

app.include_router(health_router)
app.include_router(reservation_router)
app.include_router(guide_router)
app.include_router(tour_router)
app.include_router(notification_router)
app.include_router(issue_router)
app.include_router(stats_router)
app.include_router(mock_router)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://cpsy301-small-prototype.vercel.app",
    "https://oceanarium.duckdns.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
