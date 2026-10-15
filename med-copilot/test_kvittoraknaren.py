import importlib.util
import io
import os
import runpy
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

MODULE_PATH = os.path.join(os.path.dirname(__file__), "Kvittoräknaren.py")
spec = importlib.util.spec_from_file_location("kvittoraknaren", MODULE_PATH)
kvittoraknaren = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kvittoraknaren)


class TestKvittoraknaren(unittest.TestCase):
    def test_two_items_100kr_25_percent_moms(self):
        # kontrollerar att två varor à 100 kr med 25 % moms blir 250 kr
        result = kvittoraknaren.main("vara1 100, vara2 100", 1.25)
        self.assertEqual(result, 250)

    def test_discount_code_reduces_receipt_by_10_percent_before_vat(self):
        result = kvittoraknaren.main("vara1 100, vara2 100", 1.25, "RABATT10")
        self.assertEqual(result, 225)

    def test_discount_code_is_case_insensitive_and_ignores_surrounding_spaces(self):
        result = kvittoraknaren.main("vara1 100", 1.25, " rabatt10 ")
        self.assertEqual(result, 112.5)

    def test_unknown_discount_code_does_not_change_total(self):
        result = kvittoraknaren.main("vara1 100", 1.25, "OGILTIG")
        self.assertEqual(result, 125)

    def test_supported_currencies_are_accepted(self):
        for currency in ("SEK", "EUR", "USD"):
            with self.subTest(currency=currency):
                result = kvittoraknaren.main("vara1 100", 1.25, currency=currency)
                self.assertEqual(result, 125)

    def test_currency_is_case_insensitive_and_ignores_surrounding_spaces(self):
        result = kvittoraknaren.main("vara1 100", 1.25, currency=" eur ")
        self.assertEqual(result, 125)

    def test_unsupported_currency_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "Currency must be SEK, EUR, or USD"):
            kvittoraknaren.main("vara1 100", 1.25, currency="GBP")

    def test_cli_displays_selected_currency_with_total(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["vara1 100", "", "USD"]):
            with redirect_stdout(output):
                runpy.run_path(MODULE_PATH, run_name="__main__")
        self.assertIn("125.00 USD", output.getvalue())

    def test_cli_defaults_to_sek_when_currency_is_blank(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["vara1 100", "", ""]):
            with redirect_stdout(output):
                runpy.run_path(MODULE_PATH, run_name="__main__")
        self.assertIn("125.00 SEK", output.getvalue())

    def test_cli_reprompts_for_unsupported_currency(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["vara1 100", "", "GBP", "EUR"]):
            with redirect_stdout(output):
                runpy.run_path(MODULE_PATH, run_name="__main__")
        self.assertIn("Currency must be SEK, EUR, or USD.", output.getvalue())
        self.assertIn("125.00 EUR", output.getvalue())


if __name__ == "__main__":
    unittest.main()
