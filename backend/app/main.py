import logging
import os
import uuid
from typing import Optional

from fastapi import (
    FastAPI, Depends, HTTPException, Query, Header,
    UploadFile, File, Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import SessionLocal, engine, Base
from .models import IncidentDB

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visionguard")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="VisionGuard API")

# CORS: comma separated origins, e.g. "http://localhost:5173,https://myapp.vercel.app"
origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key: detection script isse incident bhejegi
API_KEY = os.getenv("API_KEY", "dev-key")

# Evidence photos folder
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)
app.mount("/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")

VALID_STATUS = {"OPEN", "ACKNOWLEDGED", "RESOLVED"}
VALID_SEVERITY = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_key(x_api_key: Optional[str] = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


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


@app.post("/api/incidents", dependencies=[Depends(check_key)])
async def create_incident(
    id: str = Form(...),
    camera_id: str = Form(...),
    incident_type: str = Form(...),
    severity: str = Form(...),
    confidence: float = Form(...),
    object_id: int = Form(...),
    timestamp: float = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    severity = severity.upper()
    if severity not in VALID_SEVERITY:
        raise HTTPException(status_code=400, detail="Invalid severity")

    filename = ""
    if photo is not None:
        filename = f"{uuid.uuid4()}.jpg"
        data = await photo.read()
        with open(os.path.join(EVIDENCE_DIR, filename), "wb") as f:
            f.write(data)

    row = IncidentDB(
        id=id,
        camera_id=camera_id,
        incident_type=incident_type,
        severity=severity,
        confidence=confidence,
        object_id=object_id,
        timestamp=timestamp,
        evidence_path=filename,
        status="OPEN",
    )
    db.add(row)
    db.commit()
    return to_dict(row)


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    row = db.get(IncidentDB, incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return to_dict(row)


class StatusUpdate(BaseModel):
    status: str


@app.patch("/api/incidents/{incident_id}", dependencies=[Depends(check_key)])
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