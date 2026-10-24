from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
import uuid
import os

# Add the skills directory to sys.path to import the humanizer logic
# Using a relative path based on the project structure
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HUMAN_SKILL_PATH = os.path.join(BASE_DIR, "..", "instagram-agent-skill", "skills", "ig-human")
if HUMAN_SKILL_PATH not in sys.path:
    sys.path.append(HUMAN_SKILL_PATH)

try:
    from humanize import humanize as run_humanize
    from detect import run as run_detect
except ImportError as e:
    print(f"Error importing humanizer tools: {e}")

from .domain.models import Member, Workout, TrainingPhase, Metric
from .application.services import TrainingPlanService
from .infrastructure.repository import SQLiteMemberRepository

app = FastAPI(title="Runners Sin Edad API")

# Dependency Injection
repo = SQLiteMemberRepository()
service = TrainingPlanService(repo)

# --- Pydantic Schemas ---

class HumanizeRequest(BaseModel):
    text: str

class HumanizeResponse(BaseModel):
    original_text: str
    cleaned_text: str
    report: Dict[str, Any]
    detection: Dict[str, Any]

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

# --- Humanizer Endpoints ---

@app.post("/humanize/", response_model=HumanizeResponse)
def api_humanize(request: HumanizeRequest):
    """
    Takes a text draft, runs it through the humanize.py pipeline,
    and returns the cleaned text along with the detection score.
    """
    try:
        # 1. Load Lexicon
        lex_path = os.path.join(HUMAN_SKILL_PATH, "slop.json")
        import json
        with open(lex_path, encoding="utf-8") as f:
            lexicon = json.load(f)

        # 2. Run Humanization
        clean_text, report = run_humanize(request.text, lexicon)

        # 3. Run Detection on the cleaned text
        detect_results, overall_score, verdict = run_detect(clean_text, lexicon)

        return {
            "original_text": request.text,
            "cleaned_text": clean_text,
            "report": report,
            "detection": {
                "score": overall_score,
                "verdict": verdict,
                "details": detect_results
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Humanizer error: {str(e)}")

# --- Member Endpoints ---

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
