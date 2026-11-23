"""
Pruebas exhaustivas para Runners Sin Edad (Arquitectura Hexagonal).
Valida Dominio, Aplicacion, Infraestructura y API (FastAPI).
Cumple con estandares L3 y CLAUDE.md (camino feliz y casos de error).
"""

from datetime import date
import pytest
from fastapi.testclient import TestClient

from apps.runners_sin_edad.domain.models import Member, Workout, TrainingPhase, Metric
from apps.runners_sin_edad.application.services import TrainingPlanService, MemberRepository
from apps.runners_sin_edad.infrastructure.repository import SQLiteMemberRepository
from apps.runners_sin_edad.main import app, repo, service


# ============================================================================
# 1. Tests de Dominio
# ============================================================================

def test_member_and_metric_creation():
    """Valida la creacion de entidades Member y Value Objects Metric."""
    member = Member(
        id="mem-001",
        name="Carlos Perez",
        email="carlos@example.com",
        birth_date=date(1982, 5, 14),
        current_phase=TrainingPhase.BASE,
    )
    assert member.id == "mem-001"
    assert member.current_phase == TrainingPhase.BASE
    assert len(member.metrics) == 0

    metric = Metric(name="VO2max", value=42.5, unit="ml/kg/min", recorded_at=date(2026, 11, 10))
    member.add_metric(metric)
    assert len(member.metrics) == 1
    assert member.metrics[0].value == 42.5

    member.update_phase(TrainingPhase.STRENGTH)
    assert member.current_phase == TrainingPhase.STRENGTH


def test_workout_entity():
    """Valida la entidad Workout y su estado inicial."""
    workout = Workout(
        id="w-101",
        date=date(2026, 11, 13),
        description="Rodaje 8k Zona 2",
        target_rpe=6,
    )
    assert workout.completed is False
    assert workout.actual_rpe is None


# ============================================================================
# 2. Tests de Aplicacion (TrainingPlanService)
# ============================================================================

class InMemoryMemberRepository(MemberRepository):
    """Repositorio en memoria para aislar la capa de aplicacion."""

    def __init__(self):
        self._members = {}

    def save(self, member: Member) -> None:
        self._members[member.id] = member

    def find_by_id(self, member_id: str):
        return self._members.get(member_id)

    def list_all(self):
        return list(self._members.values())


def test_service_assign_and_complete_workout_happy_path():
    """Prueba el flujo completo de asignar y completar un entrenamiento."""
    repo_mem = InMemoryMemberRepository()
    serv = TrainingPlanService(repo_mem)

    member = Member(
        id="m-1",
        name="Lucia Gomez",
        email="lucia@example.com",
        birth_date=date(1980, 2, 20),
        current_phase=TrainingPhase.BASE,
    )
    repo_mem.save(member)

    # 1. Asignar workout
    workout = Workout(id="w-1", date=date(2026, 11, 13), description="Series 4x1000m", target_rpe=8)
    serv.assign_workout("m-1", workout)

    updated = repo_mem.find_by_id("m-1")
    assert len(updated.workouts) == 1
    assert updated.workouts[0].completed is False

    # 2. Completar workout
    serv.complete_workout("m-1", "w-1", rpe=8, notes="Buen ritmo en pista")
    finished = repo_mem.find_by_id("m-1")
    assert finished.workouts[0].completed is True
    assert finished.workouts[0].actual_rpe == 8
    assert finished.workouts[0].notes == "Buen ritmo en pista"


def test_service_errors():
    """Valida los flujos de error en el servicio de aplicacion."""
    repo_mem = InMemoryMemberRepository()
    serv = TrainingPlanService(repo_mem)

    # Error: Asignar a miembro inexistente
    with pytest.raises(ValueError, match="Member non-existent not found"):
        serv.assign_workout("non-existent", Workout(id="w-1", date=date.today(), description="Run", target_rpe=5))

    # Error: Completar en miembro inexistente
    with pytest.raises(ValueError, match="Member non-existent not found"):
        serv.complete_workout("non-existent", "w-1", rpe=6)

    # Error: Completar workout inexistente en miembro existente
    member = Member(id="m-2", name="Pedro", email="p@ex.com", birth_date=date(1975, 1, 1), current_phase=TrainingPhase.BASE)
    repo_mem.save(member)

    with pytest.raises(ValueError, match="Workout invalid-w not found"):
        serv.complete_workout("m-2", "invalid-w", rpe=7)


# ============================================================================
# 3. Tests de Infraestructura (SQLiteMemberRepository)
# ============================================================================

def test_sqlite_repository(tmp_path):
    """Valida persistencia real en SQLite en un archivo temporal aislado."""
    db_file = str(tmp_path / "test_runners.db")
    sql_repo = SQLiteMemberRepository(db_path=db_file)

    member = Member(
        id="sql-001",
        name="Ana Garcia",
        email="ana@example.com",
        birth_date=date(1985, 8, 22),
        current_phase=TrainingPhase.SPEED,
    )
    metric = Metric(name="Cooper Test", value=2350.0, unit="m", recorded_at=date(2026, 11, 1))
    workout = Workout(id="w-sql-1", date=date(2026, 11, 14), description="Tirada Larga 14k", target_rpe=7)

    member.add_metric(metric)
    member.workouts.append(workout)

    # Guardar
    sql_repo.save(member)

    # Recuperar
    loaded = sql_repo.find_by_id("sql-001")
    assert loaded is not None
    assert loaded.name == "Ana Garcia"
    assert loaded.current_phase == TrainingPhase.SPEED
    assert len(loaded.metrics) == 1
    assert loaded.metrics[0].value == 2350.0
    assert len(loaded.workouts) == 1
    assert loaded.workouts[0].description == "Tirada Larga 14k"

    # Listar
    all_members = sql_repo.list_all()
    assert len(all_members) == 1
    assert all_members[0].id == "sql-001"

    # Buscar inexistente
    assert sql_repo.find_by_id("missing-id") is None


# ============================================================================
# 4. Tests de API (FastAPI Endpoints)
# ============================================================================

@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """Configura un cliente de prueba con base de datos temporal aislada."""
    test_db = str(tmp_path / "api_test.db")
    test_repo = SQLiteMemberRepository(db_path=test_db)
    test_service = TrainingPlanService(test_repo)

    monkeypatch.setattr("apps.runners_sin_edad.main.repo", test_repo)
    monkeypatch.setattr("apps.runners_sin_edad.main.service", test_service)

    return TestClient(app)


def test_api_read_root(api_client):
    """Valida el endpoint raiz."""
    response = api_client.get("/")
    assert response.status_code == 200
    assert "Runners Sin Edad API is online" in response.json()["message"]


def test_api_create_and_get_member(api_client):
    """Valida la creacion y consulta de un miembro via REST."""
    payload = {
        "id": "runner-100",
        "name": "Ruben Test",
        "email": "ruben.test@example.com",
        "birth_date": "1983-04-12",
        "current_phase": "Base",
        "metrics": [{"name": "VO2max", "value": 48.0, "unit": "ml/kg/min", "recorded_at": "2026-11-01"}],
        "workouts": [],
    }
    create_res = api_client.post("/members/", json=payload)
    assert create_res.status_code == 200
    assert create_res.json()["id"] == "runner-100"

    # Obtener miembro
    get_res = api_client.get("/members/runner-100")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Ruben Test"
    assert len(get_res.json()["metrics"]) == 1


def test_api_member_not_found(api_client):
    """Valida error 404 al consultar un miembro inexistente."""
    res = api_client.get("/members/non-existent-id")
    assert res.status_code == 404
    assert res.json()["detail"] == "Member not found"


def test_api_assign_and_complete_workout_patch_json_body(api_client):
    """
    Valida el flujo de workout y especificamente el FIX del endpoint PATCH:
    Envia el payload como JSON body (como lo hace dashboard.html).
    """
    # 1. Crear miembro
    member_data = {
        "id": "runner-patch-test",
        "name": "Maratonista 35+",
        "email": "master@example.com",
        "birth_date": "1988-10-10",
        "current_phase": "Fuerza",
        "metrics": [],
        "workouts": [],
    }
    api_client.post("/members/", json=member_data)

    # 2. Asignar workout
    workout_data = {
        "id": "w-patch-1",
        "date": "2026-11-13",
        "description": "Fartlek 10x 1' rapido / 1' suave",
        "target_rpe": 8,
        "completed": False,
    }
    assign_res = api_client.post("/members/runner-patch-test/workouts/", json=workout_data)
    assert assign_res.status_code == 200
    assert assign_res.json()["workout_id"] == "w-patch-1"

    # 3. Completar workout enviando JSON body (solucionando el bug del dashboard)
    patch_payload = {
        "rpe": 9,
        "notes": "Excelente sensacion en los cambios de ritmo",
    }
    patch_res = api_client.patch("/members/runner-patch-test/workouts/w-patch-1", json=patch_payload)
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Workout completed"

    # 4. Verificar que se actualizo en la base de datos
    check_res = api_client.get("/members/runner-patch-test")
    assert check_res.status_code == 200
    w_updated = check_res.json()["workouts"][0]
    assert w_updated["completed"] is True
    assert w_updated["actual_rpe"] == 9
    assert w_updated["notes"] == "Excelente sensacion en los cambios de ritmo"


def test_api_complete_workout_errors(api_client):
    """Valida que los flujos de error devuelvan codigos 404 adecuados."""
    patch_payload = {"rpe": 7, "notes": "Test"}

    # Miembro inexistente -> 404
    res1 = api_client.patch("/members/ghost/workouts/w-1", json=patch_payload)
    assert res1.status_code == 404

    # Miembro existe pero workout inexistente -> 404
    api_client.post("/members/", json={
        "id": "runner-empty",
        "name": "Empty",
        "email": "e@ex.com",
        "birth_date": "1990-01-01",
        "current_phase": "Base",
        "metrics": [],
        "workouts": [],
    })
    res2 = api_client.patch("/members/runner-empty/workouts/invalid-wid", json=patch_payload)
    assert res2.status_code == 404


def test_api_import_markdown(api_client):
    """Valida la importacion de un atleta y su plan a partir de Markdown."""
    sample_md = """# Plan 5K/10K · Atleta Test Markdown
DATOS DEL CORREDOR
- Nombre: Atleta Test Markdown
- Edad: 38
- Meta: 5K

## 3. Calendario semanal
**Semana 1: Primeros pasos**
| Día | Sesión | Detalle exacto | Esfuerzo (1-10) |
| --- | --- | --- | --- |
| Lunes | Intervalos CaCo | 6 min caminata + 8x(1' trote / 2' caminata) | 5 |
| Miércoles | Intervalos CaCo | 6 min caminata + 8x(1' trote / 2' caminata) | 5 |

## 4. Fuerza y movilidad
Rutinas de fuerza general.
"""
    res = api_client.post("/api/members/import-markdown", json={"markdown_content": sample_md})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Member imported successfully"
    assert data["workouts_count"] == 2
    assert "atleta-test-markdown" in data["member_id"]

    # Verificar que el miembro fue creado en la base de datos
    member_res = api_client.get(f"/members/{data['member_id']}")
    assert member_res.status_code == 200
    assert member_res.json()["name"] == "Atleta Test Markdown"
    assert len(member_res.json()["workouts"]) == 2


def test_api_whatsapp_export(api_client):
    """Valida la generacion del formato de texto para compartir por WhatsApp."""
    # 1. Crear miembro con sesión
    member_payload = {
        "id": "runner-wa-test",
        "name": "Corredor WhatsApp",
        "email": "wa@test.com",
        "birth_date": "1985-06-15",
        "current_phase": "Base",
        "workouts": [
            {
                "id": "w-wa-1",
                "date": "2026-11-23",
                "description": "Trote regenerativo 30min",
                "target_rpe": 4,
                "completed": False
            }
        ]
    }
    api_client.post("/members/", json=member_payload)

    # 2. Consultar exportación WhatsApp
    wa_res = api_client.get("/api/members/runner-wa-test/whatsapp-export")
    assert wa_res.status_code == 200
    wa_data = wa_res.json()
    assert "whatsapp_text" in wa_data
    assert "Corredor WhatsApp" in wa_data["whatsapp_text"]
    assert "Trote regenerativo 30min" in wa_data["whatsapp_text"]

