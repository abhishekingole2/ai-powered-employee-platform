from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient

from app.ai_executor import execute_tool
from app.ai_service import get_conversation_history
from app.database import get_db
from app.main import app
from app.models import AIConversationDB, AIMessageDB
from app.security import (
    SECRET_KEY,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.llm_provider import OllamaProvider


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_password_hashing_and_verification():
    password = "correct horse battery staple"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("incorrect password", hashed)


def test_jwt_creation_and_validation():
    token = create_access_token({"sub": "17"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

    assert payload["sub"] == "17"
    assert "exp" in payload


def test_ollama_provider_reads_environment_configuration(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama-host:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b")

    provider = OllamaProvider()

    assert provider.base_url == "http://ollama-host:11434"
    assert provider.model == "qwen2.5:7b"


def test_protected_employee_endpoint_rejects_missing_auth(client):
    response = client.get("/employees")

    assert response.status_code == 401


def test_role_authorization_rejects_employee_from_admin_route(client):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1,
        role="employee",
    )

    response = client.get("/admin/test")

    assert response.status_code == 403


def test_authenticated_user_response_includes_linked_employee_id(client):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1,
        username="abhishek",
        email="user@example.com",
        role="employee",
        employee_id=42,
    )

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["employee_id"] == 42


def test_unknown_ai_tool_is_rejected():
    with pytest.raises(ValueError, match="Unknown tool"):
        execute_tool(
            tool_name="not_a_real_tool",
            current_user=SimpleNamespace(role="employee"),
            db=object(),
        )


def test_invalid_ai_tool_arguments_are_rejected():
    with pytest.raises(ValueError, match="Invalid arguments"):
        execute_tool(
            tool_name="search_employees",
            current_user=SimpleNamespace(role="employee"),
            db=object(),
            arguments={},
        )


def test_conversation_ownership_is_enforced_by_chat_endpoint(client):
    class Query:
        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return SimpleNamespace(id=23, user_id=2)

    class FakeDB:
        def query(self, model):
            assert model is AIConversationDB
            return Query()

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1,
        role="employee",
    )
    app.dependency_overrides[get_db] = lambda: FakeDB()

    response = client.post(
        "/ai/chat",
        json={"message": "hello", "conversation_id": 23},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have access to this conversation"


@pytest.mark.parametrize(
    "path,page",
    [
        ("/login", "login"),
        ("/dashboard", "dashboard"),
        ("/ui/projects", "projects"),
        ("/leave", "leave"),
        ("/ui/employees", "employees"),
        ("/ai-assistant", "ai_assistant"),
    ],
)
def test_ui_pages_render_with_expected_auth_guard_marker(client, path, page):
    response = client.get(path)

    assert response.status_code == 200
    assert f'data-page="{page}"' in response.text
    if page != "login":
        assert 'data-protected="true"' in response.text


def test_static_javascript_is_served(client):
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "Authorization" in response.text
    assert 'window.location.replace("/login")' in response.text


def test_tool_result_history_preserves_ollama_tool_name_and_call_id():
    stored_messages = [
        SimpleNamespace(
            role="assistant",
            content="",
            tool_calls_data=[
                {
                    "id": "call_abc",
                    "type": "function",
                    "function": {"name": "get_my_projects", "arguments": {}},
                }
            ],
        ),
        SimpleNamespace(
            role="tool",
            content='[{"id": 1}]',
            tool_calls_data={
                "tool_name": "get_my_projects",
                "tool_call_id": "call_abc",
            },
        ),
    ]

    class Query:
        def __init__(self, result):
            self.result = result

        def filter(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def first(self):
            return self.result

        def all(self):
            return self.result

    class FakeDB:
        def query(self, model):
            if model is AIConversationDB:
                return Query(SimpleNamespace(id=23, user_id=1))
            assert model is AIMessageDB
            return Query(stored_messages)

    history = get_conversation_history(
        conversation_id=23,
        current_user=SimpleNamespace(id=1),
        db=FakeDB(),
    )

    assert history[0]["tool_calls"][0]["id"] == "call_abc"
    assert history[1]["tool_name"] == "get_my_projects"
    assert history[1]["tool_call_id"] == "call_abc"
