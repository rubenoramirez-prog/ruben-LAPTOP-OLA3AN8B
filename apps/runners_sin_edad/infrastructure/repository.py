import sqlite3
import json
from datetime import date
from typing import List, Optional
from apps.runners_sin_edad.domain.models import Member, Workout, TrainingPhase, Metric
from apps.runners_sin_edad.application.services import MemberRepository

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
                    current_phase TEXT NOT NULL,
                    start_date TEXT,
                    end_date TEXT,
                    paid INTEGER DEFAULT 1,
                    methodology_markdown TEXT
                )
            """)
            # Migration check for existing databases without start_date/end_date/paid/methodology_markdown
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(members)")
            columns = [col[1] for col in cursor.fetchall()]
            if "start_date" not in columns:
                conn.execute("ALTER TABLE members ADD COLUMN start_date TEXT")
            if "end_date" not in columns:
                conn.execute("ALTER TABLE members ADD COLUMN end_date TEXT")
            if "paid" not in columns:
                conn.execute("ALTER TABLE members ADD COLUMN paid INTEGER DEFAULT 1")
            if "methodology_markdown" not in columns:
                conn.execute("ALTER TABLE members ADD COLUMN methodology_markdown TEXT")

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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    receipt_ref TEXT,
                    FOREIGN KEY (member_id) REFERENCES members(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS coach_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            """)
            # Insert default coach if not exists (password: atumarca2026)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM coach_users WHERE username = 'coach'")
            if cursor.fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO coach_users (username, password_hash, role) VALUES (?, ?, ?)",
                    ("coach", "atumarca2026", "admin")
                )
                conn.execute(
                    "INSERT INTO coach_users (username, password_hash, role) VALUES (?, ?, ?)",
                    ("ruben", "atumarca2026", "admin")
                )
            conn.commit()

    def save(self, member: Member) -> None:
        with sqlite3.connect(self.db_path) as conn:
            s_date = member.start_date.isoformat() if member.start_date else None
            e_date = member.end_date.isoformat() if member.end_date else None

            # Save Member
            conn.execute(
                "INSERT OR REPLACE INTO members (id, name, email, birth_date, current_phase, start_date, end_date, paid, methodology_markdown) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (member.id, member.name, member.email, member.birth_date.isoformat(), member.current_phase.value, s_date, e_date, 1 if member.paid else 0, member.methodology_markdown)
            )

            # Save Workouts
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

            s_date = date.fromisoformat(row["start_date"]) if row["start_date"] else None
            e_date = date.fromisoformat(row["end_date"]) if row["end_date"] else None
            is_paid = bool(row["paid"]) if "paid" in row.keys() and row["paid"] is not None else True
            meth_md = row["methodology_markdown"] if "methodology_markdown" in row.keys() else None

            member = Member(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                birth_date=date.fromisoformat(row["birth_date"]),
                current_phase=TrainingPhase(row["current_phase"]),
                start_date=s_date,
                end_date=e_date,
                paid=is_paid,
                methodology_markdown=meth_md
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
            ids = [row["id"] for row in rows]
        members = [self.find_by_id(mid) for mid in ids]
        return [m for m in members if m is not None]

    def delete(self, member_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM workouts WHERE member_id = ?", (member_id,))
            conn.execute("DELETE FROM metrics WHERE member_id = ?", (member_id,))
            cursor = conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
            conn.commit()
            return cursor.rowcount > 0
