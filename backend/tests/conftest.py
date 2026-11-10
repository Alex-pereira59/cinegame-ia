"""Configuración de pruebas: SQLite temporal y modelo de IA simulado (sin llamadas externas)."""
import json
import os
import tempfile

_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_db.name}"
os.environ["LLM_PROVIDER"] = "fake"
os.environ["SKIP_INIT_DB"] = "1"
os.environ["JWT_SECRET"] = "test-secret-con-longitud-suficiente-1234567890"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.ai.llm import LLMClient, LLMResponse, ToolCall, get_llm  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


class ScriptedLLM(LLMClient):
    """LLM de prueba: devuelve respuestas programadas y registra los mensajes recibidos."""

    def __init__(self, script=None, default="Respuesta de prueba [#1]", tokens=(100, 20)):
        self.script = list(script or [])
        self.default = default
        self.tokens = tokens
        self.calls = []

    def chat(self, messages, tools=None, model=None, temperature=0.3):
        self.calls.append({"messages": [dict(m) for m in messages], "tools": tools})
        if self.script:
            item = self.script.pop(0)
            if isinstance(item, tuple):  # (nombre_herramienta, argumentos)
                return LLMResponse("", [ToolCall(f"call_{len(self.calls)}", item[0], json.dumps(item[1]))],
                                   *self.tokens)
            return LLMResponse(item, [], *self.tokens)
        return LLMResponse(self.default, [], *self.tokens)


@pytest.fixture()
def llm():
    fake = ScriptedLLM()
    app.dependency_overrides[get_llm] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_llm, None)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db, demo_users=True)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def admin_h(client):
    return login(client, "admin", "Admin123!")


@pytest.fixture()
def user_h(client):
    return login(client, "alex", "Usuario123!")
