import importlib.util
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kvitto_testrunner import ReportRunner

MODULE_PATH = os.path.join(os.path.dirname(__file__), "Kvittoräknaren.py")
spec = importlib.util.spec_from_file_location("kvittoraknaren_med_opencode", MODULE_PATH)
kvitto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kvitto)


class TestDiscountCode(unittest.TestCase):

    def test_discount_is_case_insensitive_and_trimmed(self):
        result = kvitto.main("vara1 100", 1.25, " rabatt10 ")
        self.assertEqual(result, 112.5)


class TestCurrency(unittest.TestCase):

    def test_genuinely_converts_the_total(self):
        # 230 SEK med 0% moms -> 230 / 11.5 = 20 EUR; 105 SEK -> 105 / 10.5 = 10 USD
        self.assertAlmostEqual(kvitto.main("vara1 230", 1.0, None, "EUR"), 20.0)
        self.assertAlmostEqual(kvitto.main("vara1 105", 1.0, None, "USD"), 10.0)

    def test_currency_is_case_insensitive_and_trimmed(self):
        result = kvitto.main("vara1 230", 1.0, None, " eur ")
        self.assertAlmostEqual(result, 20.0)

    def test_discount_and_moms_then_currency_conversion(self):
        # (100 + 100) * 0.9 * 1.25 = 225 SEK, konverterat till EUR: 225 / 11.5
        result = kvitto.main("vara1 100, vara2 100", 1.25, "RABATT10", "EUR")
        self.assertAlmostEqual(result, 225 / 11.5)

    def test_unsupported_currency_raises_value_error(self):
        with self.assertRaises(ValueError):
            kvitto.main("vara1 100", 1.25, None, "GBP")


if __name__ == "__main__":
    unittest.main(testRunner=ReportRunner())


"""
Job Done zug zug
"""
