# CURRENT_STATE.md

## Project

Argentourse

Personal finance / ledger application.

Stack:

Backend - FastAPI - PostgreSQL - SQLAlchemy 2.0 - Alembic - Pydantic
v2 - uv (package manager)

Frontend (planned) - React - Vite - TanStack Query

Money values stored as integer cents.

------------------------------------------------------------------------

# Backend Architecture

## Folder structure

server/ │ ├─ pyproject.toml ├─ uv.lock ├─ .env │ ├─ alembic/ │ └─ app/ │
├─ main.py │ ├─ core/ │ ├─ config.py │ └─ db.py │ ├─ models/ │ ├─
base.py │ ├─ user.py │ ├─ account.py │ ├─ category.py │ └─
transaction.py │ ├─ schemas/ │ ├─ user.py │ ├─ account.py │ ├─
category.py │ └─ transaction.py │ ├─ services/ │ ├─ base_service.py │ └─
account_service.py │ └─ api/ ├─ deps.py │ └─ v1/ ├─ api.py │ └─
endpoints/ └─ accounts.py

------------------------------------------------------------------------

# Database

Tables created through Alembic:

users accounts categories transactions alembic_version

Primary IDs are UUIDs.

Relationships:

User ├─ Accounts ├─ Categories └─ Transactions

Account └─ Transactions

Category └─ Transactions

Transactions store:

amount_cents transaction_date description account_id category_id user_id

Future plan:

transaction_kind transfer_group_id

for mirrored transfers.

------------------------------------------------------------------------

# Balance Strategy

Accounts contain:

current_balance_cents

But the ledger (transactions) is the source of truth.

Balance will be:

-   updated on writes
-   recomputable from ledger

Hybrid model for performance + integrity.

------------------------------------------------------------------------

# API

API versioning implemented:

/api/v1

Current endpoints:

POST /api/v1/accounts GET /api/v1/accounts GET
/api/v1/accounts/{account_id} PATCH /api/v1/accounts/{account_id} DELETE
/api/v1/accounts/{account_id}

Interactive docs:

/docs /redoc

------------------------------------------------------------------------

# Authentication (temporary)

Using dependency:

get_current_user()

Currently returns a demo user from DB.

Later this will become:

JWT auth Bearer tokens python-jose

------------------------------------------------------------------------

# Service Layer

Pattern:

routes → services → models → database

Services contain business logic.

Example:

account_service

Base CRUD utilities being added via:

BaseService

to reduce repeated DB operations.

------------------------------------------------------------------------

# Development Workflow

Environment:

uv pyproject.toml uv sync

Run server:

uv run uvicorn app.main:app --reload

Database migrations:

uv run alembic revision --autogenerate -m "message" uv run alembic
upgrade head

------------------------------------------------------------------------

# Next Development Steps

1.  Finalize BaseService
2.  Implement Category service + endpoints
3.  Implement Transaction service
4.  Implement Transfer endpoint
5.  Build Dashboard queries

Example future endpoints:

POST /api/v1/transfers GET /api/v1/dashboard/summary GET
/api/v1/dashboard/net-worth

------------------------------------------------------------------------

# Ledger Design

Transfers will be represented by two mirrored transactions.

Example:

Checking -10000 Savings +10000 transfer_group_id = same UUID

This preserves ledger balance and simplifies reporting.

------------------------------------------------------------------------

# Important Conventions

Money stored as:

int cents

Example:

\$178.60 → 17860

Never store floats.

------------------------------------------------------------------------

# Notes

Architecture intentionally resembles Flask app factory pattern but
implemented with FastAPI dependency injection.

Key concepts:

Depends() routers services schemas

------------------------------------------------------------------------

# End of Snapshot
