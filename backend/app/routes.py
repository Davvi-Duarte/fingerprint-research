import uuid
import csv
import hashlib
import io
import json
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from .database import db
from .models import FingerprintRecord
from .schemas import FingerprintSubmitSchema

bp = Blueprint("api", __name__)

submit_schema = FingerprintSubmitSchema()


def _hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()


def _parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Browser Fingerprint Research API is running."}), 200


@bp.route("/api/fingerprints", methods=["POST"])
def create_fingerprint():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    errors = submit_schema.validate(payload)
    if errors:
        return jsonify({"error": "Validation failed.", "details": errors}), 422

    data = submit_schema.load(payload)

    record = FingerprintRecord(
    participant_name=data["participant_name"],
    session_id=str(uuid.uuid4()),
    user_agent=request.headers.get("User-Agent"),
    library_name="FingerprintJS OSS",

    visitor_id=None,
    confidence=None,
    components=None,

    raw_result=data["fingerprint_result"],

    duration_total_ms=None,
    client_started_at=None,
    client_finished_at=None,
    ip_address_hash=_hash_ip(request.remote_addr),
)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "message": "Fingerprint recorded successfully. Thank you for participating.",
        "id": record.id,
        "participant_id": record.participant_id,
        "session_id": record.session_id,
        "created_at": record.created_at.isoformat(),
    }), 201


@bp.route("/api/fingerprints", methods=["GET"])
def list_fingerprints():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    pagination = FingerprintRecord.query.order_by(
        FingerprintRecord.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "records": [r.to_summary() for r in pagination.items],
    }), 200


@bp.route("/api/fingerprints/<int:record_id>", methods=["GET"])
def get_fingerprint(record_id):
    record = db.get_or_404(FingerprintRecord, record_id)
    return jsonify(record.to_summary()), 200


@bp.route("/api/fingerprints/<int:record_id>/raw", methods=["GET"])
def get_fingerprint_raw(record_id):
    if not current_app.config.get("ALLOW_RAW_EXPORT", False):
        return jsonify({
            "error": "Raw export is disabled. Set ALLOW_RAW_EXPORT=true to enable."
        }), 403

    record = db.get_or_404(FingerprintRecord, record_id)
    return jsonify(record.to_full()), 200


@bp.route("/api/export", methods=["GET"])
def export_fingerprints():
    include_raw = request.args.get("include_raw", "false").lower() == "true"
    fmt = request.args.get("format", "json").lower()

    if include_raw and not current_app.config.get("ALLOW_RAW_EXPORT", False):
        return jsonify({
            "error": "Raw export is disabled. Set ALLOW_RAW_EXPORT=true to enable include_raw."
        }), 403

    records = FingerprintRecord.query.order_by(FingerprintRecord.created_at.asc()).all()

    if include_raw:
        # Exportação completa: inclui participant_name, todos os componentes e raw_result
        rows = [r.to_full() for r in records]
    else:
        # Exportação resumida: inclui participant_name mas sem dados brutos
        rows = [r.to_export_row() for r in records]

    if fmt == "csv":
        if not rows:
            return "", 204

        # Para CSV com include_raw, components e raw_result são serializados como string JSON
        # pois CSV não suporta estruturas aninhadas nativamente
        csv_rows = []
        for row in rows:
            flat = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    flat[k] = json.dumps(v, ensure_ascii=False)
                else:
                    flat[k] = v
            csv_rows.append(flat)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=csv_rows[0].keys())
        writer.writeheader()
        writer.writerows(csv_rows)
        csv_data = output.getvalue()

        from flask import Response
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=fingerprints_export.csv"},
        )

    return jsonify({"total": len(rows), "records": rows}), 200
