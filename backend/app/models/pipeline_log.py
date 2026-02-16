"""Pipeline execution log model."""
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class PipelineLog(Base):
    """Data pipeline execution log."""

    __tablename__ = "pipeline_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # running/success/failed/skipped
    steps_completed = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, default=7, nullable=False)
    error = Column(Text, nullable=True)
    trigger_type = Column(String(20), nullable=False)  # scheduled/manual

    def __repr__(self) -> str:
        return f"<PipelineLog {self.id} {self.status} {self.started_at}>"
