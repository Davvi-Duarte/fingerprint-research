import uuid
from datetime import datetime, timezone

from sqlalchemy.types import JSON

from .database import db


class FingerprintRecord(db.Model):
    __tablename__ = "fingerprint_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    participant_name = db.Column(db.Text, nullable=False)
    participant_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user_agent = db.Column(db.Text, nullable=True)
    library_name = db.Column(db.Text, nullable=True, default="FingerprintJS OSS")

    visitor_id = db.Column(db.Text, nullable=True)
    confidence = db.Column(JSON, nullable=True)
    components = db.Column(JSON, nullable=True)
    raw_result = db.Column(JSON, nullable=True)

    duration_total_ms = db.Column(db.Float, nullable=True)
    client_started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    client_finished_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ip_address_hash = db.Column(db.Text, nullable=True)

    def to_summary(self):
        """Resumo para listagem — sem dados brutos."""
        return {
            "id": self.id,
            "participant_name": self.participant_name,
            "participant_id": self.participant_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "library_name": self.library_name,
            "visitor_id": self.visitor_id,
            "duration_total_ms": self.duration_total_ms,
        }

    def to_full(self):
        """Exportação no formato final da pesquisa."""
        return {
        "participant_name": self.participant_name,
        "fingerprint_result": self.raw_result,
    }

    def to_export_row(self):
        """Exportação resumida — inclui nome mas sem components/raw_result."""
        return {
            "id": self.id,
            "participant_name": self.participant_name,
            "participant_id": self.participant_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "visitor_id": self.visitor_id,
            "duration_total_ms": self.duration_total_ms,
            "library_name": self.library_name,
        }
