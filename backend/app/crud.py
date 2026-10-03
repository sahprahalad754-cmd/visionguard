from .database import SessionLocal, engine, Base
from .models import IncidentDB
from .incident import Incident

Base.metadata.create_all(bind=engine)  # table nahi hai toh bana dega


def save_incident(incident: Incident):
    db = SessionLocal()
    try:
        row = IncidentDB(
            id=incident.id,
            camera_id=incident.camera_id,
            incident_type=incident.incident_type,
            severity=incident.severity.value,
            confidence=incident.confidence,
            object_id=incident.object_id,
            timestamp=incident.timestamp,
            evidence_path=incident.evidence_path,
            status=incident.status.value,
        )
        db.add(row)
        db.commit()
        print(f"[DB] Saved incident {incident.id}")
    except Exception as e:
        db.rollback()
        print("[DB ERROR]", e)
    finally:
        db.close()