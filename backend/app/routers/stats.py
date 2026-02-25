from fastapi import APIRouter

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("")
def read_stats():
    return {
        "toursToday": 14,
        "customersToday": 45,
        "cancellations": 2,
        "avgRating": "4.9",
    }
