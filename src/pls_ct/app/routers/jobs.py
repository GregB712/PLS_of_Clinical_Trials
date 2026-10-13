"""PDF upload -> persisted background preprocessing job, and job status."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from pls_ct.app.deps import get_session
from pls_ct.app.schemas import JobOut, UploadResponse
from pls_ct.config import Config
from pls_ct.db.models import Job

router = APIRouter(tags=["jobs"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


def _uploads_dir() -> Path:
    d = Config.from_env().processed_dir / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def extract_text(path: str) -> str:
    """Extract plain text from a PDF (pdfminer; base dependency). Monkeypatched in tests."""
    from pdfminer.high_level import extract_text as _pdf_extract

    return (_pdf_extract(path) or "").strip()


def run_preprocess(engine: Engine, job_id: int, path: str) -> None:
    """Background worker: convert the uploaded PDF to text and record the outcome."""
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = factory()
    try:
        job = session.get(Job, job_id)
        if job is None:
            return
        job.status = "running"
        session.commit()
        try:
            text = extract_text(path)
            warnings = [] if text else ["no selectable text (likely scanned; OCR not enabled)"]
            job.result = {"n_chars": len(text), "preview": text[:1000], "warnings": warnings}
            job.status = "succeeded"
        except Exception as exc:  # noqa: BLE001 - record failure on the job, don't crash the worker
            job.error = f"{type(exc).__name__}: {exc}"
            job.status = "failed"
        session.commit()
    finally:
        session.close()


@router.post("/uploads", response_model=UploadResponse, status_code=202)
async def upload(
    request: Request,
    background: BackgroundTasks,
    file: UploadFile,
    session: Session = Depends(get_session),
) -> UploadResponse:
    name = file.filename or ""
    if not (name.lower().endswith(".pdf") or file.content_type == "application/pdf"):
        raise HTTPException(status_code=415, detail="only PDF uploads are accepted")

    # Stream to disk with a hard size cap; a server-generated name prevents path traversal.
    dest = _uploads_dir() / f"{uuid.uuid4().hex}.pdf"
    size = 0
    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="file exceeds 20 MB limit")
            out.write(chunk)

    job = Job(kind="preprocess", status="queued", payload={"filename": name, "path": str(dest)})
    session.add(job)
    session.flush()
    job_id = job.id
    session.commit()

    background.add_task(run_preprocess, request.app.state.engine, job_id, str(dest))
    return UploadResponse(job_id=job_id, status="queued")


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, session: Session = Depends(get_session)) -> JobOut:
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"job {job_id} not found")
    return JobOut(id=job.id, kind=job.kind, status=job.status, result=job.result, error=job.error)
