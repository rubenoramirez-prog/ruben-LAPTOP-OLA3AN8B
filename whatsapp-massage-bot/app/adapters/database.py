import sqlite3
import os
from typing import List, Optional
from app.domain.models import MassageService, Appointment, ChatSession

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "clinic.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            duration_mins INTEGER NOT NULL,
            price_mxn REAL NOT NULL,
            description TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            client_name TEXT NOT NULL,
            service_id TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            reminder_sent INTEGER DEFAULT 0,
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    """)

    # Robust check for reminder_sent column in existing table
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [col[1] for col in cursor.fetchall()]
    if "reminder_sent" not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN reminder_sent INTEGER DEFAULT 0")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            phone_number TEXT PRIMARY KEY,
            current_state TEXT NOT NULL,
            selected_service TEXT,
            selected_datetime TEXT,
            client_name TEXT
        )
    """)

    # Seed default massage services if empty
    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        default_services = [
            ("s1", "Masaje Relajante / Sueco", 60, 650.0, "Masaje suave con aceites esenciales para liberar tensión acumulada."),
            ("s2", "Masaje Descontracturante", 60, 800.0, "Presión media-alta enfocada en nudos musculares y espalda."),
            ("s3", "Piedras Calientes (Basálticas)", 90, 1100.0, "Termoterapia profunda para relajación muscular total."),
            ("s4", "Reflexología Podal & Holística", 45, 500.0, "Estimulación de puntos reflejos en pies para equilibrar energía.")
        ]
        cursor.executemany("INSERT INTO services VALUES (?, ?, ?, ?, ?)", default_services)

    conn.commit()
    conn.close()

def get_all_services() -> List[MassageService]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services")
    rows = cursor.fetchall()
    conn.close()
    return [MassageService(**dict(row)) for row in rows]

def get_service(service_id: str) -> Optional[MassageService]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
    row = cursor.fetchone()
    conn.close()
    return MassageService(**dict(row)) if row else None

def save_appointment(app: Appointment) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO appointments (phone_number, client_name, service_id, appointment_time, status, created_at, reminder_sent)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (app.phone_number, app.client_name, app.service_id, app.appointment_time, app.status, app.created_at))
    conn.commit()
    app_id = cursor.lastrowid
    conn.close()
    return app_id

def get_session(phone_number: str) -> ChatSession:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE phone_number = ?", (phone_number,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return ChatSession(**dict(row))
    else:
        return ChatSession(phone_number=phone_number)

def save_session(session: ChatSession):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (phone_number, current_state, selected_service, selected_datetime, client_name)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(phone_number) DO UPDATE SET
            current_state = excluded.current_state,
            selected_service = excluded.selected_service,
            selected_datetime = excluded.selected_datetime,
            client_name = excluded.client_name
    """, (session.phone_number, session.current_state, session.selected_service, session.selected_datetime, session.client_name))
    conn.commit()
    conn.close()
