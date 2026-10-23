from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import uuid

from .domain.models import Member, Workout, TrainingPhase, Metric
from .application.services import TrainingPlanService
from .infrastructure.repository import SQLiteMemberRepository

app = FastAPI(title="Runners Sin Edad API")

# Dependency Injection
repo = SQLiteMemberRepository()
service = TrainingPlanService(repo)

# --- Pydantic Schemas for API ---

class MetricSchema(BaseModel):
    name: str
    value: float
    unit: str
    recorded_at: date

class WorkoutSchema(BaseModel):
    id: Optional[str] = None
    date: date
    description: str
    target_rpe: int
    actual_rpe: Optional[int] = None
    completed: bool = False
    notes: Optional[str] = None

class MemberSchema(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    birth_date: date
    current_phase: TrainingPhase
    metrics: List[MetricSchema] = []
    workouts: List[WorkoutSchema] = []

# --- Endpoints ---

@app.post("/members/", response_model=MemberSchema)
def create_member(member: MemberSchema):
    member_id = str(uuid.uuid4())[:8]
    new_member = Member(
        id=member_id,
        name=member.name,
        email=member.email,
        birth_date=member.birth_date,
        current_phase=member.current_phase,
        metrics=[Metric(**m.dict()) for m in member.metrics],
        workouts=[Workout(**w.dict()) for w in member.workouts]
    )
    repo.save(new_member)
    return new_member

@app.get("/members/{member_id}", response_model=MemberSchema)
def get_member(member_id: str):
    member = repo.find_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@app.post("/members/{member_id}/workouts/")
def add_workout(member_id: str, workout: WorkoutSchema):
    w_id = str(uuid.uuid4())[:8]
    new_workout = Workout(
        id=w_id,
        date=workout.date,
        description=workout.description,
        target_rpe=workout.target_rpe,
        actual_rpe=workout.actual_rpe,
        completed=workout.completed,
        notes=workout.notes
    )
    service.assign_workout(member_id, new_workout)
    return {"status": "Workout assigned", "workout_id": w_id}

@app.patch("/members/{member_id}/workouts/{workout_id}")
def complete_workout(member_id: str, workout_id: str, rpe: int, notes: str = None):
    service.complete_workout(member_id, workout_id, rpe, notes)
    return {"status": "Workout completed"}

@app.get("/members/", response_model=List[MemberSchema])
def list_members():
    return repo.list_all()
