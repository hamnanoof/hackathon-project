# Subscript — Subscription Management

A Flask and SQLite application for managing a subscription catalog, subscriptions, invoices, and recorded payments with role-based access control.

## Requirements

- Python 3.9+
- pip
- click (for CLI commands)

## Run locally

From the `subscription-management` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install click
$env:SECRET_KEY = "replace-this-with-a-long-random-value"
```

### Option 1: Start with demo data

```powershell
$env:FLASK_APP = "backend.app"
py -m flask seed --customers 50
py -m backend.app
```

This creates:
- Admin user: admin@example.com / Brightloop@2026
- Staff user: staff@example.com / Brightloop@2026
- 50 customer accounts (customer1@example.com through customer50@example.com)
- Products, plans, taxes, discounts, templates
- Subscriptions spread over the past year

### Option 2: Start without demo data

```powershell
py -m backend.app
```

**Note:** Public registration is disabled. The first user created in the database will be assigned the admin role. You can create additional accounts directly in the database or modify the registration endpoint as needed.

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The SQLite database is initialized automatically at `database/subscription.db`.

For a persistent secret, set `SECRET_KEY` in the environment before starting the server. `DATABASE_PATH` can optionally be set to use a different SQLite file.

## Features

- Role-based access control (admin, staff, customer)
- Customer management with account creation
- Per-account products and monthly/yearly/weekly plans
- Subscription creation and cancellation; new subscriptions automatically create an invoice
- Invoice listing and payment recording (this app records payments but does not process or charge real cards)
- Dashboard counts for products, customers, active subscriptions, pending invoices, and collected payments
- Server-side pagination for performance
- SQLite WAL mode for better concurrency

## API overview

All API routes are same-origin and application data routes require a logged-in session.

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/auth/login` | Start a session |
| POST | `/api/auth/logout` | End a session |
| GET | `/api/auth/me` | Get the current account |
| GET, POST | `/api/customers` | List or add customers (admin/staff only) |
| PATCH | `/api/customers/<id>` | Update customer (admin/staff only) |
| DELETE | `/api/customers/<id>` | Delete customer (admin/staff only) |
| GET, POST | `/api/products` | List or add products (admin/staff only) |
| DELETE | `/api/products/<id>` | Delete a product without dependent plans (admin/staff only) |
| GET, POST | `/api/plans` | List or add plans (admin/staff only) |
| DELETE | `/api/plans/<id>` | Delete a plan without subscriptions (admin/staff only) |
| GET, POST | `/api/subscriptions` | List or start subscriptions |
| PATCH | `/api/subscriptions/<id>` | Activate or cancel a subscription |
| GET | `/api/invoices` | List invoices |
| GET, POST | `/api/payments` | List or record payments |
| GET | `/api/dashboard` | Get workspace summary metrics |

JSON errors use an `error` field with the appropriate HTTP status. Passwords are never stored in plaintext.
