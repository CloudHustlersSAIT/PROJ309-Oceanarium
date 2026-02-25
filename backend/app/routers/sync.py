from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..jobs.sync_scheduler import get_sync_service
from ..models.sync_log import SyncLog

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/trigger")
def trigger_sync(db: Session = Depends(get_db)):
    service = get_sync_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Sync service not initialised")

    sync_log = service.run_sync(db)
    return {
        "status": sync_log.status,
        "new_count": sync_log.new_count,
        "changed_count": sync_log.changed_count,
        "cancelled_count": sync_log.cancelled_count,
        "errors": sync_log.errors,
    }


@router.get("/logs")
def list_sync_logs(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    logs = (
        db.query(SyncLog)
        .order_by(SyncLog.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "finished_at": log.finished_at.isoformat() if log.finished_at else None,
            "new_count": log.new_count,
            "changed_count": log.changed_count,
            "cancelled_count": log.cancelled_count,
            "status": log.status,
            "errors": log.errors,
        }
        for log in logs
    ]
