# Personal Finance API (NestJS)

NestJS owns authentication and finance writes. It shares PostgreSQL with the companion FastAPI service, which remains read-only and supplies categorization, predictions, and anomaly detection.

## Features

- JWT authentication: register and login, with authenticated current-user profile management.
- User-scoped category creation and listing, plus transactions.
- Monthly per-category budgets and budget usage.
- Monthly spending/income reports and month-over-month trends.
- Authenticated AI proxy endpoints that pass the signed-in user's ID to FastAPI.
- Swagger UI at `/docs`.

## Setup

1. Install Node.js 20.11 or newer and PostgreSQL.
2. Copy `.env.example` to `.env`; set `DATABASE_URL` to the same database URL used by FastAPI, a strong `JWT_SECRET`, `FASTAPI_BASE_URL`, and the same private `FASTAPI_INTERNAL_API_KEY` used in `fastapi/.env`.
3. Install dependencies:

   ```powershell
   npm.cmd install
   ```

4. For a **new, empty local database only**, create the tables and shared categories:

   ```powershell
   npm.cmd run db:setup
   ```

   If using an existing database shared with FastAPI, do not run `db:setup` blindly. First confirm its schema and Prisma migration history; use the same valid `DATABASE_URL` and make only the reviewed schema change needed for `Budget`.

5. Start NestJS:

   ```powershell
   npm.cmd run start:dev
   ```

The app listens on `http://localhost:3000`; Swagger is at `http://localhost:3000/docs`.

## Database compatibility

The Prisma models for `"User"`, `"Category"`, and `"Transaction"` use the identifiers and columns expected by FastAPI. The `Budget` model is the only new table introduced by this NestJS app. Before applying schema changes to a database already managed by another Prisma project, compare its existing Prisma schema/migration history and back up the database. `npm.cmd run prisma:push` is intended for a new/local development database; do not run it against production or a shared database without reviewing the proposed schema changes.

The FastAPI seed script can create the shared demo user and categories. NestJS registration does not create or alter FastAPI files or seed data.

## API workflow

All routes except registration and login require a JWT bearer token. Registration returns an access token, so a new user can proceed directly to authenticated requests. For later sessions, use the login endpoint and send its token as `Authorization: Bearer <token>`.

### 1. Create a user account

- `POST /auth/register` — create an account and receive an access token.

### 2. Authenticate

- `POST /auth/login` — sign in and receive an access token.

### 3. Create and list categories

- `POST /categories` — create a personal category with a name and type (`INCOME` or `EXPENSE`).
- `GET /categories` — list shared and personal categories.
- `PATCH /categories/:id` — update one of your custom categories. A category type cannot be changed if it has incompatible transactions or budgets.
- `DELETE /categories/:id` — delete one of your custom categories if it has no transactions or budgets.

### 4. Create and manage transactions

- `POST /transactions` — create a transaction. If `categoryId` is omitted, FastAPI suggests a category.
- `GET /transactions` — list transactions.
- `GET /transactions/:id` — get a transaction.
- `PATCH /transactions/:id` — update a transaction.
- `DELETE /transactions/:id` — delete a transaction.
- `GET /transactions/import/template` — download a CSV template. Required columns: `date` (`YYYY-MM-DD`), `description`, `amount` (positive, at most 2 decimal places), and `type` (`INCOME` or `EXPENSE`). `category` is optional.
- `POST /transactions/import` — upload the completed template as multipart form data with the file field named `file`. The entire file is validated before saving; any invalid row or unavailable category rejects the import without writing transactions. Blank categories are suggested by FastAPI. Maximum: 500 transactions per file and 5 MB.

### 5. Set budgets

- `POST /budgets` — create or replace a monthly category budget.
- `GET /budgets` — list budgets for a month.
- `GET /budgets/usage?year=&month=` — compare spending with monthly budgets.
- `PATCH /budgets/:id` — update a budget.
- `DELETE /budgets/:id` — delete a budget.

### 6. Review reports

- `GET /reports/monthly?year=&month=` — view monthly income, spending, and category totals.
- `GET /reports/trends?months=6` — view month-over-month trends.
- `http://localhost:3000/trends.html` — visualize income, expenses, and net trends using the authenticated trends endpoint.

### 7. Use AI analytics

- `POST /ai/predict-spending` — predict spending per category (optional body: `{ "months": 3, "asOf": "2026-10-01" }`).
- `POST /ai/detect-anomaly` — find unusually large expenses (optional body: `{ "multiplier": 2 }`).
- `POST /ai/categorize` — suggest a category for a transaction description.

### 8. Manage your profile

- `GET /users/profile` — view the authenticated user profile.
- `PATCH /users/profile` — update the authenticated user’s name and/or email.

AI routes call the matching FastAPI endpoint and forward the authenticated user's ID; callers cannot choose another user's ID.
