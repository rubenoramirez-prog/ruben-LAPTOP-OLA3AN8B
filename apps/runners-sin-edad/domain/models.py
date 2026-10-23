from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from enum import Enum

class TrainingPhase(Enum):
    BASE = "Base"
    STRENGTH = "Fuerza"
    SPEED = "Velocidad"
    TAPER = "Taper"

@dataclass(frozen=True)
class Metric:
    """Value object for physiological markers."""
    name: str  # e.g., "VO2max", "Cooper Test"
    value: float
    unit: str
    recorded_at: date

@dataclass
class Workout:
    """Entity representing a single training session."""
    id: str
    date: date
    description: str
    target_rpe: int  # Rate of Perceived Exertion (1-10)
    actual_rpe: Optional[int] = None
    completed: bool = False
    notes: Optional[str] = None

@dataclass
class Member:
    """Entity representing a coach's client (Adult 35+)."""
    id: str
    name: str
    email: str
    birth_date: date
    current_phase: TrainingPhase
    metrics: List[Metric] = field(default_factory=list)
    workouts: List[Workout] = field(default_factory=list)

    def update_phase(self, new_phase: TrainingPhase):
        self.current_phase = new_phase

    def add_metric(self, metric: Metric):
        self.metrics.append(metric)
