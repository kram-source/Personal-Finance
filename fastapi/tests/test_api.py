# API TESTS
# These tests exercise request validation, route responses, authentication-facing
# behavior, and (when PostgreSQL is available) database-backed analytics endpoints.

"""
HTTP-level tests. Need:  pip install -r requirements.txt   (FastAPI + httpx)
The classes that touch the database also need PostgreSQL running and `python seed.py` done.
They skip themselves (instead of failing) when something is missing.

    python -m unittest discover -s tests -v      (or:  pytest -v)
"""
import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    import main
    IMPORT_ERROR = None
except Exception as exc:  # noqa: BLE001  (packages not installed)
    IMPORT_ERROR = exc

DEMO_EMAIL = "demo@example.com"
HUGE = {"Laptop purchase", "Wedding catering", "Weekend trip flights", "Annual insurance premium"}


@unittest.skipIf(IMPORT_ERROR, f"FastAPI packages not installed: {IMPORT_ERROR}")
# Purpose: Group related WithoutDatabase test cases.
class TestWithoutDatabase(unittest.TestCase):
    @classmethod
    # Purpose: Prepare shared test client/database fixtures once for this test class.
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_both_categorize_routes(self):
        for path in ("/ai/categorize-transaction", "/categorize"):
            with self.subTest(path):
                r = self.client.post(path, json={"description": "Uber ride to airport"})
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.json()["category"], "Transport")
                self.assertEqual(r.json()["type"], "EXPENSE")
                self.assertIsNone(r.json()["categoryId"])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_docs_hide_swagger_topbar(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(".swagger-ui .topbar { display: none; }", response.text)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_income_categorization(self):
        r = self.client.post("/ai/categorize-transaction", json={"description": "March payroll", "type": "INCOME"})
        self.assertEqual(r.json()["category"], "Salary")

    # Purpose: Check that the corresponding behavior remains correct.

    # Purpose: Check that the corresponding behavior remains correct.

    # Purpose: Check that the corresponding behavior remains correct.

    # Purpose: Check that the corresponding behavior remains correct.
    def test_validation_errors(self):
        post = self.client.post
        self.assertEqual(post("/ai/categorize-transaction", json={}).status_code, 422)
        self.assertEqual(post("/ai/categorize-transaction", json={"description": "x", "type": "NOPE"}).status_code, 422)
        self.assertEqual(post("/ai/detect-anomaly", json={"userId": "x", "multiplier": 1}).status_code, 422)
        self.assertEqual(post("/ai/predict-spending", json={"userId": "x", "months": 0}).status_code, 422)
        self.assertEqual(self.client.get("/anomalies").status_code, 422)
        self.assertEqual(self.client.get("/predict").status_code, 422)


@unittest.skipIf(IMPORT_ERROR, f"FastAPI packages not installed: {IMPORT_ERROR}")
# Purpose: Group related WithDatabase test cases.
class TestWithDatabase(unittest.TestCase):
    @classmethod
    # Purpose: Prepare shared test client/database fixtures once for this test class.
    def setUpClass(cls):
        cls.client = TestClient(main.app)
        try:
            with main.engine.connect() as conn:
                row = conn.execute(text('SELECT id FROM "User" WHERE email = :e'), {"e": DEMO_EMAIL}).first()
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(f"Database not reachable or tables missing: {exc.__class__.__name__}")
        if row is None:
            raise unittest.SkipTest("Demo user not found: run `python seed.py` first")
        cls.user_id = row[0]

    # Purpose: Check that the corresponding behavior remains correct.
    def test_health(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok", "database": "ok"})

    # Purpose: Check that the corresponding behavior remains correct.
    def test_demo_examples_uses_real_seeded_rows(self):
        response = self.client.get("/demo/examples")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["demoUser"]["email"], DEMO_EMAIL)
        self.assertTrue(body["demoUser"]["id"])
        self.assertGreater(body["counts"]["transactionsReturned"], 0)
        self.assertEqual(body["swaggerRequests"]["POST /ai/detect-anomaly"]["userId"], body["demoUser"]["id"])
        self.assertIn("description", body["swaggerRequests"]["POST /ai/categorize-transaction"])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_anomalies_find_the_huge_expenses_and_ignore_income(self):
        for r in (self.client.get("/anomalies", params={"user_id": self.user_id}),
                  self.client.post("/ai/detect-anomaly", json={"userId": self.user_id})):
            self.assertEqual(r.status_code, 200)
            body = r.json()
            self.assertEqual(body["userId"], self.user_id)
            self.assertEqual({a["description"] for a in body["anomalies"][:4]}, HUGE)
            self.assertNotIn("Monthly salary", {a["description"] for a in body["anomalies"]})   # INCOME excluded
            self.assertIn("categoryAverage", body["anomalies"][0])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_predict(self):
        for r in (self.client.get("/predict", params={"user_id": self.user_id}),
                  self.client.post("/ai/predict-spending", json={"userId": self.user_id})):
            self.assertEqual(r.status_code, 200)
            body = r.json()
            self.assertGreaterEqual(len(body["predictions"]), 4)
            self.assertEqual(body["basedOn"]["months"], 3)
            self.assertAlmostEqual(body["totalPredicted"], sum(p["predictedAmount"] for p in body["predictions"]), places=1)

    # Purpose: Check that the corresponding behavior remains correct.
    def test_predict_as_of(self):
        r = self.client.post("/ai/predict-spending", json={"userId": self.user_id, "asOf": "2000-01-01"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["predictions"], [])      # no data that long ago -> empty, not an error

    # Purpose: Check that the corresponding behavior remains correct.
    def test_categorize_returns_category_id_for_a_user(self):
        r = self.client.post("/ai/categorize-transaction", json={"description": "Pizza night", "userId": self.user_id})
        self.assertEqual(r.json()["category"], "Food")
        self.assertIsNotNone(r.json()["categoryId"])

    # Purpose: Check that the corresponding behavior remains correct.
    def test_unknown_user_is_404_not_a_crash(self):
        unknown = str(uuid.uuid4())
        self.assertEqual(self.client.get("/anomalies", params={"user_id": unknown}).status_code, 404)
        self.assertEqual(self.client.get("/predict", params={"user_id": unknown}).status_code, 404)
        self.assertEqual(self.client.post("/ai/detect-anomaly", json={"userId": unknown}).status_code, 404)
        self.assertEqual(self.client.post("/ai/predict-spending", json={"userId": unknown}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
