import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import app as webapp_app
from kvitto_testrunner import ReportRunner


class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.client = webapp_app.app.test_client()

    def test_index_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Kvittor", response.data)

    def test_versions_endpoint_returns_three_versions(self):
        response = self.client.get("/api/versions")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 3)
        keys = {entry["key"] for entry in data}
        self.assertEqual(keys, {"med-claude", "med-copilot", "med-opencode"})

    def test_calculate_two_items_25_percent(self):
        response = self.client.post(
            "/api/calculate",
            json={"version": "med-opencode", "shopping_list": "vara1 100, vara2 100", "moms": 25},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"], 250)

    def test_calculate_med_claude_discount_applied_before_moms(self):
        response = self.client.post(
            "/api/calculate",
            json={
                "version": "med-claude",
                "shopping_list": "vara1 100, vara2 100",
                "moms": 25,
                "discount_code": "RABATT10",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"], 225)

    def test_calculate_med_copilot_discount_applied_before_moms(self):
        response = self.client.post(
            "/api/calculate",
            json={
                "version": "med-copilot",
                "shopping_list": "vara1 100, vara2 100",
                "moms": 25,
                "discount_code": "RABATT10",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"], 225)

    def test_calculate_med_opencode_discount_applied_before_moms(self):
        response = self.client.post(
            "/api/calculate",
            json={
                "version": "med-opencode",
                "shopping_list": "vara1 100, vara2 100",
                "moms": 25,
                "discount_code": "RABATT10",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"], 225)

    def test_calculate_med_claude_invalid_currency_returns_clean_error(self):
        response = self.client.post(
            "/api/calculate",
            json={
                "version": "med-claude",
                "shopping_list": "vara1 100",
                "moms": 25,
                "target_currency": "GBP",
                "currency": "GBP",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_calculate_med_copilot_invalid_currency_returns_clean_error(self):
        response = self.client.post(
            "/api/calculate",
            json={
                "version": "med-copilot",
                "shopping_list": "vara1 100",
                "moms": 25,
                "currency": "GBP",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Currency must be SEK, EUR, or USD.", response.get_json()["error"])

    def test_calculate_med_opencode_invalid_currency_returns_clean_error(self):
        response = self.client.post(
            "/api/calculate",
            json={
                "version": "med-opencode",
                "shopping_list": "vara1 100",
                "moms": 25,
                "currency": "GBP",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Okänd valuta", response.get_json()["error"])

    def test_calculate_unknown_version_returns_400(self):
        response = self.client.post(
            "/api/calculate",
            json={"version": "med-unknown", "shopping_list": "vara1 100", "moms": 25},
        )
        self.assertEqual(response.status_code, 400)

    def test_only_med_claude_uses_inventory(self):
        data = self.client.get("/api/versions").get_json()
        self.assertEqual({entry["key"]: entry["uses_inventory"] for entry in data}, {
            "med-claude": True,
            "med-copilot": False,
            "med-opencode": False,
        })

    def test_inventory_lists_items_with_price_and_vat_rate(self):
        response = self.client.get("/api/inventory/med-claude")
        self.assertEqual(response.status_code, 200)
        items = response.get_json()
        self.assertIn({"name": "Mjölk", "price": 15, "vat_percent": 12}, items)
        self.assertIn({"name": "Bok", "price": 200, "vat_percent": 6}, items)

    def test_inventory_for_version_without_one_returns_404(self):
        self.assertEqual(self.client.get("/api/inventory/med-copilot").status_code, 404)
        self.assertEqual(self.client.get("/api/inventory/med-unknown").status_code, 404)

    def test_receipt_uses_inventory_prices_and_discount(self):
        response = self.client.post(
            "/api/receipt",
            json={"version": "med-claude", "items": ["Mjölk", "Bok", "Tvål"], "discount_code": "RABATT10"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("Rabatt 10 %              -23,50", data["receipt"])
        self.assertIn("ATT BETALA               228,42", data["receipt"])
        self.assertEqual(data["messages"], [])

    def test_receipt_skips_unknown_items_with_message(self):
        response = self.client.post("/api/receipt", json={"version": "med-claude", "items": ["Mjölk", "Guld"]})
        data = response.get_json()
        self.assertEqual(data["messages"], ["Skipping unknown item: 'Guld'"])
        self.assertNotIn("Guld", data["receipt"])
        self.assertIn("ATT BETALA                16,80", data["receipt"])

    def test_receipt_unknown_discount_code_gives_message_and_full_price(self):
        response = self.client.post(
            "/api/receipt",
            json={"version": "med-claude", "items": ["Mjölk"], "discount_code": "FINNSINTE"},
        )
        data = response.get_json()
        self.assertEqual(data["messages"], ["Discount code 'FINNSINTE' does not exist, no discount applied"])
        self.assertIn("ATT BETALA                16,80", data["receipt"])

    def test_receipt_with_empty_cart_gives_inga_varor(self):
        response = self.client.post("/api/receipt", json={"version": "med-claude", "items": []})
        self.assertEqual(response.get_json()["receipt"], "Inga varor")

    def test_receipt_rejects_bad_input(self):
        for payload in (
            {"version": "med-copilot", "items": ["Mjölk"]},
            {"version": "med-claude", "items": "Mjölk"},
            {"version": "med-claude", "items": [1]},
            {"version": "med-claude", "items": ["Mjölk"], "discount_code": ["RABATT10"]},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/receipt", json=payload).status_code, 400)

    def test_run_tests_unknown_version_returns_404(self):
        response = self.client.post("/api/test/med-unknown")
        self.assertEqual(response.status_code, 404)

    def test_run_tests_removed_root_version_returns_404(self):
        response = self.client.post("/api/test/root")
        self.assertEqual(response.status_code, 404)

    def test_run_tests_version_runs_shared_and_its_own_tests_only(self):
        response = self.client.post("/api/test/med-claude")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["passed"])
        self.assertEqual(data["returncode"], 0)
        self.assertIn("== test_kvittoraknaren.py ==", data["output"])
        self.assertIn(os.path.join("med-claude", "test_kvittoraknaren.py"), data["output"])
        self.assertNotIn("med-copilot", data["output"])
        self.assertNotIn("med-opencode", data["output"])


if __name__ == "__main__":
    unittest.main(testRunner=ReportRunner())


"""
Job Done zug zug
"""
