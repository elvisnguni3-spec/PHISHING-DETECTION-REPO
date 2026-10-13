from sqlalchemy import Column, Integer, String, Float, DateTime, func

from app.database.base import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    scan_id = Column(Integer, primary_key=True, index=True)

    input = Column(String, nullable=False)
    verdict = Column(String(20), nullable=False)
    confidence = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
