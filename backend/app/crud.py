import os
import requests
from dotenv import load_dotenv

from .incident import Incident

load_dotenv()

# Local test ke liye default localhost. Deploy ke baad .env mein live URL daalna.
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "dev-key")

EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evidence")


def save_incident(incident: Incident):
    """Incident ko API ko bhejta hai (photo ke saath, agar hai)."""
    data = {
        "id": incident.id,
        "camera_id": incident.camera_id,
        "incident_type": incident.incident_type,
        "severity": incident.severity.value,
        "confidence": incident.confidence,
        "object_id": incident.object_id,
        "timestamp": incident.timestamp,
    }

    files = None
    photo_path = os.path.join(EVIDENCE_DIR, incident.evidence_path) if incident.evidence_path else ""
    if photo_path and os.path.exists(photo_path):
        files = {"photo": (incident.evidence_path, open(photo_path, "rb"), "image/jpeg")}

    try:
        res = requests.post(
            f"{API_URL}/api/incidents",
            data=data,
            files=files,
            headers={"X-API-Key": API_KEY},
            timeout=10,
        )
        if res.ok:
            print(f"[API] Saved incident {incident.id}")
        else:
            print(f"[API ERROR] {res.status_code}: {res.text}")
    except Exception as e:
        print("[API ERROR]", e)
    finally:
        if files:
            files["photo"][1].close()