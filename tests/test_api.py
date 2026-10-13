"""API tests via FastAPI TestClient against a seeded temp SQLite engine (no server/network)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from pls_ct.app.main import create_app
from pls_ct.config import REPO_ROOT
from pls_ct.dataset.build import build_examples, load_records
from pls_ct.db import repository
from pls_ct.db.engine import create_all
from pls_ct.evaluation.benchmark import run_benchmark
from pls_ct.models.baseline import LeadSentencesBackend
from pls_ct.rag.chunk import chunk_records
from pls_ct.rag.embeddings import HashingEmbedder
from pls_ct.rag.index import build_rows

SAMPLE = REPO_ROOT / "data" / "sample" / "trials.json"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PLS_PROCESSED_DIR", str(tmp_path))  # hermetic uploads dir
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", future=True)
    create_all(engine)

    records = load_records(SAMPLE)
    with Session(engine, future=True) as s:
        repository.load_records(s, records)
        repository.replace_chunks(s, build_rows(chunk_records(records), HashingEmbedder()))
        bench = run_benchmark([LeadSentencesBackend(2)], build_examples(records)[0][:4])
        repository.save_experiment(s, bench)
        s.commit()

    return TestClient(create_app(engine=engine))


def test_health_and_ready(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    ready = client.get("/api/ready").json()
    assert ready["database"] is True


def test_stats(client):
    stats = client.get("/api/stats").json()
    assert stats["trials"] == 6
    assert stats["chunks"] > 0
    assert stats["experiments"] == 1


def test_backends_lists_lead_and_providers(client):
    specs = {b["spec"]: b for b in client.get("/api/backends").json()["backends"]}
    assert specs["lead"]["available"] is True
    anthropic = next(b for s, b in specs.items() if s.startswith("anthropic"))
    assert anthropic["available"] is False  # no key in test env


def test_trials_pagination_and_search(client):
    page = client.get("/api/trials", params={"limit": 2, "offset": 0}).json()
    assert page["total"] == 6 and len(page["items"]) == 2

    filtered = client.get("/api/trials", params={"q": "SYN001"}).json()
    assert all("SYN001" in it["protocol_id"] for it in filtered["items"])


def test_trial_detail_and_404(client):
    detail = client.get("/api/trials/SYN001A2101").json()
    assert detail["report_sections"]["Objectives"]
    assert client.get("/api/trials/NOPE").status_code == 404


def test_delete_trial(client):
    assert client.delete("/api/trials/SYN006F2306").status_code == 204
    assert client.get("/api/stats").json()["trials"] == 5
    assert client.delete("/api/trials/SYN006F2306").status_code == 404


def test_summarize_trial_and_raw_text(client):
    r1 = client.post("/api/summarize", json={"trial_name": "SYN001A2101", "backend": "lead"})
    assert r1.status_code == 200 and r1.json()["text"]

    r2 = client.post("/api/summarize", json={"context": "A. B. C.", "backend": "lead-1"})
    assert r2.status_code == 200 and r2.json()["model"] == "lead-1"


def test_summarize_requires_source(client):
    assert client.post("/api/summarize", json={"backend": "lead"}).status_code == 422


def test_summarize_provider_without_key_is_clean_400(client):
    r = client.post("/api/summarize", json={"context": "x", "backend": "anthropic"})
    assert r.status_code == 400
    assert r.json()["error"] == "provider_config"


def test_rag_ask(client):
    r = client.post("/api/rag/ask", json={"query": "What were the objectives?", "k": 3})
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body and "citations" in body


def test_experiments(client):
    items = client.get("/api/experiments").json()
    assert len(items) == 1
    exp_id = items[0]["id"]
    assert client.get(f"/api/experiments/{exp_id}").json()["n_examples"] == 4
    assert client.get("/api/experiments/999").status_code == 404


def test_upload_and_job_lifecycle(client, monkeypatch):
    # Avoid needing a real PDF: stub the extractor the background worker calls.
    from pls_ct.app.routers import jobs

    monkeypatch.setattr(jobs, "extract_text", lambda path: "extracted plain text")

    resp = client.post(
        "/api/uploads",
        files={"file": ("trial.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    job = client.get(f"/api/jobs/{job_id}").json()  # background task ran synchronously
    assert job["status"] == "succeeded"
    assert job["result"]["n_chars"] == len("extracted plain text")


def test_upload_rejects_non_pdf(client):
    resp = client.post("/api/uploads", files={"file": ("x.txt", b"hello", "text/plain")})
    assert resp.status_code == 415


def test_job_404(client):
    assert client.get("/api/jobs/999").status_code == 404


def test_unhandled_error_is_clean_500_without_leak(tmp_path):
    # A route that raises an unexpected error must return a generic 500, not a stack trace.
    from sqlalchemy import create_engine

    from pls_ct.app.main import create_app
    from pls_ct.db.engine import create_all

    engine = create_engine(f"sqlite:///{tmp_path / 'e.db'}", future=True)
    create_all(engine)
    app = create_app(engine=engine)

    @app.get("/api/_boom")
    def _boom():
        raise RuntimeError("secret internal detail")

    boom_client = TestClient(app, raise_server_exceptions=False)
    resp = boom_client.get("/api/_boom")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"] == "internal_error"
    assert "secret internal detail" not in resp.text
