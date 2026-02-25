from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def read_notifications():
    mock_notifications = [
        {
            "id": 1,
            "message": "Guide Ana Costa swapped tour Dolphin Feeding",
            "timestamp": "2025-02-06T14:30:00",
        },
        {
            "id": 2,
            "message": "New booking for Shark Diving received",
            "timestamp": "2025-02-06T13:15:00",
        },
        {
            "id": 3,
            "message": "Guide Liam Brown is unavailable Feb 9",
            "timestamp": "2025-02-06T10:00:00",
        },
    ]
    return mock_notifications
