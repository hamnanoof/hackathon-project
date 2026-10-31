from flask import Blueprint, jsonify, request, session

from backend.auth import require_auth
from backend.database import get_db


payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")


@payments_bp.get("")
@require_auth
def list_payments():
    rows = get_db().execute(
        """SELECT payments.id, payments.amount, payments.method, payments.status,
                  payments.paid_at, invoices.invoice_number
           FROM payments JOIN invoices ON invoices.id = payments.invoice_id
           WHERE payments.user_id = ? ORDER BY payments.id DESC""",
        (session["user_id"],),
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@payments_bp.post("")
@require_auth
def record_payment():
    data = request.get_json(silent=True) or {}
    method = str(data.get("method", "")).strip().lower()
    try:
        invoice_id = int(data.get("invoice_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "A valid invoice is required"}), 400
    if method not in {"card", "bank transfer", "cash"}:
        return jsonify({"error": "Payment method must be card, bank transfer, or cash"}), 400
    db = get_db()
    invoice = db.execute(
        "SELECT id, amount, status FROM invoices WHERE id = ? AND user_id = ?",
        (invoice_id, session["user_id"]),
    ).fetchone()
    if invoice is None:
        return jsonify({"error": "Invoice not found"}), 404
    if invoice["status"] == "paid":
        return jsonify({"error": "Invoice has already been paid"}), 409
    cursor = db.execute(
        """INSERT INTO payments (user_id, invoice_id, amount, method, status)
           VALUES (?, ?, ?, ?, 'completed')""",
        (session["user_id"], invoice_id, invoice["amount"], method),
    )
    db.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (invoice_id,))
    db.commit()
    return jsonify({"id": cursor.lastrowid, "invoice_id": invoice_id, "status": "completed"}), 201

