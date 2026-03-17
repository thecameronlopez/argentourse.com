# CURRENT_STATE.md

## Project

Argentourse

Personal finance / ledger application.

Stack:

Backend - FastAPI - PostgreSQL - SQLAlchemy 2.0 - Alembic - Pydantic
v2 - uv (package manager)

Frontend - React - Vite - TypeScript - TanStack Query - TanStack
Router - Axios - Tailwind (optional)

Money values stored as integer cents.

------------------------------------------------------------------------

# Repository Structure

argentourse/ │ ├─ server/ (FastAPI backend) │ └─ web/ (React frontend)

------------------------------------------------------------------------

# Backend Architecture

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

# Frontend Setup

Frontend lives in:

web/

Create project:

npm create vite@latest web

Choose:

React TypeScript

Install dependencies:

npm install

Core libraries:

npm install @tanstack/react-query npm install @tanstack/react-router npm
install axios

Optional UI stack:

npm install tailwindcss postcss autoprefixer

------------------------------------------------------------------------

# Frontend Structure

web/ │ ├─ src/ │ │ │ ├─ main.tsx │ ├─ App.tsx │ │ │ ├─ api/ │ │
client.ts │ │ │ ├─ routes/ │ │ index.tsx │ │ accounts.tsx │ │ │ ├─
features/ │ │ accounts/ │ │ AccountsPage.tsx │ │ useAccounts.ts │ │ │ ├─
components/ │ │ │ └─ types/ │ └─ vite.config.ts

Conceptual structure mirrors backend:

routes → pages features → domain logic api → backend communication

------------------------------------------------------------------------

# Frontend Data Flow

React Query handles API state.

Example flow:

component → hook → API → backend

Example:

useAccounts()

calls

GET /api/v1/accounts

------------------------------------------------------------------------

# Frontend Dev Workflow

Run backend:

uv run uvicorn app.main:app --reload

Run frontend:

npm run dev

Frontend:

http://localhost:5173

Backend:

http://localhost:8000

Later Vite proxy will forward API requests.

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

# End of Snapshot
