from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class MassageService:
    id: str
    name: str
    duration_mins: int
    price_mxn: float
    description: str

@dataclass
class Appointment:
    id: Optional[int]
    phone_number: str
    client_name: str
    service_id: str
    appointment_time: str
    status: str = "CONFIRMED"  # CONFIRMED, CANCELLED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ChatSession:
    phone_number: str
    current_state: str = "MENU"  # MENU, AWAITING_SERVICE, AWAITING_DATE, AWAITING_NAME, CONFIRMED
    selected_service: Optional[str] = None
    selected_datetime: Optional[str] = None
    client_name: Optional[str] = None
