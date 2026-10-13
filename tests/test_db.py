"""Tests for the persistence layer: schema, DAL, and idempotent upserts (in-memory SQLite)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from pls_ct.config import REPO_ROOT
from pls_ct.dataset.build import load_records as load_json
from pls_ct.db import repository
from pls_ct.db.engine import create_all
from pls_ct.db.models import Base

SAMPLE = REPO_ROOT / "data" / "sample" / "trials.json"


@pytest.fixture
def session():
    engine = create_engine("sqlite://", future=True)  # in-memory
    create_all(engine)
    with Session(engine, future=True) as s:
        yield s


def test_create_all_builds_schema():
    engine = create_engine("sqlite://", future=True)
    create_all(engine)
    assert {"trials", "documents", "sections"}.issubset(set(Base.metadata.tables))


def test_upsert_creates_then_unchanged(session):
    records = load_json(SAMPLE)
    rec = records[0]

    first = repository.upsert_trial(session, rec)
    session.commit()
    assert first == {"report": "created", "summary": "created"}

    # Re-upserting identical content is a no-op.
    second = repository.upsert_trial(session, rec)
    session.commit()
    assert second == {"report": "unchanged", "summary": "unchanged"}

    # No duplicate trial created.
    assert repository.count_trials(session) == 1


def test_upsert_updates_on_changed_content(session):
    records = load_json(SAMPLE)
    rec = records[0]
    repository.upsert_trial(session, rec)
    session.commit()

    changed = {**rec, "report_sections": {**rec["report_sections"], "Objectives": "DIFFERENT"}}
    outcome = repository.upsert_trial(session, changed)
    session.commit()
    assert outcome["report"] == "updated"
    assert outcome["summary"] == "unchanged"

    trial = repository.get_trial(session, rec["trial_name"])
    report_doc = next(d for d in trial.documents if d.kind == "report")
    objectives = next(s for s in report_doc.sections if s.name == "Objectives")
    assert objectives.text == "DIFFERENT"


def test_load_records_is_idempotent(session):
    records = load_json(SAMPLE)
    first = repository.load_records(session, records)
    session.commit()
    assert first["created"] == len(records) * 2  # report + summary per trial
    assert first["updated"] == 0

    second = repository.load_records(session, records)
    session.commit()
    assert second["unchanged"] == len(records) * 2
    assert second["created"] == 0
    assert repository.count_trials(session) == len(records)


def test_absent_document_recorded(session):
    rec = {"trial_name": "T1", "source": "synthetic", "report_sections": {"Objectives": "x"}}
    outcome = repository.upsert_trial(session, rec)
    session.commit()
    assert outcome == {"report": "created", "summary": "absent"}
