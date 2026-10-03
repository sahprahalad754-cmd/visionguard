import uuid, time
from sqlalchemy import Column, String, Float, Integer, Text
from .database import Base

class IncidentDB(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, index=True, nullable=False)
    incident_type = Column(String, index=True, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(Float)
    object_id = Column(Integer)
    timestamp = Column(Float, default=time.time, index=True)
    evidence_path = Column(Text, default="")
    status = Column(String, default="OPEN", index=True)