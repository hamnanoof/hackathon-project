from datetime import date

from flask import Blueprint, jsonify, request, session

from backend.auth import require_role
from backend.database import get_db


subscriptions_bp = Blueprint("subscriptions", __name__, url_prefix="/api/subscriptions")


@subscriptions_bp.get("")
@require_role("admin", "staff", "customer")
def list_subscriptions():
    db = get_db()

    user = db.execute(
        "SELECT role, email FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user["role"] == "customer":
        rows = db.execute(
            """SELECT subscriptions.id, subscriptions.status,
                      subscriptions.start_date,
                      plans.name AS plan_name, plans.price,
                      plans.billing_interval,
                      products.name AS product_name,
                      customers.name AS customer_name,
                      customers.email AS customer_email
               FROM subscriptions
               JOIN plans ON plans.id = subscriptions.plan_id
               JOIN products ON products.id = plans.product_id
               JOIN customers ON customers.id = subscriptions.customer_id
               WHERE customers.email = ?
               ORDER BY subscriptions.id DESC""",
            (user["email"],),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT subscriptions.id, subscriptions.status,
                      subscriptions.start_date,
                      plans.name AS plan_name, plans.price,
                      plans.billing_interval,
                      products.name AS product_name,
                      customers.name AS customer_name,
                      customers.email AS customer_email
               FROM subscriptions
               JOIN plans ON plans.id = subscriptions.plan_id
               JOIN products ON products.id = plans.product_id
               LEFT JOIN customers ON customers.id = subscriptions.customer_id
               WHERE subscriptions.user_id = ?
               ORDER BY subscriptions.id DESC""",
            (session["user_id"],),
        ).fetchall()

    return jsonify([dict(row) for row in rows])


@subscriptions_bp.post("")
@require_role("admin", "staff")
def create_subscription():
    data = request.get_json(silent=True) or {}

    try:
        plan_id = int(data.get("plan_id"))
        customer_id = int(data.get("customer_id")) if data.get("customer_id") else None
    except (TypeError, ValueError):
        return jsonify({"error": "A valid plan is required"}), 400

    db = get_db()

    plan = db.execute(
        """SELECT plans.* FROM plans
           JOIN products ON products.id = plans.product_id
           WHERE plans.id = ? AND products.user_id = ?""",
        (plan_id, session["user_id"]),
    ).fetchone()

    if plan is None:
        return jsonify({"error": "Plan not found"}), 404

    if customer_id:
        customer = db.execute(
            "SELECT id FROM customers WHERE id = ? AND user_id = ?",
            (customer_id, session["user_id"]),
        ).fetchone()

        if customer is None:
            return jsonify({"error": "Customer not found"}), 404

    started = date.today().isoformat()

    cursor = db.execute(
        """INSERT INTO subscriptions
           (user_id, plan_id, customer_id, status, start_date)
           VALUES (?, ?, ?, 'active', ?)""",
        (session["user_id"], plan_id, customer_id, started),
    )

    invoice_number = f"INV-{date.today():%Y%m%d}-{cursor.lastrowid:05d}"

    db.execute(
        """INSERT INTO invoices
           (user_id, subscription_id, invoice_number, amount, status, due_date)
           VALUES (?, ?, ?, ?, 'pending', ?)""",
        (session["user_id"], cursor.lastrowid, invoice_number,
         plan["price"], started),
    )

    db.commit()

    return jsonify({
        "id": cursor.lastrowid,
        "status": "active",
        "start_date": started
    }), 201


@subscriptions_bp.patch("/<int:subscription_id>")
@require_role("admin", "staff", "customer")
def update_subscription(subscription_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip().lower()

    if status not in {"active", "cancelled"}:
        return jsonify({"error": "Status must be active or cancelled"}), 400

    db = get_db()

    user = db.execute(
        "SELECT role, email FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user["role"] == "customer":
        if status != "cancelled":
            return jsonify({"error": "Customers can only cancel their own subscriptions"}), 403

        cursor = db.execute(
            """UPDATE subscriptions
               SET status = 'cancelled'
               WHERE id = ?
               AND customer_id IN (
                   SELECT id FROM customers WHERE email = ?
               )
               AND status = 'active'""",
            (subscription_id, user["email"]),
        )
    else:
        cursor = db.execute(
            """UPDATE subscriptions
               SET status = ?
               WHERE id = ? AND user_id = ?""",
            (status, subscription_id, session["user_id"]),
        )

    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Subscription not found"}), 404

    return jsonify({
        "id": subscription_id,
        "status": status
    })