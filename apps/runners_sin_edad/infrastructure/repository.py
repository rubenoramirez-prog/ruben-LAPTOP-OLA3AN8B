import sqlite3
import json
from datetime import date
from typing import List, Optional
from ..domain.models import Member, Workout, TrainingPhase, Metric
from ..application.services import MemberRepository

class SQLiteMemberRepository(MemberRepository):
    """Adapter: SQLite implementation of the MemberRepository port."""

    def __init__(self, db_path: str = "runners_sin_edad.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    current_phase TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id TEXT PRIMARY KEY,
                    member_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target_rpe INTEGER NOT NULL,
                    actual_rpe INTEGER,
                    completed INTEGER DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (member_id) REFERENCES members(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (member_id) REFERENCES members(id)
                )
            """)
            conn.commit()

    def save(self, member: Member) -> None:
        with sqlite3.connect(self.db_path) as conn:
            # Save Member
            conn.execute(
                "INSERT OR REPLACE INTO members (id, name, email, birth_date, current_phase) VALUES (?, ?, ?, ?, ?)",
                (member.id, member.name, member.email, member.birth_date.isoformat(), member.current_phase.value)
            )

            # Save Workouts (Simplification: Clear and rewrite for this MVP)
            conn.execute("DELETE FROM workouts WHERE member_id = ?", (member.id,))
            for w in member.workouts:
                conn.execute(
                    "INSERT INTO workouts (id, member_id, date, description, target_rpe, actual_rpe, completed, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (w.id, member.id, w.date.isoformat(), w.description, w.target_rpe, w.actual_rpe, 1 if w.completed else 0, w.notes)
                )

            # Save Metrics
            conn.execute("DELETE FROM metrics WHERE member_id = ?", (member.id,))
            for m in member.metrics:
                conn.execute(
                    "INSERT INTO metrics (member_id, name, value, unit, recorded_at) VALUES (?, ?, ?, ?, ?)",
                    (member.id, m.name, m.value, m.unit, m.recorded_at.isoformat())
                )
            conn.commit()

    def find_by_id(self, member_id: str) -> Optional[Member]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
            if not row:
                return None

            member = Member(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                birth_date=date.fromisoformat(row["birth_date"]),
                current_phase=TrainingPhase(row["current_phase"])
            )

            # Load Workouts
            workout_rows = conn.execute("SELECT * FROM workouts WHERE member_id = ?", (member_id,)).fetchall()
            for wr in workout_rows:
                member.workouts.append(Workout(
                    id=wr["id"],
                    date=date.fromisoformat(wr["date"]),
                    description=wr["description"],
                    target_rpe=wr["target_rpe"],
                    actual_rpe=wr["actual_rpe"],
                    completed=bool(wr["completed"]),
                    notes=wr["notes"]
                ))

            # Load Metrics
            metric_rows = conn.execute("SELECT * FROM metrics WHERE member_id = ?", (member_id,)).fetchall()
            for mr in metric_rows:
                member.metrics.append(Metric(
                    name=mr["name"],
                    value=mr["value"],
                    unit=mr["unit"],
                    recorded_at=date.fromisoformat(mr["recorded_at"])
                ))

            return member

    def list_all(self) -> List[Member]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT id FROM members").fetchall()
            return [self.find_by_id(row["id"]) for row in rows]
