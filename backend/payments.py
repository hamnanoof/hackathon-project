
import sqlite3

from flask import Blueprint, jsonify, request, session

from backend.auth import require_role
from backend.database import get_db


payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/api/payments"
)


# VIEW PAYMENTS
@payments_bp.get("")
@require_role("admin", "staff", "customer")
def list_payments():

    db = get_db()

    user = db.execute(
        "SELECT role FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user is None:
        session.clear()
        return jsonify({"error": "Account not found"}), 401

    if user["role"] == "customer":

        # Customers can view only their own payments
        rows = db.execute(
            """SELECT payments.id,
                      payments.invoice_id,
                      payments.amount,
                      payments.method,
                      payments.status,
                      payments.paid_at,
                      invoices.invoice_number
               FROM payments
               JOIN invoices
                   ON invoices.id = payments.invoice_id
               JOIN subscriptions
                   ON subscriptions.id = invoices.subscription_id
               JOIN customers
                   ON customers.id = subscriptions.customer_id
               WHERE customers.account_id = ?
               ORDER BY payments.id DESC""",
            (session["user_id"],)
        ).fetchall()

    else:

        # Admin/staff can view payments under their account
        rows = db.execute(
            """SELECT payments.id,
                      payments.invoice_id,
                      payments.amount,
                      payments.method,
                      payments.status,
                      payments.paid_at,
                      invoices.invoice_number
               FROM payments
               JOIN invoices
                   ON invoices.id = payments.invoice_id
               WHERE payments.user_id = ?
               ORDER BY payments.id DESC""",
            (session["user_id"],)
        ).fetchall()

    return jsonify([dict(row) for row in rows])


# RECORD PAYMENT
@payments_bp.post("")
@require_role("admin", "staff", "customer")
def record_payment():

    data = request.get_json(silent=True) or {}

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
        return jsonify({
            "error": "A valid invoice is required"
        }), 400

    # Validate payment method
    allowed_methods = {
        "card",
        "bank transfer",
        "cash"
    }

    if method not in allowed_methods:
        return jsonify({
            "error": "Payment method must be card, bank transfer, or cash"
        }), 400

    db = get_db()
    user_id = session["user_id"]

    user = db.execute(
        "SELECT role FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if user is None:
        session.clear()
        return jsonify({"error": "Account not found"}), 401

    try:

        # Start database transaction
        db.execute("BEGIN IMMEDIATE")

        # Find invoice according to logged-in user's role
        if user["role"] == "customer":

            invoice = db.execute(
                """SELECT invoices.id,
                          invoices.amount,
                          invoices.status,
                          invoices.user_id
                   FROM invoices
                   JOIN subscriptions
                       ON subscriptions.id = invoices.subscription_id
                   JOIN customers
                       ON customers.id = subscriptions.customer_id
                   WHERE invoices.id = ?
                   AND customers.account_id = ?""",
                (invoice_id, user_id)
            ).fetchone()

        else:

            invoice = db.execute(
                """SELECT id, amount, status, user_id
                   FROM invoices
                   WHERE id = ? AND user_id = ?""",
                (invoice_id, user_id)
            ).fetchone()

        # Check invoice ownership
        if invoice is None:
            db.rollback()
            return jsonify({
                "error": "Invoice not found"
            }), 404

        # Prevent duplicate payment
        if invoice["status"] == "paid":
            db.rollback()
            return jsonify({
                "error": "Invoice has already been paid"
            }), 409

        if invoice["status"] != "pending":
            db.rollback()
            return jsonify({
                "error": "Only pending invoices can be paid"
            }), 409

        # Record payment under the invoice owner's account
        cursor = db.execute(
            """INSERT INTO payments
               (user_id, invoice_id, amount, method, status)
               VALUES (?, ?, ?, ?, 'completed')""",
            (
                invoice["user_id"],
                invoice_id,
                invoice["amount"],
                method
            )
        )

        # Mark invoice as paid
        update = db.execute(
            """UPDATE invoices
               SET status = 'paid'
               WHERE id = ?
               AND user_id = ?
               AND status = 'pending'""",
            (invoice_id, invoice["user_id"])
        )

        if update.rowcount != 1:
            db.rollback()
            return jsonify({
                "error": "Invoice could not be updated"
            }), 409

        # Save both changes together
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


