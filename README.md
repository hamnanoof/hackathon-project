# Subscript — Subscription Management

A small Flask and SQLite application for managing a subscription catalog, subscriptions, invoices, and recorded payments.

## Requirements

- Python 3.9+
- pip

## Run locally

From the `subscription-management` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:SECRET_KEY = "replace-this-with-a-long-random-value"
python -m backend.app
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000), create an account, and use the sidebar to manage the workspace. The SQLite database is initialized automatically at `database/subscription.db`.

For a persistent secret, set `SECRET_KEY` in the environment before starting the server. `DATABASE_PATH` can optionally be set to use a different SQLite file.

## Features

- Account registration, login, and logout using secure password hashes and an HTTP-only session cookie
- Per-account products and monthly/yearly plans
- Subscription creation and cancellation; new subscriptions automatically create an invoice
- Invoice listing and payment recording (this app records payments but does not process or charge real cards)
- Dashboard counts for products, active subscriptions, pending invoices, and collected payments

## API overview

All API routes are same-origin and application data routes require a logged-in session.

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create an account |
| POST | `/api/auth/login` | Start a session |
| POST | `/api/auth/logout` | End a session |
| GET | `/api/auth/me` | Get the current account |
| GET, POST | `/api/products` | List or add products |
| DELETE | `/api/products/<id>` | Delete a product without dependent plans |
| GET, POST | `/api/plans` | List or add plans |
| DELETE | `/api/plans/<id>` | Delete a plan without subscriptions |
| GET, POST | `/api/subscriptions` | List or start subscriptions |
| PATCH | `/api/subscriptions/<id>` | Activate or cancel a subscription |
| GET | `/api/invoices` | List invoices |
| GET, POST | `/api/payments` | List or record payments |
| GET | `/api/dashboard` | Get workspace summary metrics |

JSON errors use an `error` field with an appropriate HTTP status. Passwords are never stored in plaintext.
