
import sqlite3

from flask import Blueprint, jsonify, request, session

from backend.auth import require_auth
from backend.database import get_db


payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")


# Get all payments belonging to the logged-in user
@payments_bp.get("")
@require_auth
def list_payments():

    rows = get_db().execute(
        """SELECT payments.id, payments.amount, payments.method,
                  payments.status, payments.paid_at,
                  invoices.invoice_number
           FROM payments
           JOIN invoices
           ON invoices.id = payments.invoice_id
           AND invoices.user_id = payments.user_id
           WHERE payments.user_id = ?
           ORDER BY payments.id DESC""",
        (session["user_id"],),
    ).fetchall()

    return jsonify([dict(row) for row in rows])


# Record a payment for an invoice
@payments_bp.post("")
@require_auth
def record_payment():

    data = request.get_json(silent=True)

    # Validate request data
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request data"}), 400

    method = str(data.get("method", "")).strip().lower()

    # Validate invoice ID
    try:
        raw_invoice_id = data.get("invoice_id")

        if isinstance(raw_invoice_id, bool):
            raise ValueError

        invoice_id = int(raw_invoice_id)

        if invoice_id <= 0:
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({"error": "A valid invoice is required"}), 400

    # Validate payment method
    allowed_methods = {"card", "bank transfer", "cash"}

    if method not in allowed_methods:
        return jsonify({
            "error": "Payment method must be card, bank transfer, or cash"
        }), 400

    db = get_db()
    user_id = session["user_id"]

    try:
        # Start a transaction to prevent partial updates
        db.execute("BEGIN IMMEDIATE")

        # Find invoice belonging to the logged-in user
        invoice = db.execute(
            """SELECT id, amount, status
               FROM invoices
               WHERE id = ? AND user_id = ?""",
            (invoice_id, user_id),
        ).fetchone()

        if invoice is None:
            db.rollback()
            return jsonify({"error": "Invoice not found"}), 404

        # Prevent payment of an already paid invoice
        if invoice["status"] == "paid":
            db.rollback()
            return jsonify({
                "error": "Invoice has already been paid"
            }), 409

        # Record payment
        cursor = db.execute(
            """INSERT INTO payments
               (user_id, invoice_id, amount, method, status)
               VALUES (?, ?, ?, ?, 'completed')""",
            (user_id, invoice_id, invoice["amount"], method),
        )

        # Update invoice status
        update = db.execute(
            """UPDATE invoices
               SET status = 'paid'
               WHERE id = ? AND user_id = ? AND status = 'pending'""",
            (invoice_id, user_id),
        )

        # Ensure invoice was updated successfully
        if update.rowcount != 1:
            db.rollback()
            return jsonify({
                "error": "Invoice could not be updated"
            }), 409

        # Save both operations together
        db.commit()

        return jsonify({
            "id": cursor.lastrowid,
            "invoice_id": invoice_id,
            "status": "completed",
            "message": "Payment recorded successfully"
        }), 201

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({
            "error": "Payment already exists or violates a database constraint"
        }), 409

    except Exception:
        db.rollback()
        raise
