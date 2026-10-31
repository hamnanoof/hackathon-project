from flask import Blueprint, jsonify, session

from backend.auth import require_role
from backend.database import get_db


invoices_bp = Blueprint("invoices", __name__, url_prefix="/api/invoices")


@invoices_bp.get("")
@require_role("admin", "staff", "customer")
def list_invoices():
    db = get_db()

    user = db.execute(
        "SELECT role, email FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user["role"] == "customer":
        rows = db.execute(
            """SELECT invoices.id, invoices.invoice_number,
                      invoices.amount, invoices.status,
                      invoices.due_date,
                      products.name AS product_name,
                      plans.name AS plan_name,
                      customers.name AS customer_name,
                      customers.email AS customer_email
               FROM invoices
               JOIN subscriptions
                   ON subscriptions.id = invoices.subscription_id
               JOIN plans ON plans.id = subscriptions.plan_id
               JOIN products ON products.id = plans.product_id
               JOIN customers ON customers.id = subscriptions.customer_id
               WHERE customers.email = ?
               ORDER BY invoices.id DESC""",
            (user["email"],),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT invoices.id, invoices.invoice_number,
                      invoices.amount, invoices.status,
                      invoices.due_date,
                      products.name AS product_name,
                      plans.name AS plan_name,
                      customers.name AS customer_name,
                      customers.email AS customer_email
               FROM invoices
               JOIN subscriptions
                   ON subscriptions.id = invoices.subscription_id
               JOIN plans ON plans.id = subscriptions.plan_id
               JOIN products ON products.id = plans.product_id
               LEFT JOIN customers ON customers.id = subscriptions.customer_id
               WHERE invoices.user_id = ?
               ORDER BY invoices.id DESC""",
            (session["user_id"],),
        ).fetchall()

    return jsonify([dict(row) for row in rows])

