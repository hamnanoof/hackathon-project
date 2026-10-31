
import click
from flask import Flask, jsonify, send_from_directory, session

from backend import config
from backend.auth import auth_bp, require_auth
from backend.customers import customers_bp
from backend.database import init_db, get_db
from backend.errors import ApiError
from backend.invoices import invoices_bp
from backend.payments import payments_bp
from backend.products import products_bp
from backend.subscriptions import subscriptions_bp
from backend.seed import seed_customers


def create_app():

    app = Flask(__name__, static_folder=None)

    app.config.from_object(config)

    app.config["BASE_DIR"] = str(config.BASE_DIR)
    app.config["DATABASE_PATH"] = str(config.DATABASE_PATH)

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Initialize database
    init_db(app)

    # Global error handler for ApiError
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify(error.to_dict()), error.status_code

    # Register backend routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)

    # DASHBOARD API
    @app.get("/api/dashboard")
    @require_auth
    def dashboard():

        db = get_db()
        user_id = session["user_id"]

        user = db.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if user is None:
            session.clear()
            return jsonify({"error": "Account not found"}), 401

        role = user["role"]

        # ADMIN AND STAFF DASHBOARD
        if role in ("admin", "staff"):

            counts = db.execute(
                """SELECT

                    (SELECT COUNT(*)
                     FROM products
                     WHERE user_id = ?) AS products,

                    (SELECT COUNT(*)
                     FROM customers
                     WHERE user_id = ?) AS customers,

                    (SELECT COUNT(*)
                     FROM subscriptions
                     WHERE user_id = ?
                     AND status = 'active') AS active_subscriptions,

                    (SELECT COUNT(*)
                     FROM invoices
                     WHERE user_id = ?
                     AND status = 'pending') AS pending_invoices,

                    (SELECT COALESCE(SUM(amount), 0)
                     FROM payments
                     WHERE user_id = ?
                     AND status = 'completed') AS collected
                """,
                (
                    user_id,
                    user_id,
                    user_id,
                    user_id,
                    user_id
                )
            ).fetchone()

        # CUSTOMER DASHBOARD
        elif role == "customer":

            counts = db.execute(
                """SELECT

                    (SELECT COUNT(DISTINCT products.id)
                     FROM products
                     JOIN customers
                     ON customers.user_id = products.user_id
                     WHERE customers.account_id = ?
                    ) AS products,

                    (SELECT COUNT(*)
                     FROM subscriptions
                     JOIN customers
                     ON customers.id = subscriptions.customer_id
                     WHERE customers.account_id = ?
                     AND subscriptions.status = 'active'
                    ) AS active_subscriptions,

                    (SELECT COUNT(*)
                     FROM invoices
                     JOIN subscriptions
                     ON subscriptions.id = invoices.subscription_id
                     JOIN customers
                     ON customers.id = subscriptions.customer_id
                     WHERE customers.account_id = ?
                     AND invoices.status = 'pending'
                    ) AS pending_invoices,

                    (SELECT COALESCE(SUM(payments.amount), 0)
                     FROM payments
                     JOIN invoices
                     ON invoices.id = payments.invoice_id
                     JOIN subscriptions
                     ON subscriptions.id = invoices.subscription_id
                     JOIN customers
                     ON customers.id = subscriptions.customer_id
                     WHERE customers.account_id = ?
                     AND payments.status = 'completed'
                    ) AS collected
                """,
                (
                    user_id,
                    user_id,
                    user_id,
                    user_id
                )
            ).fetchone()

            return jsonify({
                "role": role,
                "customers": 0,
                **dict(counts)
            })

        else:

            return jsonify({
                "error": "Invalid account role"
            }), 403

        return jsonify({
            "role": role,
            **dict(counts)
        })

    # FRONTEND HOME PAGE
    @app.get("/")
    def index():

        return send_from_directory(
            config.FRONTEND_DIR,
            "index.html"
        )

    # FRONTEND STATIC FILES
    @app.get("/<path:filename>")
    def frontend_file(filename):

        return send_from_directory(
            config.FRONTEND_DIR,
            filename
        )

    return app


app = create_app()


# CLI command for seeding data
@app.cli.command()
@click.option('--customers', default=10, help='Number of customers to create')
def seed(customers):
    """Seed the database with demo data"""
    with app.app_context():
        seed_customers(customers)


if __name__ == "__main__":

    app.run(debug=True)
