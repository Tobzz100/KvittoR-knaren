import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import app as webapp_app


class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.client = webapp_app.app.test_client()

    def test_index_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Kvittor", response.data)

    def test_versions_endpoint_returns_four_versions(self):
        response = self.client.get("/api/versions")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 4)
        keys = {entry["key"] for entry in data}
        self.assertEqual(keys, {"root", "med-claude", "med-copilot", "med-opencode"})

    def test_calculate_root_two_items_25_percent(self):
        response = self.client.post(
            "/api/calculate",
            json={"version": "root", "shopping_list": "vara1 100, vara2 100", "moms": 25},
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

    def test_run_tests_unknown_version_returns_404(self):
        response = self.client.post("/api/test/med-unknown")
        self.assertEqual(response.status_code, 404)

    def test_run_tests_root_passes(self):
        response = self.client.post("/api/test/root")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["passed"])
        self.assertEqual(data["returncode"], 0)


if __name__ == "__main__":
    unittest.main()


"""
Job Done zug zug
"""
