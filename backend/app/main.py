import logging
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from .models import IncidentDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visionguard")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="VisionGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_STATUS = {"OPEN", "ACKNOWLEDGED", "RESOLVED"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_dict(row: IncidentDB):
    return {
        "id": row.id,
        "camera_id": row.camera_id,
        "incident_type": row.incident_type,
        "severity": row.severity,
        "confidence": row.confidence,
        "object_id": row.object_id,
        "timestamp": row.timestamp,
        "evidence_path": row.evidence_path,
        "status": row.status,
    }


@app.get("/api/health")
def health():
    logger.info("Health check called")
    return {"status": "ok"}


@app.get("/api/incidents")
def list_incidents(
    camera_id: Optional[str] = None,
    incident_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(IncidentDB)
    if camera_id:
        q = q.filter(IncidentDB.camera_id == camera_id)
    if incident_type:
        q = q.filter(IncidentDB.incident_type == incident_type)
    if status:
        q = q.filter(IncidentDB.status == status.upper())
    rows = q.order_by(IncidentDB.timestamp.desc()).limit(limit).all()
    return [to_dict(r) for r in rows]


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    row = db.get(IncidentDB, incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return to_dict(row)


class StatusUpdate(BaseModel):
    status: str


@app.patch("/api/incidents/{incident_id}")
def update_status(incident_id: str, body: StatusUpdate, db: Session = Depends(get_db)):
    new_status = body.status.upper()
    if new_status not in VALID_STATUS:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(VALID_STATUS)}")
    row = db.get(IncidentDB, incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    row.status = new_status
    db.commit()
    return to_dict(row)