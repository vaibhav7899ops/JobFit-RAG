from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, func

from app.db.base import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    analysis_json = Column(JSON, nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
