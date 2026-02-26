import random
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from .clorian_client import ClorianBooking, ClorianClientBase

TOUR_NAMES = [
    "Behind the Scenes",
    "Night at the Oceanarium",
    "Coral Explorer",
    "Shark Dive",
    "Penguin Encounter",
    "Whale Watching",
    "Tropical Reef Walk",
    "Deep Sea Discovery",
]

FIRST_NAMES = [
    "Emma", "Liam", "Sofia", "Noah", "Olivia",
    "Lucas", "Mia", "Ethan", "Isabella", "James",
    "Ana", "Miguel", "Maria", "Pedro", "Joana",
]

LAST_NAMES = [
    "Silva", "Santos", "Ferreira", "Oliveira", "Costa",
    "Rodrigues", "Martins", "Pereira", "Almeida", "Sousa",
    "Johnson", "Williams", "Brown", "Taylor", "Anderson",
]

EXPERTISE_MAP = {
    "Behind the Scenes": ("Facility Operations", "Operations"),
    "Night at the Oceanarium": ("Nocturnal Species", "Marine Biology"),
    "Coral Explorer": ("Coral Reef", "Marine Ecology"),
    "Shark Dive": ("Sharks", "Marine Biology"),
    "Penguin Encounter": ("Penguins", "Zoology"),
    "Whale Watching": ("Whales", "Marine Biology"),
    "Tropical Reef Walk": ("Tropical Fish", "Marine Ecology"),
    "Deep Sea Discovery": ("Deep Sea", "Oceanography"),
}

LANGUAGES = ["en", "pt", "es", "fr"]


def generate_mock_bookings(
    seed: int = 42,
    count: int = 10,
    base_date: Optional[date] = None,
) -> List[ClorianBooking]:
    rng = random.Random(seed)
    if base_date is None:
        base_date = date.today() + timedelta(days=1)

    bookings: List[ClorianBooking] = []
    for i in range(count):
        tour = rng.choice(TOUR_NAMES)
        expertise, category = EXPERTISE_MAP[tour]

        days_offset = rng.randint(0, 14)
        booking_date = base_date + timedelta(days=days_offset)

        start_hour = rng.choice([9, 10, 11, 14, 15, 16])
        duration_hours = rng.choice([1, 2])
        start = time(start_hour, 0)
        end = time(start_hour + duration_hours, 0)

        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)

        bookings.append(
            ClorianBooking(
                clorian_booking_id=f"CLR-{rng.randint(1000, 9999):04d}",
                date=booking_date,
                start_time=start,
                end_time=end,
                required_expertise=expertise,
                required_category=category,
                requested_language_code=rng.choice(LANGUAGES),
                adult_tickets=rng.randint(1, 6),
                child_tickets=rng.randint(0, 4),
                customer_name=f"{first} {last}",
                customer_email=f"{first.lower()}.{last.lower()}@example.com",
                tour_name=tour,
            )
        )

    return bookings


class ClorianMockClient(ClorianClientBase):
    """Mock Clorian client for development and testing.

    Generates realistic bookings using a deterministic seed,
    or allows manual manipulation via add/remove/update/clear.
    """

    def __init__(self, seed: int = 42, count: int = 10) -> None:
        self._bookings: List[ClorianBooking] = generate_mock_bookings(
            seed=seed, count=count
        )

    def fetch_bookings(self, since: Optional[datetime] = None) -> List[ClorianBooking]:
        return list(self._bookings)

    def add_booking(self, booking: ClorianBooking) -> None:
        self._bookings.append(booking)

    def remove_booking(self, clorian_booking_id: str) -> None:
        self._bookings = [
            b for b in self._bookings if b.clorian_booking_id != clorian_booking_id
        ]

    def update_booking(self, clorian_booking_id: str, **kwargs) -> None:
        for b in self._bookings:
            if b.clorian_booking_id == clorian_booking_id:
                for key, value in kwargs.items():
                    setattr(b, key, value)
                break

    def clear(self) -> None:
        self._bookings.clear()
