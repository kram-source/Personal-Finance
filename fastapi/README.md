# FastAPI Personal Finance Analytics

## Run locally (Windows PowerShell)

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with the same JWT_SECRET as NestJS and your PostgreSQL DATABASE_URL
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

Swagger docs: http://127.0.0.1:8000/docs . The service is read-only against the shared Prisma/PostgreSQL database; NestJS remains the canonical writer.

## Code layout

- `main.py`: Uvicorn entrypoint.
- `src/api/application.py`: app configuration, authentication middleware, exception handling, and router registration.
- `src/api/routes/`: one router per feature.
- `src/api/schemas.py`: shared Pydantic request/response models.
- `src/api/dependencies.py`: shared database access and feature adapters.
- `src/core/`: environment configuration and JWT validation.
- `src/services/`: analytics algorithms and data operations.

Never commit `.env`. Do not expose `FASTAPI_INTERNAL_API_KEY` to browser clients.

---

# Personal Finance & Expense Analytics: FastAPI service

Spending **prediction**, **categorization** and **anomaly detection**.
FastAPI only **reads** from the PostgreSQL database; NestJS/Prisma owns the schema and all writes, including the one canonical seed.

It uses the **same database and tables as the NestJS app** (Prisma tables `"User"`, `"Category"`,
`"Transaction"`) and talks to it over the routes NestJS's `AiService` already calls.

## Endpoints

| NestJS `AiService` calls (POST) | Same thing, task-list route | What it does |
|---|---|---|
| `/ai/categorize-transaction` | `POST /categorize` | description/optional merchant to category name (+ `categoryId` if `userId` is sent), with rule-based confidence |
| `/ai/detect-anomaly` | `GET /anomalies?user_id=` | expenses above a configurable multiple of the median peer transaction in their category |
| `/ai/predict-spending` | `GET /predict?user_id=` | next estimate per category = average of the last 3 completed months |
| — | `GET /analytics/summary?user_id=` | forecast, budget comparison, anomalies, duplicate candidates, and insights |
| — | `GET /analytics/insights?user_id=` | month-to-date spending vs the same elapsed period last month |
| — | `GET /duplicates?user_id=` | possible duplicate expenses (review only; never deletes) |

Also: `GET /health` (checks the API and the database). Interactive docs: http://127.0.0.1:8000/docs

JSON uses **camelCase** (`userId`, `categoryId`) like the NestJS API. User ids are **UUID strings**.
Database anomaly detection, duplicate review, forecasting, and spending insights analyse only `EXPENSE`
transactions; the categorizer also supports `INCOME`. An unknown user returns **404**; a user with no
expenses returns an empty list.

### Examples

```jsonc
// POST /ai/categorize-transaction
{ "description": "Uber ride to airport", "type": "EXPENSE", "userId": "<uuid>" }
// ->
{ "description": "Uber ride to airport", "type": "EXPENSE", "category": "Transport",
  "categoryId": "<uuid of the Transport category>", "matchedKeyword": "uber", "confidence": 0.9 }

// POST /ai/detect-anomaly   { "userId": "<uuid>", "multiplier": 2 }   (multiplier optional)
{ "userId": "<uuid>", "multiplier": 2.0, "anomalies": [
  { "transactionId": "<uuid>", "description": "Weekend trip flights", "category": "Transport",
    "categoryId": "<uuid>", "amount": 1250.0, "date": "2026-04-15",
    "categoryAverage": 82.35, "timesAverage": 15.18, "severity": "high",
    "reason": "This transport expense is 15.2x the average baseline (median of other transport transactions)." } ] }

// POST /ai/predict-spending   { "userId": "<uuid>", "months": 3, "asOf": "2026-05-01" }   (months, asOf optional)
{ "userId": "<uuid>", "year": 2026, "month": 10, "totalPredicted": 1071.43,
  "basedOn": { "start": "2026-07-01", "end": "2026-09-30", "months": 3 },
  "predictions": [ { "category": "Food", "categoryId": "<uuid>", "predictedAmount": 345.74 } ] }
```

## Setup

1. Python 3.10+ and PostgreSQL.
2. Virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate          # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` (the `DATABASE_URL` must be the **same one the NestJS `.env` uses**).

## Run the whole project (order matters)

Use NestJS/Prisma as the single owner of the schema and demo seed. FastAPI is read-only.

```powershell
# 1. First terminal: from the nestjs/ folder
npm.cmd install
npm.cmd run db:setup       # fresh local database only: generate client, db push, seed
npm.cmd run start:dev      # http://localhost:3000

# 2. Second terminal: from the fastapi/ folder
python -m venv venv
venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
fastapi dev main.py        # http://127.0.0.1:8000
```

Copy `nestjs/.env.example` to `nestjs/.env` and `fastapi/.env.example` to `fastapi/.env`.
Both `DATABASE_URL` values must point to the same PostgreSQL database.

For an already initialized database, reseed with `npm.cmd run prisma:seed` from `nestjs/`.
Avoid `db:setup` on a database with data you need to preserve because `prisma db push` changes schema state.
`fastapi/seed.py` is only a compatibility wrapper that invokes the NestJS seed; it does not write data itself and is not needed during normal startup.

### Use real database values in Swagger

Open http://127.0.0.1:8000/docs and execute **GET `/demo/examples`** first. This read-only helper queries the shared database and returns:
- the actual demo user's UUID (`demoUser.id`);
- existing transactions and categories;
- ready-to-copy request bodies for categorization, anomaly detection, forecasting, and analytics endpoints.

Copy the actual `demoUser.id` into any endpoint's `userId` or `user_id` field, or copy the request body directly from `swaggerRequests`. This avoids guessing UUIDs or relying on Swagger's generic `"string"` placeholders.

The helper reads only `demo@example.com` and its related transaction/category records. It never writes to PostgreSQL. It returns 404 if the canonical seed has not been run. It is enabled for local development by default; set `ENABLE_DEMO_EXAMPLES=false` in `fastapi/.env` to disable it.


## Connection to NestJS

Already wired in the combined project. `nestjs/src/ai/ai.controller.ts` exposes three JWT-protected endpoints
(`GET /ai/predict`, `GET /ai/anomalies`, `POST /ai/categorize`) that take the user from the login token and call
this service. NestJS also calls `/ai/categorize-transaction` when a transaction is created without a category.

## Tests

```bash
python -m unittest discover -s tests -v      # or: pytest -v
```
- `tests/test_core.py`: logic (categorizer, anomalies, prediction, URL handling). Needs nothing else.
- `tests/test_api.py`: the HTTP routes. Needs the packages installed, PostgreSQL running and `python seed.py` done;
  otherwise they are skipped.

### Combined dashboard endpoint

`GET /analytics/summary?user_id=<uuid>&months=3&multiplier=2` returns the forecast, anomaly list, and anomaly counts by severity in one request. It reads the same Prisma-created tables and does not add or change database columns. `POST /ai/categorize-transaction` also accepts an optional `merchant` field, e.g. `{ "merchant": "Uber", "description": "Airport trip", "type": "EXPENSE", "userId": "<uuid>" }`. The `confidence` value is a simple rule-match indicator, not a statistically calibrated probability.

## Good to know

- **Prediction** = average monthly spend per category over the last 3 *completed* months, used as the
  estimate for the month after them (the current month while it is still in progress). With less history,
  only the months since the user's first expense are used.
- **Anomaly severity:** low (2x–3x peer average), medium (3x–4x), high (4x or more); anomalies include an explanation.
- **Old demo data:** `tests/sample_statement.csv` covers Jan to Apr 2026. For data that old,
  pass `asOf` (for example `2026-05-01`), otherwise the last 3 months are empty and so is the prediction.
- **Categories** use the NestJS shared names (Food, Transport, Shopping, Bills, Entertainment, Healthcare,
  Salary, Freelance, Other). Rules are keyword lists in `core.py` (`CATEGORY_RULES`); the first match wins.
- NestJS maps FastAPI problems to its own errors: an unknown user becomes `404`, any other FastAPI error `502`, and FastAPI being unreachable `503 FastAPI service is unavailable`.
- Do not expose port 8000 publicly: there is no login on this service (NestJS handles authentication).

## Analytics upgrades

### Robust anomaly detection and duplicate review

`GET /anomalies?user_id=<uuid>&multiplier=2` now compares each positive expense against the **median of other expenses in the same category**. The median is less affected by a few very large transactions, and the transaction being tested is excluded from its own baseline. For response compatibility, the existing `categoryAverage` field name is retained, but it contains this median baseline. Severity remains low (2x–3x), medium (3x–4x), high (4x or more).

`GET /duplicates?user_id=<uuid>&window_days=3` suggests pairs with the same normalized description and amount within the selected number of days (0–30). This is deliberately a review queue: legitimate recurring purchases can look alike, so nothing is deleted automatically. The combined summary also includes `duplicateSummary` and `possibleDuplicates`.

### Spending insights

`GET /analytics/insights?user_id=<uuid>&as_of=2026-10-13` compares spending from the first of the current month through `as_of` with the same elapsed day range in the previous month. It returns totals, percentage change, top categories, and the largest category increase. When there is no previous-period baseline, the percentage is `null` rather than misleadingly showing zero.



Example:

```json
{
  "csvText": "date,description,amount,type\n2026-05-01,Uber ride,250.00,EXPENSE\n2026-05-02,Monthly salary,5000.00,INCOME"
}
```

### Remaining limitations

- Forecasting remains a transparent historical average of completed calendar months; it does not model seasonality or future one-off events.
- Categorization uses deterministic keyword rules. Confidence is a rule-match indicator, not a calibrated ML probability.
- Duplicate matches and anomalies are suggestions, not fraud determinations. Always review them before taking action.
- FastAPI has no end-user authentication. Keep it on a trusted local/private network and call it through authenticated NestJS routes.


### Budget-aware analytics

`GET /analytics/summary?user_id=<uuid>&months=3&multiplier=2` now includes `budgetComparison` and `budgetSummary`, using existing rows in Prisma’s `Budget` table for the forecast month. No schema migration is required.


### Saving a suggested category to an existing transaction

NestJS exposes `POST /ai/transactions/{transactionId}/categorize` (Bearer token required). It loads the transaction only when it belongs to the authenticated user, asks FastAPI for a category suggestion, validates that the category is available to that user and transaction type, then persists the `categoryId` through Prisma. This route does not accept a user ID from the client. The existing `POST /ai/categorize` remains a suggestion-only endpoint.

## Authentication: use NestJS login

FastAPI analytics routes now require an access token issued by NestJS. They do not have a separate login system.

1. Set the **same** `JWT_SECRET` value in `nestjs/.env` and `fastapi/.env`.
2. Set the **same private** `FASTAPI_INTERNAL_API_KEY` value in both `.env` files. NestJS uses this key only for its server-to-server `/ai/*` calls. Never expose this key in frontend code or commit `.env` files.
3. Start PostgreSQL, then NestJS and FastAPI.
4. In NestJS Swagger (`http://localhost:3000/docs`), execute `POST /auth/login` with your registered account credentials. Copy `accessToken` from the response.
5. In FastAPI Swagger (`http://127.0.0.1:8000/docs`), click **Authorize**, paste the token (without adding the word `Bearer` if Swagger's HTTP Bearer dialog handles it), and authorize.
6. Execute analytics routes. User IDs in query strings or JSON bodies must match the ID in the JWT; attempts to request another user's data return `403`.

`GET /health` remains public for liveness checks. `/docs` and `/openapi.json` are public so Swagger can load, but analytics operations require authentication. `GET /demo/examples` now returns examples for the logged-in user rather than always returning the demo account. The internal `/ai/*` routes accept the private service key because NestJS already protects the corresponding application routes with its JWT guard.

If FastAPI returns `503 Authentication is not configured`, check `JWT_SECRET`. If NestJS AI routes return a FastAPI error, verify the internal API key matches exactly in both services.


## JWT user identity for Swagger (updated)

For public FastAPI analytics routes, click **Authorize** in Swagger and provide the NestJS access token as a Bearer token. The service derives the user ID from the validated JWT `sub` claim, so `userId` / `user_id` can be omitted from `/anomalies`, `/predict`, `/duplicates`, `/analytics/summary`, `/analytics/insights`, `/categorize`, and the public `/ai/*` routes. If an ID is supplied, it must match the authenticated user.

Trusted NestJS service-to-service calls authenticated with `x-internal-api-key` may continue to include `userId` in their `/ai/*` payloads; the NestJS API contract is unchanged. Restart FastAPI after replacing the files.


## Refactored source layout

The existing `main.py` entrypoint is retained for compatibility, but the FastAPI application
implementation now lives in `src/api/application.py`. The analytics logic formerly grouped
in `core.py` is split into focused modules:

- `src/services/categorization.py` — keyword rules and category suggestions
- `src/services/anomaly_detection.py` — unusual-spending detection
- `src/services/duplicate_detection.py` — possible duplicate transactions
- `src/services/prediction.py` — monthly spending forecasts and date helpers
- `src/services/insights.py` — spending insight calculations
- `src/services/transactions.py` — expense data model and database-row conversion
- `src/services/database.py` — database URL normalization and reusable SQL
- `core.py` — compatibility facade so existing tests/imports continue to work

Run the app from this `fastapi` directory with `python -m uvicorn main:app --reload`.


## API route organization

HTTP route handlers are split by feature under `src/api/`: categorization, anomalies, predictions, analytics, duplicate detection, account/testing helpers, and health. `src/api/application.py` retains app setup, authentication middleware, shared request/response models, and shared helper functions, then registers each router. Business logic remains under `src/services/`.
