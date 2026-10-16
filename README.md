# Personal Finance & Expense Analytics (backend)

Backend only; the frontend is built by another team against the NestJS API.

```
 frontend ──► NestJS :3000 (auth, transactions, budgets, reports)
                  │  writes + reads                      ▲ HTTP (AiService)
                  ▼                                      │
             PostgreSQL ◄── reads only ── FastAPI :8000 (categorisation, anomalies, predictions)
```

| Folder | What it is |
|---|---|
| `nestjs/` | The public API. JWT login, transactions, monthly budgets, reports, and proxy endpoints for the analytics. Swagger at http://localhost:3000/docs |
| `fastapi/` | Internal analytics service. Never exposed to the frontend; NestJS calls it and passes the logged-in user's id. Docs at http://127.0.0.1:8000/docs |
| `docker-compose.yml` | Optional local PostgreSQL that matches the `.env.example` files |

The frontend team only needs the NestJS URL and the Swagger page. Do not expose port 8000 publicly (FastAPI has no login).

## Run it (first time)

You need Node 20.11+, Python 3.10+ and PostgreSQL (or `docker compose up -d` for one).

**1. Environment files** (copy each `.env.example` to `.env`; `DATABASE_URL` must be identical in both, and set a real `JWT_SECRET` in `nestjs/.env`)

**2. NestJS** (PowerShell; use `npm` instead of `npm.cmd` on Mac/Linux)
```powershell
cd nestjs
npm.cmd install
npm.cmd run db:setup        # creates the tables and the shared categories
npm.cmd run start:dev       # http://localhost:3000/docs
```

**3. FastAPI** (second terminal)
```powershell
cd fastapi
python -m venv venv
venv\Scripts\activate       # Mac/Linux: source venv/bin/activate
.\venv\Scripts\python.exe -m pip install -r requirements.txt
python -m uvicorn main:app --reload        # http://127.0.0.1:8000/docs
```

**4. Use real Swagger example values** at http://127.0.0.1:8000/docs: execute `GET /demo/examples` first. It returns the actual seeded demo user UUID, existing transactions, categories, and ready-to-copy payloads for the analytics routes. This is read-only and uses the shared PostgreSQL database. Then check NestJS at http://localhost:3000/docs: `POST /auth/login` with `demo@example.com` / `Demo@1234`, click Authorize with the token, and try `GET /ai/predict`, `GET /ai/anomalies` and `GET /reports/monthly`. `GET http://127.0.0.1:8000/health` confirms FastAPI can reach the database.

## What covers which requirement

| Requirement | Where |
|---|---|
| Authentication | NestJS `POST /auth/register`, `/auth/login` |
| Categories | NestJS `POST /categories` creates a user-owned category; `GET /categories` lists shared and personal categories |
| Transactions | NestJS `/transactions` CRUD with filters and paging; a missing category is filled in by FastAPI |
| Budgets | NestJS `/budgets` plus `/budgets/usage` (spent vs budget per category) |
| Reports | NestJS `/reports/monthly`, `/reports/trends` |
| Spending predictions | FastAPI `/ai/predict-spending`, exposed as NestJS `GET /ai/predict` |
| Categorisation | FastAPI `/ai/categorize-transaction`, exposed as NestJS `POST /ai/categorize` |
| Anomaly detection | FastAPI `/ai/detect-anomaly`, exposed as NestJS `GET /ai/anomalies`; includes severity and explanation |
| Analytics summary | FastAPI `GET /analytics/summary?user_id=...` combines forecast and anomaly summary (internal service) |
| PostgreSQL | One database; Prisma (NestJS) owns the schema, FastAPI reads the same tables |

## Tests

```powershell
cd fastapi; python -m unittest discover -s tests -v       # analysis logic; HTTP tests skip unless the DB is up and seeded
```

## Things to know

- Prisma `db push` is for a fresh local database. If the team shares one database, agree on one schema owner first.
- FastAPI errors (including "user not found") reach the frontend as a generic 503/502/404 from NestJS.
- Predictions are an average of the last 3 completed months; with old demo data pass `asOf` (e.g. `2026-05-01`).

## Shared authentication for FastAPI

FastAPI uses the same `JWT_SECRET` as NestJS and requires a valid NestJS login token for analytics and Swagger executions. Set matching `JWT_SECRET` and `FASTAPI_INTERNAL_API_KEY` values in `nestjs/.env` and `fastapi/.env`. Sign in using `POST /auth/login` in NestJS Swagger, then click **Authorize** in FastAPI Swagger and paste the returned `accessToken`. FastAPI rejects requests for a `userId` other than the authenticated user's ID. The `FASTAPI_INTERNAL_API_KEY` is only for protected NestJS-to-FastAPI server calls; keep it secret and never place it in frontend code.
