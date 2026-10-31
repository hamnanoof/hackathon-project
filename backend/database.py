
import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE_PATH"])
        db_path.parent.mkdir(parents=True, exist_ok=True)

        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(_error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def migrate_db(db):

    # Create customers table if it doesn't exist
    db.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, email)
        )
    """)

    # Check customer table columns
    customer_columns = [
        row["name"]
        for row in db.execute(
            "PRAGMA table_info(customers)"
        ).fetchall()
    ]

    # Add account_id if it doesn't exist
    if "account_id" not in customer_columns:
        db.execute("""
            ALTER TABLE customers
            ADD COLUMN account_id INTEGER
            REFERENCES users(id) ON DELETE SET NULL
        """)

    # Check subscription table columns
    subscription_columns = [
        row["name"]
        for row in db.execute(
            "PRAGMA table_info(subscriptions)"
        ).fetchall()
    ]

    # Add customer_id if it doesn't exist
    if "customer_id" not in subscription_columns:
        db.execute("""
            ALTER TABLE subscriptions
            ADD COLUMN customer_id INTEGER
            REFERENCES customers(id)
        """)

    # Create indexes
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_customers_user
        ON customers(user_id)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_customers_account
        ON customers(account_id)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscriptions_customer
        ON subscriptions(customer_id)
    """)


def init_db(app):
    app.teardown_appcontext(close_db)

    with app.app_context():
        db = get_db()

        # Initialize database schema
        schema_path = (
            Path(app.config["BASE_DIR"]) / "database" / "schema.sql"
        )

        db.executescript(
            schema_path.read_text(encoding="utf-8")
        )

        # Add role column if it doesn't exist
        user_columns = [
            row["name"]
            for row in db.execute(
                "PRAGMA table_info(users)"
            ).fetchall()
        ]

        if "role" not in user_columns:
            db.execute("""
                ALTER TABLE users
                ADD COLUMN role TEXT NOT NULL DEFAULT 'customer'
                CHECK (role IN ('admin', 'staff', 'customer'))
            """)

        # Run migrations
        migrate_db(db)

        db.commit()

