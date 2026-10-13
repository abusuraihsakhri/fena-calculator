import os

os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-not-for-production")

from fastapi.testclient import TestClient
from agents.api import app


def test_static_browser_and_health():
    client = TestClient(app)
    page = client.get("/")
    assert page.status_code == 200
    assert "FENa Calculator" in page.text
    module = client.get("/calculator.mjs")
    assert module.status_code == 200
    assert "calculateFena" in module.text
    assert client.get("/health").json()["status"] == "healthy"


def test_audit_logs_require_explicit_authorization(monkeypatch):
    client = TestClient(app)
    monkeypatch.delenv("AUDIT_READ_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 403
    monkeypatch.setenv("AUDIT_READ_TOKEN", "unit-test-log-read-token")
    assert client.get("/api/audit/logs").status_code == 403
    assert client.get("/api/audit/logs", headers={"X-Audit-Read-Token": "incorrect"}).status_code == 403
    response = client.get("/api/audit/logs", headers={"X-Audit-Read-Token": "unit-test-log-read-token"})
    assert response.status_code == 200
    assert response.json()["verified"] is True


def test_mock_chat_does_not_claim_clinical_validation():
    client = TestClient(app)
    response = client.post("/api/chat", json={"query": "Explain the FENa formula"})
    assert response.status_code == 200
    assert "no clinical analysis performed" in response.json()["response"]
