import uuid
import time
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


@dataclass
class Incident:
    camera_id: str
    incident_type: str          # e.g. "restricted_zone", "fall_detected", "no_helmet"
    severity: Severity
    confidence: float
    object_id: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    evidence_path: str = ""
    status: IncidentStatus = IncidentStatus.OPEN

    def to_dict(self):
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "incident_type": self.incident_type,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "object_id": self.object_id,
            "timestamp": self.timestamp,
            "evidence_path": self.evidence_path,
            "status": self.status.value,
        }


class IncidentManager:
    """
    Manages incident creation with cooldown to prevent duplicate
    incidents from being created every frame for the same object.
    """

    def __init__(self, cooldown_seconds: float = 10.0):
        self.cooldown_seconds = cooldown_seconds
        self.incidents: list[Incident] = []
        # key: (camera_id, incident_type, object_id) -> last incident timestamp
        self._last_incident_time: dict[tuple, float] = {}

    def _cooldown_key(self, camera_id, incident_type, object_id):
        return (camera_id, incident_type, object_id)

    def can_create_incident(self, camera_id, incident_type, object_id) -> bool:
        key = self._cooldown_key(camera_id, incident_type, object_id)
        last_time = self._last_incident_time.get(key)
        if last_time is None:
            return True
        return (time.time() - last_time) >= self.cooldown_seconds

    def create_incident(self, camera_id, incident_type, severity, confidence,
                         object_id, evidence_path=""):
        if not self.can_create_incident(camera_id, incident_type, object_id):
            return None  # still in cooldown, skip

        incident = Incident(
            camera_id=camera_id,
            incident_type=incident_type,
            severity=severity,
            confidence=confidence,
            object_id=object_id,
            evidence_path=evidence_path,
        )
        self.incidents.append(incident)

        key = self._cooldown_key(camera_id, incident_type, object_id)
        self._last_incident_time[key] = time.time()

        return incident

    def get_all_incidents(self):
        return [i.to_dict() for i in self.incidents]


if __name__ == "__main__":
    # Quick test to verify the debounce logic works
    manager = IncidentManager(cooldown_seconds=5)

    print("Attempt 1:")
    inc1 = manager.create_incident("cam_01", "restricted_zone", Severity.HIGH, 0.85, object_id=3)
    print(inc1.to_dict() if inc1 else "Skipped (cooldown)")

    print("\nAttempt 2 (immediately after, should be skipped):")
    inc2 = manager.create_incident("cam_01", "restricted_zone", Severity.HIGH, 0.90, object_id=3)
    print(inc2.to_dict() if inc2 else "Skipped (cooldown)")

    print("\nAttempt 3 (different object_id, should succeed):")
    inc3 = manager.create_incident("cam_01", "restricted_zone", Severity.HIGH, 0.80, object_id=7)
    print(inc3.to_dict() if inc3 else "Skipped (cooldown)")

    print(f"\nTotal incidents stored: {len(manager.get_all_incidents())}")