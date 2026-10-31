import random
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash
from backend.database import get_db


def seed_customers(N):
    """Seed N customers with subscriptions spread over the past year"""
    db = get_db()

    # Create admin user
    db.execute(
        """INSERT INTO users (name, email, password_hash, role)
           VALUES (?, ?, ?, 'admin')""",
        ("Admin User", "admin@example.com", generate_password_hash("Brightloop@2026"))
    )

    # Create staff user
    db.execute(
        """INSERT INTO users (name, email, password_hash, role)
           VALUES (?, ?, ?, 'staff')""",
        ("Staff User", "staff@example.com", generate_password_hash("Brightloop@2026"))
    )

    # Create GST taxes
    db.execute(
        """INSERT INTO taxes (user_id, name, rate)
           VALUES (?, ?, ?)""",
        (1, "GST 18%", 18.0)
    )
    db.execute(
        """INSERT INTO taxes (user_id, name, rate)
           VALUES (?, ?, ?)""",
        (1, "GST 5%", 5.0)
    )

    # Create products
    db.execute(
        """INSERT INTO products (user_id, name, description)
           VALUES (?, ?, ?)""",
        (1, "ERP System", "Enterprise Resource Planning software")
    )
    db.execute(
        """INSERT INTO products (user_id, name, description)
           VALUES (?, ?, ?)""",
        (1, "CRM Software", "Customer Relationship Management")
    )
    db.execute(
        """INSERT INTO products (user_id, name, description)
           VALUES (?, ?, ?)""",
        (1, "HR Management", "Human Resources Management System")
    )
    db.execute(
        """INSERT INTO products (user_id, name, description)
           VALUES (?, ?, ?)""",
        (1, "Project Management", "Project and Task Management Tool")
    )

    # Create plans with variants
    db.execute(
        """INSERT INTO plans (product_id, name, price, billing_interval)
           VALUES (?, ?, ?, ?)""",
        (1, "Basic ERP", 5000, "month")
    )
    db.execute(
        """INSERT INTO plans (product_id, name, price, billing_interval)
           VALUES (?, ?, ?, ?)""",
        (1, "Odoo Variant", 560, "month")
    )
    db.execute(
        """INSERT INTO plans (product_id, name, price, billing_interval)
           VALUES (?, ?, ?, ?)""",
        (1, "SAP Variant", 900, "month")
    )
    db.execute(
        """INSERT INTO plans (product_id, name, price, billing_interval)
           VALUES (?, ?, ?, ?)""",
        (2, "CRM Basic", 3000, "month")
    )
    db.execute(
        """INSERT INTO plans (product_id, name, price, billing_interval)
           VALUES (?, ?, ?, ?)""",
        (2, "CRM Pro", 5000, "year")
    )
    db.execute(
        """INSERT INTO plans (product_id, name, price, billing_interval)
           VALUES (?, ?, ?, ?)""",
        (3, "HR Basic", 2000, "month")
    )
    db.execute(
        """INSERT INTO plans (product_id, name, price, billing_interval)
           VALUES (?, ?, ?, ?)""",
        (4, "PM Basic", 1500, "week")
    )

    # Create discounts
    db.execute(
        """INSERT INTO discounts (user_id, name, type, value)
           VALUES (?, ?, ?, ?)""",
        (1, "Early Bird", "percentage", 10.0)
    )
    db.execute(
        """INSERT INTO discounts (user_id, name, type, value)
           VALUES (?, ?, ?, ?)""",
        (1, "Annual Discount", "fixed", 1000.0)
    )

    # Create quotation template
    db.execute(
        """INSERT INTO templates (user_id, name, data)
           VALUES (?, ?, ?)""",
        (1, "Standard Quotation", '{"template": "standard"}')
    )

    # Create N customers
    for i in range(N):
        name = f"Customer {i+1}"
        email = f"customer{i+1}@example.com"

        # Create customer user
        user_cursor = db.execute(
            """INSERT INTO users (name, email, password_hash, role)
               VALUES (?, ?, ?, 'customer')""",
            (name, email, generate_password_hash("Brightloop@2026"))
        )

        account_id = user_cursor.lastrowid

        # Create customer record
        customer_cursor = db.execute(
            """INSERT INTO customers (user_id, account_id, name, email, phone, address)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (1, account_id, name, email, f"+123456789{i:03d}", f"{i+1} Main Street, City")
        )

        customer_id = customer_cursor.lastrowid

        # Create random subscriptions spread over the past year
        num_subscriptions = random.randint(1, 3)
        for _ in range(num_subscriptions):
            plan_id = random.randint(1, 7)
            start_date = datetime.now() - timedelta(days=random.randint(1, 365))

            sub_cursor = db.execute(
                """INSERT INTO subscriptions (user_id, plan_id, customer_id, status, start_date, next_invoice_date)
                   VALUES (?, ?, ?, 'active', ?, ?)""",
                (1, plan_id, customer_id, start_date.isoformat(), (start_date + timedelta(days=30)).isoformat())
            )

            subscription_id = sub_cursor.lastrowid

            # Create invoice
            plan = db.execute("SELECT price FROM plans WHERE id = ?", (plan_id,)).fetchone()
            invoice_number = f"INV-{start_date:%Y%m%d}-{subscription_id:05d}"

            inv_cursor = db.execute(
                """INSERT INTO invoices (user_id, subscription_id, invoice_number, amount, status, due_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (1, subscription_id, invoice_number, plan["price"], "paid", start_date.isoformat())
            )

            invoice_id = inv_cursor.lastrowid

            # Record payment (80% chance of being paid)
            if random.random() < 0.8:
                db.execute(
                    """INSERT INTO payments (user_id, invoice_id, amount, method, status, paid_at)
                       VALUES (?, ?, ?, 'card', 'completed', ?)""",
                    (1, invoice_id, plan["price"], start_date.isoformat())
                )
            else:
                # Leave some overdue
                db.execute(
                    """UPDATE invoices SET status = 'overdue' WHERE id = ?""",
                    (invoice_id,)
                )

    db.commit()
    print(f"Seeded {N} customers successfully")
