from abc import ABC, abstractmethod
from typing import List, Optional
from apps.runners_sin_edad.domain.models import Member, Workout, TrainingPhase, Metric

class MemberRepository(ABC):
    """Port: Interface for member data persistence."""

    @abstractmethod
    def save(self, member: Member) -> None:
        pass

    @abstractmethod
    def find_by_id(self, member_id: str) -> Optional[Member]:
        pass

    @abstractmethod
    def list_all(self) -> List[Member]:
        pass

class TrainingPlanService:
    """Application Service: Orchestrates business logic for training."""

    def __init__(self, repo: MemberRepository):
        self.repo = repo

    def assign_workout(self, member_id: str, workout: Workout) -> None:
        member = self.repo.find_by_id(member_id)
        if not member:
            raise ValueError(f"Member {member_id} not found")

        member.workouts.append(workout)
        self.repo.save(member)

    def complete_workout(self, member_id: str, workout_id: str, rpe: int, notes: str = None) -> None:
        member = self.repo.find_by_id(member_id)
        if not member:
            raise ValueError(f"Member {member_id} not found")

        for w in member.workouts:
            if w.id == workout_id:
                w.completed = True
                w.actual_rpe = rpe
                w.notes = notes
                break

        self.repo.save(member)
