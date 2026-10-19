import importlib.util
import io
import os
import runpy
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

MODULE_PATH = os.path.join(os.path.dirname(__file__), "Kvittoräknaren.py")
spec = importlib.util.spec_from_file_location("kvittoraknaren_med_copilot", MODULE_PATH)
kvitto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kvitto)


class TestDiscountCode(unittest.TestCase):

    def test_discount_is_case_insensitive_and_trimmed(self):
        result = kvitto.main("vara1 100", 1.25, " rabatt10 ")
        self.assertEqual(result, 112.5)


class TestCurrency(unittest.TestCase):

    def test_validates_currency_but_never_actually_converts_the_total(self):
        # bug: the result is identical regardless of which supported currency is chosen
        for currency in ("SEK", "EUR", "USD"):
            with self.subTest(currency=currency):
                result = kvitto.main("vara1 100", 1.25, currency=currency)
                self.assertEqual(result, 125)

    def test_currency_is_case_insensitive_and_trimmed(self):
        result = kvitto.main("vara1 100", 1.25, currency=" eur ")
        self.assertEqual(result, 125)

    def test_unsupported_currency_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "Currency must be SEK, EUR, or USD"):
            kvitto.main("vara1 100", 1.25, currency="GBP")


class TestCliBehavior(unittest.TestCase):
    """__main__ loop re-prompts on an invalid currency - unique to this version."""

    def run_cli(self, inputs):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs):
            with redirect_stdout(output):
                runpy.run_path(MODULE_PATH, run_name="__main__")
        return output.getvalue()

    def test_cli_displays_selected_currency_with_total(self):
        self.assertIn("125.00 USD", self.run_cli(["vara1 100", "", "USD"]))

    def test_cli_defaults_to_sek_when_currency_is_blank(self):
        self.assertIn("125.00 SEK", self.run_cli(["vara1 100", "", ""]))

    def test_cli_reprompts_for_unsupported_currency(self):
        output = self.run_cli(["vara1 100", "", "GBP", "EUR"])
        self.assertIn("Currency must be SEK, EUR, or USD.", output)
        self.assertIn("125.00 EUR", output)


if __name__ == "__main__":
    unittest.main()


"""
Job Done zug zug
"""
