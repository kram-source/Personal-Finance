# DEMO-SEED COMPATIBILITY AND TEST DATA
# NestJS/Prisma remains the canonical database writer. This module supplies synthetic
# sample rows for unit tests and a wrapper that invokes the NestJS seed command.

"""
Seed demo data into the SAME PostgreSQL database the NestJS app uses.

It writes straight into the Prisma tables ("User", "Category", "Transaction"), so
the demo user can also log in through NestJS:

    email:    demo@example.com
    password: Demo@1234

Run the NestJS migration first (it creates the tables):
    npm run prisma:migrate

Then, from this folder:
    python seed.py

Safe to re-run: it only deletes/re-creates transactions that this script created
(source = 'FastAPI seed'). Anything else in the database is left alone.
"""
import calendar
import os
import random
import sys
import uuid
from datetime import date, datetime

from dotenv import load_dotenv

import core

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/personal_finance")

DEMO_NAME = "Demo User"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "Demo@1234"
SOURCE = "FastAPI seed"

# Same shared categories as NestJS prisma/seed.ts (created here only if missing).
SHARED_CATEGORIES = [
    ("Food", "EXPENSE"), ("Transport", "EXPENSE"), ("Shopping", "EXPENSE"),
    ("Bills", "EXPENSE"), ("Entertainment", "EXPENSE"), ("Healthcare", "EXPENSE"),
    ("Salary", "INCOME"), ("Freelance", "INCOME"),
    ("Other", "EXPENSE"), ("Other", "INCOME"),
]

# category: (weight, (min, max), descriptions)
EXPENSE_PATTERNS = {
    "Food": (32, (5, 90), ["Grocery store", "Supermarket groceries", "Cafe lunch", "Restaurant dinner",
                           "Pizza night", "Swiggy order", "Zomato dinner", "Market vegetables",
                           "Cafe breakfast", "Bakery snacks"]),
    "Transport": (20, (3, 60), ["Uber ride", "Taxi ride", "Bus pass", "Metro card refill", "Train fare",
                                "Petrol fill-up", "Parking and tolls", "Rideshare trip"]),
    "Shopping": (14, (15, 150), ["Amazon order", "Flipkart order", "Clothing purchase", "Shoes purchase",
                                 "Household supplies", "Kitchen supplies", "Online book purchase"]),
    "Bills": (12, (30, 130), ["Electric bill", "Water bill", "Internet bill", "Gas bill",
                              "Mobile phone bill", "Phone recharge"]),
    "Entertainment": (8, (8, 70), ["Movie tickets", "Streaming subscription", "Concert ticket", "Cinema and snacks"]),
    "Healthcare": (7, (10, 90), ["Pharmacy purchase", "Doctor visit", "Dental checkup", "Prescription medicine"]),
    "Other": (7, (2, 25), ["Other bank charge", "Other service charge", "Other account fee"]),
}

# (months ago, description, category, amount): deliberately huge, so /anomalies has work to do.
# All are older than the 3-month prediction window, so /predict stays realistic.
HUGE_EXPENSES = [
    (5, "Laptop purchase", "Shopping", 1899.00),
    (4, "Wedding catering", "Food", 950.00),
    (6, "Weekend trip flights", "Transport", 1250.00),
    (4, "Annual insurance premium", "Bills", 1480.00),
]

MONTHS_OF_HISTORY = 6      # plus the current (partial) month
EXPENSES_PER_MONTH = 22


def build_seed_data(today: date, rng: random.Random) -> list[dict]:
    """Pure function: returns transactions as dicts (category given by NAME)."""
    this_month = core.first_of_month(today)
    rows: list[dict] = []

    # Purpose: Append one normalized transaction record to the generated demo dataset.
    def add(kind, category, description, amount, day: date):
        rows.append({
            "type": kind, "category": category, "description": description,
            "amount": round(amount, 2), "date": datetime(day.year, day.month, day.day, 12, 0, 0),
        })

    names = list(EXPENSE_PATTERNS)
    weights = [EXPENSE_PATTERNS[n][0] for n in names]

    for k in range(MONTHS_OF_HISTORY, -1, -1):
        month = core.add_months(this_month, -k)
        last_day = calendar.monthrange(month.year, month.month)[1]
        max_day = last_day if k > 0 else today.day          # never create future dates
        count = EXPENSES_PER_MONTH if k > 0 else round(EXPENSES_PER_MONTH * today.day / 30)

        add("INCOME", "Salary", "Monthly salary", 4200.00, month.replace(day=1))
        if max_day >= 10 and rng.random() < 0.6:
            add("INCOME", "Freelance", rng.choice(["Freelance website work", "Freelance consulting"]),
                rng.uniform(300, 600), month.replace(day=10))

        for _ in range(count):
            cat = rng.choices(names, weights)[0]
            _, (lo, hi), descriptions = EXPENSE_PATTERNS[cat]
            add("EXPENSE", cat, rng.choice(descriptions), rng.uniform(lo, hi),
                month.replace(day=rng.randint(1, max_day)))

    for months_ago, description, cat, amount in HUGE_EXPENSES:
        month = core.add_months(this_month, -months_ago)
        add("EXPENSE", cat, description, amount, month.replace(day=15))
    return rows


def main() -> None:
    """Run the one canonical Prisma seed used by NestJS and FastAPI.

    Run from any directory. NestJS/Prisma owns writes and schema semantics;
    FastAPI only consumes the resulting shared database.
    """
    import subprocess
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    nestjs_dir = project_root / "nestjs"
    try:
        subprocess.run(["npm", "run", "prisma:seed"], cwd=nestjs_dir, check=True)
    except FileNotFoundError:
        sys.exit("npm was not found. Install Node.js/npm and run this script again.")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Shared Prisma seed failed (exit code {exc.returncode}). Check DATABASE_URL in nestjs/.env.")


if __name__ == "__main__":
    main()
