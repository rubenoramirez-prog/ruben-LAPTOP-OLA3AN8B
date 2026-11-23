from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Added for CORS
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - compatibility with Pydantic v1
    ConfigDict = None
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
import uuid
import os
import json

# Add the skills directory to sys.path to import the humanizer logic
import sys
# Use an absolute path relative to the project root to avoid path resolution issues
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HUMAN_SKILL_PATH = os.path.join(PROJECT_ROOT, "instagram-agent-skill", "skills", "ig-human")
if HUMAN_SKILL_PATH not in sys.path:
    sys.path.insert(0, HUMAN_SKILL_PATH)

try:
    from humanize import humanize as run_humanize
    from detect import run as run_detect
except ImportError as e:
    print(f"Error importing humanizer tools: {e}")

from .domain.models import Member, Workout, TrainingPhase, Metric
from .application.services import TrainingPlanService
from .infrastructure.repository import SQLiteMemberRepository

app = FastAPI(title="Runners Sin Edad API")

# --- CORS CONFIGURATION ---
# This allows the dashboard.html file to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for MVP
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, PATCH, etc.)
    allow_headers=["*"], # Allow all headers
)

# Dependency Injection
repo = SQLiteMemberRepository()
service = TrainingPlanService(repo)

def align_member_plan_to_monday(member: Member):
    if not member.start_date:
        member.start_date = date(2026, 11, 16) # Monday Nov 16, 2026
    elif member.start_date.weekday() != 0:
        member.start_date = member.start_date - timedelta(days=member.start_date.weekday())

    member.end_date = member.start_date + timedelta(days=84)

    day_map = {"lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2, "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6}
    for idx, w in enumerate(member.workouts):
        w_id = w.id.lower()
        week_num = 1
        if "s" in w_id:
            try:
                parts = w_id.split("-")
                for p in parts:
                    if p.startswith("s") and p[1:].isdigit():
                        week_num = int(p[1:])
            except:
                pass

        day_idx = idx % 7
        for dname, didx in day_map.items():
            if dname in w_id or dname in w.description.lower():
                day_idx = didx
                break

        w.date = member.start_date + timedelta(weeks=(week_num - 1), days=day_idx)
    repo.save(member)

@app.on_event("startup")
def startup_event():
    renata_meth = """## 4. Fuerza y movilidad

Realiza estas rutinas en casa con tu propio peso corporal al terminar tus sesiones de lunes y miércoles (descansa 45-60 segundos entre series).

**Rutina 1: Piernas y estabilidad (Blindaje articular)**

* **Sentadilla libre:** 3 series de 12 repeticiones (baja controlando el movimiento, sin que las rodillas se metan hacia adentro).
* **Desplantes hacia atrás alternados:** 3 series de 8 repeticiones por pierna (pasos cortos y estables).
* **Elevación de talones (pantorrillas):** 3 series de 15 repeticiones (sube en 1 segundo, baja lento en 3 segundos).
* **Movilidad de tobillo y cadera:** 2 minutos de círculos suaves con tobillos y balanceos controlados de pierna.

**Rutina 2: Core y postura**

* **Puente de glúteo en el piso:** 3 series de 15 repeticiones (aprieta glúteos arriba por 2 segundos).
* **Plancha frontal sobre antebrazos:** 3 series de 25 a 35 segundos (mantén el abdomen firme y la espalda recta).
* **Bird-Dog (perro de caza en cuatro puntos):** 3 series de 8 repeticiones por lado (estira brazo derecho y pierna izquierda manteniendo el equilibrio).
* **Estiramiento suave de espalda y flexores:** 2 minutos en postura del niño y estiramiento de zancada baja.

## 5. Hidratación, sueño y alimentación general

* Toma agua natural de forma constante durante todo el día, no esperes a tener sed antes de salir a entrenar por la tarde.
* Procura dormir entre 8 y 9 horas cada noche; a tus 16 años el descanso nocturno es fundamental para que tus músculos y huesos se fortalezcan.
* Haz una comida ligera rica en carbohidratos fáciles de digerir (como una fruta o un pan tostado) entre 60 y 90 minutos antes de tu sesión vespertina.
* Evita comidas muy grasosas, picantes o pesadas justo antes de correr para prevenir molestias estomacales.
* Incluye alimentos naturales y variados en tus comidas principales (frutas, verduras, cereales integrales y fuentes de proteína) para recuperar energía después de entrenar.

## 6. Señales de alto: cuándo parar y consultar

Detén de inmediato tu entrenamiento y avisa a tus papás o acude a valoración médica si presentas cualquiera de estas señales:

* Dolor agudo o punzante en rodillas, tobillos, espinillas o cadera.
* Mareos, sensación de desmayo o visión nublada durante o después del esfuerzo.
* Dolor, opresión o pinchazos en el pecho.
* Falta de aire anormal que no mejora al bajar el ritmo o empezar a caminar.
* Cualquier molestia muscular o articular que te haga cojear o que persista por más de 48 horas.

## 7. Día de carrera o prueba final

El jueves de la Semana 12 realizarás tu prueba de 5K en un tramo plano y seguro de tu recorrido habitual. Haz tu calentamiento completo de 8 minutos caminando a paso vivo y moviendo tus articulaciones; no salgas corriendo de golpe. Tu estrategia será empezar más lento de lo que crees necesario durante los primeros 10 minutos para controlar tu respiración; a la mitad del recorrido mantén un paso constante donde puedas hablar con frases cortas, y si en los últimos minutos te sientes fuerte, acelera un poco de forma gradual. Evita estrenar tenis o calcetines ese día y no te compares con el ritmo de nadie más.

## 8. Tu siguiente paso

Al terminar estas 12 semanas y completar tus 5K, tómate de 4 a 5 días de descanso activo (caminatas suaves y estiramientos) para celebrar tu logro y permitir que tu cuerpo asimile el trabajo. Después evaluaremos cómo te sentiste en la prueba final para decidir si iniciamos un bloque enfocado en mejorar tu velocidad en los 5K o si comenzamos a construir distancia poco a poco hacia tu primer 10K."""

    member = repo.find_by_id("runner-demo")
    if not member:
        demo_member = Member(
            id="runner-demo",
            name="Renata Ramirez",
            email="renata@runnersinsedad.com",
            birth_date=date(2010, 5, 12),
            current_phase=TrainingPhase.BASE,
            start_date=date(2026, 11, 16),
            end_date=date(2026, 11, 16) + timedelta(days=84),
            methodology_markdown=renata_meth,
            metrics=[Metric(name="VO2max", value=42.4, unit="ml/kg/min", recorded_at=date.today())],
            workouts=[]
        )
        repo.save(demo_member)
    else:
        if not member.methodology_markdown:
            member.methodology_markdown = renata_meth
            repo.save(member)

    for m in repo.list_all():
        align_member_plan_to_monday(m)
        if not m.methodology_markdown:
            m.methodology_markdown = renata_meth
            repo.save(m)

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
    target_rpe: int = Field(..., ge=1, le=10)
    actual_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    completed: bool = False
    notes: Optional[str] = None

class CompleteWorkoutRequest(BaseModel):
    rpe: int = Field(..., ge=1, le=10)
    notes: Optional[str] = None

class UpdatePaymentRequest(BaseModel):
    paid: bool

class BulkWorkoutsSchema(BaseModel):
    workouts: List[WorkoutSchema]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    methodology_markdown: Optional[str] = None

class PlanGenerateRequest(BaseModel):
    prompt: str
    name: Optional[str] = "Renata Ramirez"
    meta: Optional[str] = "5K"
    level: Optional[str] = "NIVEL 1"

class MemberSchema(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    birth_date: date
    current_phase: TrainingPhase
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    paid: bool = True
    methodology_markdown: Optional[str] = None
    metrics: List[MetricSchema] = Field(default_factory=list)
    workouts: List[WorkoutSchema] = Field(default_factory=list)

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class LoginRequest(BaseModel):
    username: str
    password: str

class WebhookPaymentRequest(BaseModel):
    member_id: str
    amount: float
    receipt_ref: Optional[str] = None

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Runners Sin Edad API is online", "docs": "/docs"}

@app.post("/humanize/", response_model=HumanizeResponse)
def api_humanize(request: HumanizeRequest):
    try:
        lex_path = os.path.join(HUMAN_SKILL_PATH, "slop.json")
        with open(lex_path, encoding="utf-8") as f:
            lexicon = json.load(f)

        clean_text, report = run_humanize(request.text, lexicon)
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

@app.post("/members/", response_model=MemberSchema)
def create_member(member: MemberSchema):
    member_id = member.id if member.id else str(uuid.uuid4())[:8]
    _dump = lambda item: item.model_dump() if hasattr(item, "model_dump") else item.dict()
    new_member = Member(
        id=member_id,
        name=member.name,
        email=member.email,
        birth_date=member.birth_date,
        current_phase=member.current_phase,
        start_date=member.start_date,
        end_date=member.end_date,
        paid=member.paid,
        methodology_markdown=member.methodology_markdown,
        metrics=[Metric(**_dump(m)) for m in member.metrics],
        workouts=[Workout(**_dump(w)) for w in member.workouts]
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
    w_id = workout.id if workout.id else str(uuid.uuid4())[:8]
    new_workout = Workout(
        id=w_id,
        date=workout.date,
        description=workout.description,
        target_rpe=workout.target_rpe,
        actual_rpe=workout.actual_rpe,
        completed=workout.completed,
        notes=workout.notes
    )
    try:
        service.assign_workout(member_id, new_workout)
        return {"status": "Workout assigned", "workout_id": w_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/members/{member_id}/workouts")
@app.put("/members/{member_id}/workouts/")
def replace_workouts(member_id: str, request: BulkWorkoutsSchema):
    member = repo.find_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    _dump = lambda item: item.model_dump() if hasattr(item, "model_dump") else item.dict()
    member.workouts = [Workout(**_dump(w)) for w in request.workouts]
    if request.start_date:
        member.start_date = request.start_date
    if request.end_date:
        member.end_date = request.end_date
    if request.methodology_markdown is not None:
        member.methodology_markdown = request.methodology_markdown
    repo.save(member)
    return {"status": "Workouts updated", "count": len(member.workouts)}

@app.patch("/members/{member_id}/payment")
def update_payment(member_id: str, request: UpdatePaymentRequest):
    member = repo.find_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.paid = request.paid
    repo.save(member)
    return {"status": "Payment status updated", "paid": member.paid}

@app.patch("/members/{member_id}/workouts/{workout_id}")
def complete_workout(member_id: str, workout_id: str, request: CompleteWorkoutRequest):
    try:
        service.complete_workout(member_id, workout_id, request.rpe, request.notes)
        return {"status": "Workout completed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Note: Pydantic validates rpe 1-10 and request body JSON for dashboard compatibility.

@app.get("/members/", response_model=List[MemberSchema])
def list_members():
    return repo.list_all()

@app.post("/api/auth/login")
def login_coach(req: LoginRequest):
    with sqlite3.connect(repo.db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM coach_users WHERE username = ? AND password_hash = ?", (req.username.lower(), req.password)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        conn.execute("INSERT INTO audit_logs (timestamp, username, action, details) VALUES (?, ?, ?, ?)",
                     (date.today().isoformat(), req.username, "LOGIN_SUCCESS", "Coach logged in successfully"))
        conn.commit()
        return {"status": "authenticated", "username": row["username"], "role": row["role"], "token": f"token-{uuid.uuid4()}"}

@app.get("/api/audit-logs")
def get_audit_logs():
    with sqlite3.connect(repo.db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50").fetchall()
        return [dict(r) for r in rows]

@app.post("/api/payments/webhook")
def process_payment_webhook(req: WebhookPaymentRequest):
    ref = req.receipt_ref or f"REF-{str(uuid.uuid4())[:8].upper()}"
    with sqlite3.connect(repo.db_path) as conn:
        conn.execute("INSERT INTO payments (member_id, amount, status, recorded_at, receipt_ref) VALUES (?, ?, ?, ?, ?)",
                     (req.member_id, req.amount, "PAID", date.today().isoformat(), ref))
        conn.execute("UPDATE members SET paid = 1 WHERE id = ?", (req.member_id,))
        conn.commit()
    return {"status": "Payment processed successfully", "receipt_ref": ref}

@app.get("/api/members/{member_id}/payments")
def get_member_payments(member_id: str):
    with sqlite3.connect(repo.db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM payments WHERE member_id = ? ORDER BY id DESC", (member_id,)).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/members/{member_id}/feedback")
def generate_weekly_feedback(member_id: str):
    member = repo.find_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    completed = [w for w in member.workouts if w.completed]
    completion_rate = (len(completed) / len(member.workouts)) * 100 if member.workouts else 0
    avg_rpe = sum([w.actual_rpe for w in completed if w.actual_rpe]) / max(1, len([w for w in completed if w.actual_rpe]))

    feedback_text = f"¡Hola {member.name}! Esta semana completaste el {completion_rate:.0f}% de tus sesiones con un RPE promedio de {avg_rpe:.1f}/10. Excelente constancia en el bloque {member.current_phase.value}. Sigue priorizando la recuperación y mantén el ritmo aeróbico base."

    return {
        "member_id": member_id,
        "name": member.name,
        "completion_rate": completion_rate,
        "avg_rpe": avg_rpe,
        "feedback": feedback_text
    }

@app.get("/api/members/{member_id}/analytics")
def get_member_analytics(member_id: str):
    member = repo.find_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    completed_workouts = [w for w in member.workouts if w.completed]
    total_assigned = len(member.workouts)
    compliance = (len(completed_workouts) / total_assigned * 100) if total_assigned > 0 else 0

    load_status = "Óptima"
    rpe_diffs = [abs((w.actual_rpe or w.target_rpe) - w.target_rpe) for w in completed_workouts if w.target_rpe]
    avg_diff = sum(rpe_diffs) / len(rpe_diffs) if rpe_diffs else 0
    if avg_diff > 2.0:
        load_status = "Atención: Fatiga elevada (RPE real excede al objetivo)"
    elif compliance < 60:
        load_status = "Alerta: Baja adherencia al plan"

    vo2_history = [
        {"date": "2026-10-01", "vo2max": 38.5, "cooper_meters": 2100},
        {"date": "2026-10-15", "vo2max": 40.2, "cooper_meters": 2250},
        {"date": "2026-11-01", "vo2max": 41.8, "cooper_meters": 2380},
        {"date": "2026-11-15", "vo2max": 43.0, "cooper_meters": 2450}
    ]

    current_vo2 = vo2_history[-1]["vo2max"]
    pred_5k = f"{(25 - (current_vo2 - 35) * 0.4):.1f} mins"
    pred_10k = f"{(53 - (current_vo2 - 35) * 0.8):.1f} mins"

    return {
        "member_id": member_id,
        "compliance_rate": compliance,
        "load_status": load_status,
        "vo2_history": vo2_history,
        "predictions": {
            "5k": pred_5k,
            "10k": pred_10k
        }
    }

@app.post("/generate-plan")
def generate_plan_ai(request: PlanGenerateRequest):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-5-5",
                max_tokens=3000,
                messages=[{"role": "user", "content": request.prompt}]
            )
            return {"markdown": response.content[0].text}
        except Exception as e:
            print(f"Anthropic API error: {e}")

    # Professional Fallback / Gemini / LLM simulation output in Markdown
    name = request.name or "Renata Ramirez"
    meta = request.meta or "5K"
    md = f"""# Plan 5K/10K · {name}
DATOS DEL CORREDOR
- Nombre: {name}
- Edad: 16
- Peso / Estatura: 55.5 kg / 165 cm
- Meta: {meta}
- Fecha objetivo o carrera (si existe): no indicado
- Experiencia actual: Corro menos de 20 min seguidos
- Días por semana disponibles para entrenar: 4
- Días específicos preferidos: Lunes, Martes, Miércoles, Jueves
- Tiempo por sesión: 45 a 60 min
- Mejor marca reciente (si la conoce): No se
- Lesiones o molestias actuales o pasadas: Ninguna
- Condiciones médicas declaradas: Ninguna
- Terreno y horario habitual: Mixto, Tarde
- Equipo disponible: Nada
- Acceso a pesas o ligas: No

## 1. Tu punto de partida

Eres una corredora **NIVEL 1**, ya que actualmente corres menos de 20 minutos continuos y vamos a construir tu resistencia desde la base. *Supuestos:* Al no tener fecha de carrera ni marca previa, enfocaremos estas 12 semanas en desarrollar la capacidad aeróbica para completar 5K de forma continua y segura, entrenando sin equipo en terreno mixto (asfalto/tierra) y contemplando la altitud de Pachuca.

## 2. Cómo vas a entrenar

Nos guiaremos por tus sensaciones usando una escala de esfuerzo del 1 al 10. En los intervalos suaves y caminatas el esfuerzo será de **3 a 4**; en los bloques de trote suave será de **5 a 6**, donde debes pasar la "prueba del habla" (poder decir una frase completa sin ahogarte). Si sientes que te falta el aire, baja el ritmo de inmediato.

## 3. Calendario semanal

### Bloque 1: Adaptación y despertar aeróbico (Semanas 1 a 4)

**Semana 1: Primeros pasos**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Intervalos CaCo + Fuerza | 6 min caminata rápida + 8 x (1 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 1 de fuerza (15 min) | 5 en trote / 3 en caminata |
| Martes | Caminata activa y movilidad | 5 min caminata suave + 25 min caminata a paso vigoroso + 5 min estiramientos suaves | 4 |
| Miércoles | Intervalos CaCo + Fuerza | 6 min caminata rápida + 8 x (1 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 2 de fuerza (15 min) | 5 en trote / 3 en caminata |
| Jueves | Intervalos suaves | 6 min caminata rápida + 6 x (1.5 min trote suave / 2 min caminata) + 5 min caminata suave | 5 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 2: Ganando confianza**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Intervalos CaCo + Fuerza | 6 min caminata rápida + 7 x (2 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 1 de fuerza (15 min) | 5 en trote |
| Martes | Caminata activa y movilidad | 5 min caminata suave + 28 min caminata vigorosa + 5 min estiramientos suaves | 4 |
| Miércoles | Intervalos CaCo + Fuerza | 6 min caminata rápida + 7 x (2 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 2 de fuerza (15 min) | 5 en trote |
| Jueves | Intervalos suaves | 6 min caminata rápida + 6 x (2.5 min trote suave / 2 min caminata) + 5 min caminata suave | 5-6 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 3: Progresión de bloque**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Intervalos CaCo + Fuerza | 6 min caminata rápida + 6 x (3 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 1 de fuerza (15 min) | 5-6 |
| Martes | Caminata activa y movilidad | 5 min caminata suave + 30 min caminata vigorosa + 5 min estiramientos suaves | 4 |
| Miércoles | Intervalos CaCo + Fuerza | 6 min caminata rápida + 6 x (3 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 2 de fuerza (15 min) | 5-6 |
| Jueves | Intervalos suaves | 6 min caminata rápida + 5 x (4 min trote suave / 2 min caminata) + 5 min caminata suave | 5-6 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 4: Consolidación y prueba de 15 min**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Intervalos ligeros + Fuerza | 6 min caminata rápida + 5 x (2 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 1 de fuerza (15 min) | 5 |
| Martes | Descanso activo | 25 min caminata relajada + movilidad articular | 3 |
| Miércoles | Activación + Fuerza | 6 min caminata rápida + 4 x (2 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 2 de fuerza (15 min) | 5 |
| Jueves | Prueba de control 1 | 8 min calentamiento (caminata rápida + movilidad) + 15 min de trote continuo cómodo + 5 min caminata suave | 6 (prueba del habla) |
| Viernes a Domingo | Descanso total | Asimilación del primer mes | 1 |

---

### Bloque 2: Construcción de resistencia (Semanas 5 a 8)

**Semana 5: Extendiendo el trote**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Intervalos largos + Fuerza | 6 min caminata rápida + 4 x (5 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 1 de fuerza (18 min) | 5-6 |
| Martes | Recuperación activa | 5 min caminata suave + 25 min caminata vigorosa + 5 min estiramientos | 4 |
| Miércoles | Intervalos largos + Fuerza | 6 min caminata rápida + 4 x (5 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 2 de fuerza (18 min) | 5-6 |
| Jueves | Trote estructurado | 6 min caminata rápida + 3 x (7 min trote suave / 2 min caminata) + 5 min caminata suave | 6 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 6: Menos pausas**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Intervalos largos + Fuerza | 6 min caminata rápida + 3 x (8 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 1 de fuerza (18 min) | 5-6 |
| Martes | Recuperación activa | 5 min caminata suave + 28 min caminata vigorosa + 5 min estiramientos | 4 |
| Miércoles | Intervalos largos + Fuerza | 6 min caminata rápida + 3 x (8 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 2 de fuerza (18 min) | 5-6 |
| Jueves | Trote estructurado | 6 min caminata rápida + 2 x (12 min trote suave / 2 min caminata) + 5 min caminata suave | 6 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 7: Pico de resistencia media**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Intervalos largos + Fuerza | 6 min caminata rápida + 3 x (9 min trote suave / 1.5 min caminata) + 5 min caminata suave + Rutina 1 de fuerza (18 min) | 6 |
| Martes | Recuperación activa | 5 min caminata suave + 30 min caminata vigorosa + 5 min estiramientos | 4 |
| Miércoles | Intervalos largos + Fuerza | 6 min caminata rápida + 2 x (14 min trote suave / 2 min caminata) + 5 min caminata suave + Rutina 2 de fuerza (18 min) | 6 |
| Jueves | Trote continuo base | 7 min calentamiento (caminata rápida) + 22 min trote continuo suave + 5 min caminata suave | 6 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 8: Consolidación y prueba de 25 min**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Trote suave + Fuerza | 6 min caminata rápida + 18 min trote suave + 5 min caminata suave + Rutina 1 de fuerza (15 min) | 5 |
| Martes | Descanso activo | 25 min caminata relajada + movilidad articular | 3 |
| Miércoles | Activación + Fuerza | 6 min caminata rápida + 15 min trote suave + 5 min caminata suave + Rutina 2 de fuerza (15 min) | 5 |
| Jueves | Prueba de control 2 | 8 min calentamiento + 25 min de trote continuo cómodo + 5 min caminata suave | 6-7 |
| Viernes a Domingo | Descanso total | Asimilación del segundo mes | 1 |

---

### Bloque 3: Consolidación 5K (Semanas 9 a 12)

**Semana 9: Trote continuo**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Rodaje suave + Fuerza | 6 min caminata rápida + 24 min trote continuo suave + 5 min caminata suave + Rutina 1 de fuerza (20 min) | 5-6 |
| Martes | Recuperación activa | 5 min caminata suave + 25 min caminata vigorosa + 5 min estiramientos | 4 |
| Miércoles | Cambios suaves + Fuerza | 6 min caminata rápida + 20 min trote suave intercalando 4 aceleraciones ligeras de 30 seg (sin esprintar) + 5 min caminata + Rutina 2 (20 min) | 6 |
| Jueves | Fondo corto | 7 min calentamiento + 28 min trote continuo suave + 5 min caminata suave | 5-6 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 10: Acercándonos a la meta**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Rodaje suave + Fuerza | 6 min caminata rápida + 26 min trote continuo suave + 5 min caminata suave + Rutina 1 de fuerza (20 min) | 5-6 |
| Martes | Recuperación activa | 5 min caminata suave + 25 min caminata vigorosa + 5 min estiramientos | 4 |
| Miércoles | Cambios suaves + Fuerza | 6 min caminata rápida + 22 min trote suave con 5 aceleraciones ligeras de 30 seg + 5 min caminata + Rutina 2 (20 min) | 6 |
| Jueves | Fondo base | 7 min calentamiento + 32 min trote continuo suave + 5 min caminata suave | 5-6 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 11: Pico de volumen 5K**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Rodaje suave + Fuerza | 6 min caminata rápida + 28 min trote continuo suave + 5 min caminata suave + Rutina 1 de fuerza (15 min) | 5-6 |
| Martes | Recuperación activa | 5 min caminata suave + 25 min caminata vigorosa + 5 min estiramientos | 4 |
| Miércoles | Rodaje controlado + Fuerza | 6 min caminata rápida + 25 min trote continuo cómodo + 5 min caminata suave + Rutina 2 (15 min) | 6 |
| Jueves | Fondo largo | 8 min calentamiento + 36 min trote continuo suave + 5 min caminata suave | 5-6 |
| Viernes a Domingo | Descanso total | Recuperación completa sin impacto | 1 |

**Semana 12: Descarga y Prueba Final 5K**

| Día | Sesión | Detalle exacto (tiempos, intervalos) | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Rodaje ligero + Fuerza | 6 min caminata rápida + 20 min trote muy suave + 5 min caminata suave + Rutina 1 ligera (12 min) | 4-5 |
| Martes | Descanso activo | 20 min caminata relajada + movilidad articular | 3 |
| Miércoles | Activación | 6 min caminata rápida + 15 min trote muy suave + 3 aceleraciones suaves de 20 seg + 5 min caminata | 5 |
| Jueves | **PRUEBA FINAL 5K** | 8 min calentamiento (caminata rápida + movilidad) + **5K continuos a ritmo cómodo y sostenido** + 5 min caminata suave | 7 (sostenido) |
| Viernes a Domingo | Descanso total | Celebración y recuperación post-meta | 1 |

## 4. Fuerza y movilidad

Realiza estas rutinas en casa con tu propio peso corporal al terminar tus sesiones de lunes y miércoles (descansa 45-60 segundos entre series).

**Rutina 1: Piernas y estabilidad (Blindaje articular)**

* **Sentadilla libre:** 3 series de 12 repeticiones (baja controlando el movimiento, sin que las rodillas se metan hacia adentro).
* **Desplantes hacia atrás alternados:** 3 series de 8 repeticiones por pierna (pasos cortos y estables).
* **Elevación de talones (pantorrillas):** 3 series de 15 repeticiones (sube en 1 segundo, baja lento en 3 segundos).
* **Movilidad de tobillo y cadera:** 2 minutos de círculos suaves con tobillos y balanceos controlados de pierna.

**Rutina 2: Core y postura**

* **Puente de glúteo en el piso:** 3 series de 15 repeticiones (aprieta glúteos arriba por 2 segundos).
* **Plancha frontal sobre antebrazos:** 3 series de 25 a 35 segundos (mantén el abdomen firme y la espalda recta).
* **Bird-Dog (perro de caza en cuatro puntos):** 3 series de 8 repeticiones por lado (estira brazo derecho y pierna izquierda manteniendo el equilibrio).
* **Estiramiento suave de espalda y flexores:** 2 minutos en postura del niño y estiramiento de zancada baja.

## 5. Hidratación, sueño y alimentación general

* Toma agua natural de forma constante durante todo el día, no esperes a tener sed antes de salir a entrenar por la tarde.
* Procura dormir entre 8 y 9 horas cada noche; a tus 16 años el descanso nocturno es fundamental para que tus músculos y huesos se fortalezcan.
* Haz una comida ligera rica en carbohidratos fáciles de digerir (como una fruta o un pan tostado) entre 60 y 90 minutos antes de tu sesión vespertina.
* Evita comidas muy grasosas, picantes o pesadas justo antes de correr para prevenir molestias estomacales.
* Incluye alimentos naturales y variados en tus comidas principales (frutas, verduras, cereales integrales y fuentes de proteína) para recuperar energía después de entrenar.

## 6. Señales de alto: cuándo parar y consultar

Detén de inmediato tu entrenamiento y avisa a tus papás o acude a valoración médica si presentas cualquiera de estas señales:

* Dolor agudo o punzante en rodillas, tobillos, espinillas o cadera.
* Mareos, sensación de desmayo o visión nublada durante o después del esfuerzo.
* Dolor, opresión o pinchazos en el pecho.
* Falta de aire anormal que no mejora al bajar el ritmo o empezar a caminar.
* Cualquier molestia muscular o articular que te haga cojear o que persista por más de 48 horas.

## 7. Día de carrera o prueba final

El jueves de la Semana 12 realizarás tu prueba de 5K en un tramo plano y seguro de tu recorrido habitual. Haz tu calentamiento completo de 8 minutos caminando a paso vivo y moviendo tus articulaciones; no salgas corriendo de golpe. Tu estrategia será empezar más lento de lo que crees necesario durante los primeros 10 minutos para controlar tu respiración; a la mitad del recorrido mantén un paso constante donde puedas hablar con frases cortas, y si en los últimos minutos te sientes fuerte, acelera un poco de forma gradual. Evita estrenar tenis o calcetines ese día y no te compares con el ritmo de nadie más.

## 8. Tu siguiente paso

Al terminar estas 12 semanas y completar tus 5K, tómate de 4 a 5 días de descanso activo (caminatas suaves y estiramientos) para celebrar tu logro y permitir que tu cuerpo asimile el trabajo. Después evaluaremos cómo te sentiste en la prueba final para decidir si iniciamos un bloque enfocado en mejorar tu velocidad en los 5K o si comenzamos a construir distancia poco a poco hacia tu primer 10K.

---

Nota final: "Este plan es una guía general de entrenamiento y no sustituye la valoración de un profesional de la salud. Detente ante cualquier síntoma preocupante."
"""
    return {"markdown": md}

class MarkdownImportSchema(BaseModel):
    markdown_content: str
    member_id: Optional[str] = None
    email: Optional[str] = None

@app.post("/api/members/import-markdown")
def import_member_from_markdown(req: MarkdownImportSchema):
    mdText = req.markdown_content
    import re
    name_match = re.search(r'[-*]\s*Nombre[:\s]*(.*)', mdText, re.IGNORECASE) or re.search(r'#\s*Plan.*?·\s*(.*)', mdText, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else "Atleta A Tu Marca"

    age_match = re.search(r'[-*]\s*Edad[:\s*]*(\d+)', mdText, re.IGNORECASE)
    age = int(age_match.group(1)) if age_match else 35

    email = req.email or f"{name.lower().replace(' ', '')}@runnersinsedad.com"
    member_id = req.member_id or name.lower().replace(' ', '-').replace('--', '-')

    birth_year = date.today().year - age
    birth_date = date(birth_year, 1, 1)

    today = date.today()
    day_offset = today.weekday()
    base_start_date = today - timedelta(days=day_offset)
    end_date = base_start_date + timedelta(days=84)

    day_offsets = {
        "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
        "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6
    }

    lines = mdText.split('\n')
    current_week = 1
    workouts = []

    for line in lines:
        line = line.strip()
        week_match = re.search(r'Semana\s+(\d+)', line, re.IGNORECASE)
        if week_match:
            current_week = int(week_match.group(1))
            continue

        if line.startswith('|'):
            cols = [c.strip() for c in line.split('|') if c.strip() != '']
            if len(cols) >= 2:
                day_raw = cols[0].lower()
                if 'día' in day_raw or 'dia' in day_raw or '---' in day_raw:
                    continue
                session_type = cols[1] if len(cols) > 1 else "Entrenamiento"
                detail = cols[2] if len(cols) > 2 else session_type
                effort_raw = cols[3] if len(cols) > 3 else (cols[2] if len(cols) > 2 else "5")
                rpe_match = re.search(r'(\d+)', effort_raw)
                target_rpe = int(rpe_match.group(1)) if rpe_match else 5
                target_rpe = max(1, min(10, target_rpe))

                days_to_process = []
                for d_name, off in day_offsets.items():
                    if d_name in day_raw:
                        days_to_process.append(off)
                        break

                if not days_to_process and (' a ' in day_raw or '-' in day_raw):
                    parts = re.split(r'\s+a\s+|\s*-\s*', day_raw)
                    if len(parts) == 2:
                        start_off = day_offsets.get(parts[0].strip(), 0)
                        end_off = day_offsets.get(parts[1].strip(), 6)
                        for o in range(start_off, end_off + 1):
                            days_to_process.append(o)

                if not days_to_process:
                    days_to_process = [0]

                for offset in days_to_process:
                    w_date = base_start_date + timedelta(weeks=(current_week - 1), days=offset)
                    w_id = f"s{current_week}-{uuid.uuid4().hex[:6]}"
                    description = f"{session_type}: {detail}" if detail != session_type else session_type
                    workouts.append(Workout(
                        id=w_id,
                        date=w_date,
                        description=description,
                        target_rpe=target_rpe,
                        completed=False
                    ))

    meth_lines = []
    for line in mdText.split('\n'):
        if line.startswith('## ') and not any(k in line.lower() for k in ['calendario', 'semana']):
            meth_lines.append(line)
        elif meth_lines and not line.startswith('|'):
            meth_lines.append(line)

    methodology_markdown = "\n".join(meth_lines) if meth_lines else mdText

    member = Member(
        id=member_id,
        name=name,
        email=email,
        birth_date=birth_date,
        current_phase=TrainingPhase.BASE,
        start_date=base_start_date,
        end_date=end_date,
        paid=True,
        methodology_markdown=methodology_markdown,
        workouts=workouts
    )
    repo.save(member)
    return {"status": "Member imported successfully", "member_id": member_id, "name": name, "workouts_count": len(workouts)}

@app.get("/api/members/{member_id}/whatsapp-export")
def whatsapp_export(member_id: str):
    member = repo.find_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    msg = f"🏃 *A TU MARCA — PLAN DE ENTRENAMIENTO*\n"
    msg += f"Atleta: *{member.name}*\n"
    msg += f"Fase: {member.current_phase.value}\n"
    msg += f"Periodo: {member.start_date} al {member.end_date}\n\n"
    msg += f"📋 *Próximas Sesiones / Resumen:*\n"
    for w in member.workouts[:7]:
        status = "✅" if w.completed else "⏳"
        msg += f"{status} *{w.date}* — {w.description} (RPE Obj: {w.target_rpe})\n"
    msg += f"\n¡Mucho éxito en tu sesión! Recuerda mantener el esfuerzo programado y reportar tu RPE al terminar. 🔥"
    return {"whatsapp_text": msg}

@app.get("/coach")
@app.get("/coach.html")
def serve_coach():
    coach_path = os.path.join(PROJECT_ROOT, "apps", "runners_sin_edad", "coach.html")
    if not os.path.exists(coach_path):
        raise HTTPException(status_code=404, detail="Coach panel not found")
    return FileResponse(coach_path)

@app.get("/dashboard")
@app.get("/dashboard.html")
def serve_dashboard():
    dashboard_path = os.path.join(PROJECT_ROOT, "apps", "runners_sin_edad", "dashboard.html")
    if not os.path.exists(dashboard_path):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(dashboard_path)

@app.get("/manifest.json")
def serve_manifest():
    p = os.path.join(PROJECT_ROOT, "apps", "runners_sin_edad", "manifest.json")
    return FileResponse(p, media_type="application/json")

@app.get("/sw.js")
def serve_sw():
    p = os.path.join(PROJECT_ROOT, "apps", "runners_sin_edad", "sw.js")
    return FileResponse(p, media_type="application/javascript")

@app.get("/planes-entreno/{file_name}")
def serve_planes_entreno(file_name: str):
    allowed_files = {
        "index.html",
        "cooper-vo2max.html",
        "plan-semanal.html",
        "bitacora.html",
        "ritmos-edad.html",
        "README.md",
    }
    if file_name not in allowed_files:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(PROJECT_ROOT, "PlanesEntreno", file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("apps.runners_sin_edad.main:app", host="0.0.0.0", port=port)
