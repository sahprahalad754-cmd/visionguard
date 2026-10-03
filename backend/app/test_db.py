from .incident import IncidentManager, Severity
from .crud import save_incident

manager = IncidentManager(cooldown_seconds=10)

inc = manager.create_incident("cam_01", "restricted_zone", Severity.HIGH, 0.91, object_id=1)
if inc:
    save_incident(inc)


