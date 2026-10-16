# CORE LOGIC TESTS
# These tests verify categorization, date/amount calculations, anomaly and duplicate
# detection, predictions, insights, and compatibility with the NestJS Prisma schema.

"""
Logic tests. They need NO database and NO FastAPI, only Python.

    python -m unittest discover -s tests -v      (or:  pytest -v)
"""
import csv
import os
import random
import sqlite3
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core  # noqa: E402
import seed  # noqa: E402

HERE = os.path.dirname(__file__)


# Purpose: Create a small Expense object used by the logic tests.
def expense(i, amount, day, category="Food", cid="c-food"):
    return core.Expense(f"t{i}", f"item {i}", float(amount), day, cid, category)


# Purpose: Group related DatabaseUrl test cases.
class TestDatabaseUrl(unittest.TestCase):
    # Purpose: Check that the corresponding behavior remains correct.
    def test_nestjs_url_is_converted(self):
        url = "postgresql://postgres:secret@localhost:5432/personal_finance?schema=public"
        self.assertEqual(
            core.normalize_database_url(url),
            "postgresql+psycopg://postgres:secret@localhost:5432/personal_finance",
        )

    # Purpose: Check that the corresponding behavior remains correct.
    def test_quotes_and_postgres_scheme(self):
        self.assertTrue(core.normalize_database_url('"postgres://u:p@h/db"').startswith("postgresql+psycopg://"))

    # Purpose: Check that the corresponding behavior remains correct.
    def test_other_params_kept_and_special_password_untouched(self):
        out = core.normalize_database_url("postgresql://u:p%40ss@h:5432/db?schema=public&sslmode=require")
        self.assertEqual(out, "postgresql+psycopg://u:p%40ss@h:5432/db?sslmode=require")

    # Purpose: Check that the corresponding behavior remains correct.
    def test_already_psycopg(self):
        url = "postgresql+psycopg://u:p@h:5432/db"
        self.assertEqual(core.normalize_database_url(url), url)


# Purpose: Group related Categorize test cases.
class TestCategorize(unittest.TestCase):
    # Purpose: Check that the corresponding behavior remains correct.
    def test_nestjs_sample_statement(self):
        # NOTE: the keyword lists were tuned while looking at this file, so this is a
        # regression check, not an independent accuracy measurement.
        with open(os.path.join(HERE, "sample_statement.csv"), newline="") as fh:
            rows = list(csv.DictReader(fh))
        wrong = [
            (r["description"], r["category"], core.categorize_text(r["description"], r["type"]).category)
            for r in rows
            if core.categorize_text(r["description"], r["type"]).category != r["category"]
        ]
        self.assertGreaterEqual(1 - len(wrong) / len(rows), 0.95, wrong)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_phrases_not_taken_from_the_sample(self):
        cases = [
            ("Starbucks coffee", "EXPENSE", "Food"),
            ("Uber trip to airport", "EXPENSE", "Transport"),
            ("Netflix", "EXPENSE", "Entertainment"),
            ("Apollo pharmacy", "EXPENSE", "Healthcare"),
            ("Electricity board payment", "EXPENSE", "Bills"),
            ("IRCTC train ticket", "EXPENSE", "Transport"),
            ("Petrol pump", "EXPENSE", "Transport"),
            ("Amazon order", "EXPENSE", "Shopping"),
            ("Airtel postpaid", "EXPENSE", "Bills"),
            ("Birthday gift", "EXPENSE", "Other"),
            ("March payroll", "INCOME", "Salary"),
            ("Client invoice 114", "INCOME", "Freelance"),
            ("Cash deposit", "INCOME", "Other"),
        ]
        for description, kind, expected in cases:
            with self.subTest(description):
                self.assertEqual(core.categorize_text(description, kind).category, expected)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_whole_words_only(self):
        self.assertEqual(core.categorize_text("Business lunch meeting").category, "Food")      # not 'bus'
        self.assertEqual(core.categorize_text("Cola bottle").category, "Other")                # not 'ola'
        self.assertEqual(core.categorize_text("Buses").category, "Transport")                  # plural ok

    # Purpose: Check that the corresponding behavior remains correct.
    def test_case_and_empty(self):
        self.assertEqual(core.categorize_text("UBER RIDE").category, "Transport")
        self.assertEqual(core.categorize_text("").category, "Other")
        self.assertEqual(core.categorize_text(None).category, "Other")

    # Purpose: Check that the corresponding behavior remains correct.
    def test_names_match_nestjs_shared_categories(self):
        expense_names = {n for n, _ in core.CATEGORY_RULES["EXPENSE"]} | {core.DEFAULT_CATEGORY}
        income_names = {n for n, _ in core.CATEGORY_RULES["INCOME"]} | {core.DEFAULT_CATEGORY}
        shared = {(n, t) for n, t in seed.SHARED_CATEGORIES}
        for n in expense_names:
            self.assertIn((n, "EXPENSE"), shared)
        for n in income_names:
            self.assertIn((n, "INCOME"), shared)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_seed_descriptions_agree_with_categorizer(self):
        for r in seed.build_seed_data(date(2026, 10, 8), random.Random(42)):
            self.assertEqual(core.categorize_text(r["description"], r["type"]).category, r["category"], r)


# Purpose: Group related RowConversion test cases.
class TestRowConversion(unittest.TestCase):
    # Purpose: Check that the corresponding behavior remains correct.
    def test_postgres_style_values(self):
        from datetime import datetime
        from decimal import Decimal
        rows = [{"id": "a", "description": "Lunch", "amount": Decimal("12.50"),
                 "date": datetime(2026, 4, 1, 12, 0), "category_id": "c1", "category": "Food"}]
        (e,) = core.rows_to_expenses(rows)
        self.assertEqual((e.amount, e.date), (12.5, date(2026, 4, 1)))

    # Purpose: Check that the corresponding behavior remains correct.
    def test_iso_string_dates(self):
        rows = [{"id": "a", "description": "x", "amount": 1, "date": "2026-04-01T12:00:00.000Z",
                 "category_id": "c1", "category": "Food"}]
        self.assertEqual(core.rows_to_expenses(rows)[0].date, date(2026, 4, 1))


# Purpose: Group related Anomalies test cases.
class TestAnomalies(unittest.TestCase):
    # Purpose: Check that the corresponding behavior remains correct.
    def test_flags_only_above_multiplier(self):
        items = [expense(i, 100, date(2026, 5, 1)) for i in range(9)] + [expense(9, 900, date(2026, 5, 2))]
        # The 900 expense is compared against the other nine expenses (average 100).
        found = core.find_anomalies(items)
        self.assertEqual([a.expense.id for a in found], ["t9"])
        self.assertEqual(found[0].category_average, 100.0)
        self.assertEqual(found[0].times_average, 9.0)
        self.assertEqual(found[0].severity, "high")
        self.assertIn("9.0x the average", found[0].reason)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_exactly_double_peer_average_is_not_flagged(self):
        items = [expense(1, 100, date(2026, 5, 1)), expense(2, 100, date(2026, 5, 1)),
                 expense(3, 200, date(2026, 5, 1))]
        self.assertEqual(core.find_anomalies(items), [])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_single_expense_has_no_peer_baseline(self):
        self.assertEqual(core.find_anomalies([expense(1, 10_000, date(2026, 5, 1))]), [])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_categories_are_independent(self):
        items = [expense(i, 10, date(2026, 5, 1)) for i in range(5)] + \
                [expense(10 + i, 1000, date(2026, 5, 1), "Bills", "c-bills") for i in range(5)]
        self.assertEqual(core.find_anomalies(items), [])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_empty_input(self):
        self.assertEqual(core.find_anomalies([]), [])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_custom_multiplier(self):
        # Peer average is 100, so 300 is exactly 3x that baseline.
        items = [expense(i, 100, date(2026, 5, 1)) for i in range(9)] + [expense(9, 300, date(2026, 5, 1))]
        self.assertEqual(len(core.find_anomalies(items, 2)), 1)
        self.assertEqual(len(core.find_anomalies(items, 3)), 0)


# Purpose: Group related Predict test cases.
class TestPredict(unittest.TestCase):
    # Purpose: Check that the corresponding behavior remains correct.
    def test_average_of_last_three_completed_months(self):
        as_of = date(2026, 10, 8)    # window: Jul, Aug, Sep 2026
        items = [
            expense(1, 300, date(2026, 7, 5)), expense(2, 600, date(2026, 8, 5)), expense(3, 900, date(2026, 9, 5)),
            expense(4, 5000, date(2026, 6, 30)),      # before the window: ignored
            expense(5, 7000, date(2026, 10, 2)),      # current, unfinished month: ignored
        ]
        p = core.predict_next_month(items, as_of)
        self.assertEqual((p.year, p.month, p.months_used), (2026, 10, 3))
        self.assertEqual(p.categories[0].predicted_amount, 600.0)
        self.assertEqual(p.total, 600.0)
        self.assertEqual((p.based_on_start, p.based_on_end), (date(2026, 7, 1), date(2026, 9, 30)))

    # Purpose: Check that the corresponding behavior remains correct.
    def test_short_history_not_underestimated(self):
        items = [expense(1, 300, date(2026, 9, 5))]       # only one completed month of history
        p = core.predict_next_month(items, date(2026, 10, 8))
        self.assertEqual(p.months_used, 1)
        self.assertEqual(p.categories[0].predicted_amount, 300.0)   # not 100

    # Purpose: Check that the corresponding behavior remains correct.
    def test_year_boundary(self):
        items = [expense(1, 120, date(2025, 11, 5)), expense(2, 120, date(2025, 12, 5)), expense(3, 120, date(2026, 1, 5))]
        p = core.predict_next_month(items, date(2026, 2, 14))
        self.assertEqual((p.year, p.month, p.months_used), (2026, 2, 3))
        self.assertEqual(p.total, 120.0)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_no_data_or_only_current_month(self):
        self.assertEqual(core.predict_next_month([], date(2026, 10, 8)).categories, [])
        only_now = [expense(1, 50, date(2026, 10, 2))]
        self.assertEqual(core.predict_next_month(only_now, date(2026, 10, 8)).categories, [])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_months_parameter(self):
        items = [expense(i, 100, date(2026, i, 5)) for i in range(1, 10)]
        p = core.predict_next_month(items, date(2026, 10, 8), months=6)
        self.assertEqual(p.months_used, 6)
        self.assertEqual(p.total, 100.0)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_largest_category_first(self):
        items = [expense(1, 10, date(2026, 9, 1)), expense(2, 500, date(2026, 9, 1), "Bills", "c-bills")]
        names = [c.category for c in core.predict_next_month(items, date(2026, 10, 1)).categories]
        self.assertEqual(names, ["Bills", "Food"])


# Purpose: Group related DuplicateDetection test cases.
class TestDuplicateDetection(unittest.TestCase):
    # Purpose: Check that the corresponding behavior remains correct.
    def test_same_description_amount_nearby_is_flagged(self):
        items = [
            core.Expense("a", "UBER trip #123", 25, date(2026, 5, 1), "c", "Transport"),
            core.Expense("b", "Uber trip 123", 25, date(2026, 5, 3), "c", "Transport"),
            core.Expense("c", "Uber trip 123", 25, date(2026, 5, 10), "c", "Transport"),
        ]
        found = core.find_duplicate_transactions(items)
        self.assertEqual(len(found), 1)
        self.assertEqual((found[0].first.id, found[0].second.id, found[0].days_apart), ("a", "b", 2))

    # Purpose: Check that the corresponding behavior remains correct.
    def test_different_amount_or_description_is_not_flagged(self):
        items = [
            core.Expense("a", "Coffee shop", 5, date(2026, 5, 1), "c", "Food"),
            core.Expense("b", "Coffee shop", 6, date(2026, 5, 2), "c", "Food"),
            core.Expense("c", "Book shop", 5, date(2026, 5, 2), "c", "Shopping"),
        ]
        self.assertEqual(core.find_duplicate_transactions(items), [])


# Purpose: Group related SpendingInsights test cases.
class TestSpendingInsights(unittest.TestCase):
    # Purpose: Check that the corresponding behavior remains correct.
    def test_compares_same_elapsed_days_and_reports_category_change(self):
        items = [
            core.Expense("a", "Lunch", 100, date(2026, 4, 5), "food", "Food"),
            core.Expense("b", "Lunch", 150, date(2026, 5, 5), "food", "Food"),
            core.Expense("c", "Taxi", 50, date(2026, 5, 4), "transport", "Transport"),
            core.Expense("d", "Future", 999, date(2026, 5, 6), "food", "Food"),
        ]
        result = core.spending_insights(items, date(2026, 5, 5))
        self.assertEqual(result["currentPeriodSpend"], 200)
        self.assertEqual(result["previousPeriodSpend"], 100)
        self.assertEqual(result["changePercent"], 100.0)
        self.assertEqual(result["topCategories"][0]["category"], "Food")

    # Purpose: Check that the corresponding behavior remains correct.
    def test_no_previous_baseline_is_explicit(self):
        result = core.spending_insights([], date(2026, 5, 5))
        self.assertIsNone(result["changePercent"])
        self.assertIsNone(result["largestIncrease"])
        self.assertIn("no previous-period", result["notes"][0])


class TestPipelineOnSeedData(unittest.TestCase):
    """Seed data -> tables laid out like the Prisma ones -> the real SQL -> core logic."""

    SCHEMA = """
    CREATE TABLE "User" (id TEXT PRIMARY KEY, name TEXT, email TEXT, password TEXT);
    CREATE TABLE "Category" (id TEXT PRIMARY KEY, name TEXT, "type" TEXT, "userId" TEXT);
    CREATE TABLE "Transaction" (id TEXT PRIMARY KEY, "userId" TEXT, amount REAL, "type" TEXT,
        description TEXT, "date" TEXT, "categoryId" TEXT, source TEXT);
    """
    TODAY = date(2026, 10, 8)

    @classmethod
    # Purpose: Prepare shared test client/database fixtures once for this test class.
    def setUpClass(cls):
        cls.db = sqlite3.connect(":memory:")
        cls.db.row_factory = sqlite3.Row
        cls.db.executescript(cls.SCHEMA)
        ids = {}
        for n, (name, kind) in enumerate(seed.SHARED_CATEGORIES):
            ids[(name, kind)] = f"cat-{n}"
            cls.db.execute('INSERT INTO "Category" VALUES (?,?,?,NULL)', (ids[(name, kind)], name, kind))
        cls.db.execute('INSERT INTO "User" VALUES (?,?,?,?)', ("user-1", "Demo", "demo@example.com", "x"))
        cls.data = seed.build_seed_data(cls.TODAY, random.Random(42))
        for n, r in enumerate(cls.data):
            cls.db.execute(
                'INSERT INTO "Transaction" VALUES (?,?,?,?,?,?,?,?)',
                (f"tx-{n}", "user-1", r["amount"], r["type"], r["description"], r["date"].isoformat(),
                 ids[(r["category"], r["type"])], seed.SOURCE))

    # Purpose: Create several representative expense rows for database-query tests.
    def expenses(self):
        rows = self.db.execute(core.SQL_USER_EXPENSES, {"uid": "user-1"}).fetchall()
        return core.rows_to_expenses([dict(r) for r in rows])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_user_exists_query(self):
        self.assertIsNotNone(self.db.execute(core.SQL_USER_EXISTS, {"id": "user-1"}).fetchone())
        self.assertIsNone(self.db.execute(core.SQL_USER_EXISTS, {"id": "nobody"}).fetchone())

    # Purpose: Check that the corresponding behavior remains correct.
    def test_income_is_excluded(self):
        expected = sum(1 for r in self.data if r["type"] == "EXPENSE")
        self.assertEqual(len(self.expenses()), expected)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_huge_transactions_are_the_top_anomalies(self):
        found = core.find_anomalies(self.expenses())
        huge = {h[1] for h in seed.HUGE_EXPENSES}
        self.assertEqual({a.expense.description for a in found[: len(huge)]}, huge)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_prediction_has_values_for_the_main_categories(self):
        p = core.predict_next_month(self.expenses(), self.TODAY)
        self.assertEqual(p.months_used, 3)
        self.assertGreater(len(p.categories), 3)
        self.assertAlmostEqual(p.total, sum(c.predicted_amount for c in p.categories), places=1)
        # the deliberately huge seed items are older than the window, so no category is inflated by them
        self.assertTrue(all(c.predicted_amount < 400 for c in p.categories), p.categories)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_find_category_prefers_users_own_over_shared(self):
        self.db.execute('INSERT INTO "Category" VALUES (?,?,?,?)', ("cat-own", "Food", "EXPENSE", "user-1"))
        shared = self.db.execute(core.SQL_FIND_CATEGORY, {"name": "food", "type": "EXPENSE", "uid": "someone-else"}).fetchone()
        own = self.db.execute(core.SQL_FIND_CATEGORY, {"name": "food", "type": "EXPENSE", "uid": "user-1"}).fetchone()
        self.assertEqual(shared["id"], "cat-0")
        self.assertEqual(own["id"], "cat-own")
        wrong_type = self.db.execute(core.SQL_FIND_CATEGORY, {"name": "Salary", "type": "EXPENSE", "uid": "user-1"}).fetchone()
        self.assertIsNone(wrong_type)


if __name__ == "__main__":
    unittest.main()
