
from flask import Blueprint, jsonify, session

from backend.auth import require_role
from backend.database import get_db


invoices_bp = Blueprint(
    "invoices",
    __name__,
    url_prefix="/api/invoices"
)


# VIEW INVOICES
@invoices_bp.get("")
@require_role("admin", "staff", "customer")
def list_invoices():

    db = get_db()

    user = db.execute(
        "SELECT role FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user is None:
        return jsonify({"error": "Account not found"}), 401

    if user["role"] == "customer":

        # Customers can see only invoices belonging to their account
        rows = db.execute(
            """SELECT invoices.id,
                      invoices.subscription_id,
                      invoices.invoice_number,
                      invoices.amount,
                      invoices.status,
                      invoices.due_date,
                      products.name AS product_name,
                      plans.name AS plan_name,
                      customers.id AS customer_id,
                      customers.name AS customer_name,
                      customers.email AS customer_email
               FROM invoices
               JOIN subscriptions
                   ON subscriptions.id = invoices.subscription_id
               JOIN plans
                   ON plans.id = subscriptions.plan_id
               JOIN products
                   ON products.id = plans.product_id
               JOIN customers
                   ON customers.id = subscriptions.customer_id
               WHERE customers.account_id = ?
               ORDER BY invoices.id DESC""",
            (session["user_id"],)
        ).fetchall()

    else:

        # Admin/staff can see invoices created under their account
        rows = db.execute(
            """SELECT invoices.id,
                      invoices.subscription_id,
                      invoices.invoice_number,
                      invoices.amount,
                      invoices.status,
                      invoices.due_date,
                      products.name AS product_name,
                      plans.name AS plan_name,
                      customers.id AS customer_id,
                      customers.name AS customer_name,
                      customers.email AS customer_email
               FROM invoices
               JOIN subscriptions
                   ON subscriptions.id = invoices.subscription_id
               JOIN plans
                   ON plans.id = subscriptions.plan_id
               JOIN products
                   ON products.id = plans.product_id
               LEFT JOIN customers
                   ON customers.id = subscriptions.customer_id
               WHERE invoices.user_id = ?
               ORDER BY invoices.id DESC""",
            (session["user_id"],)
        ).fetchall()

    return jsonify([dict(row) for row in rows])
