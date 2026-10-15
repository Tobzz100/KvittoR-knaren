import importlib.util
import io
import os
import runpy
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

REPO_ROOT = os.path.dirname(__file__)

VERSIONS = {
    "root": {"folder": REPO_ROOT, "supports_discount": False, "supports_currency": False},
    "med-claude": {"folder": os.path.join(REPO_ROOT, "med-claude"), "supports_discount": True, "supports_currency": True},
    "med-copilot": {"folder": os.path.join(REPO_ROOT, "med-copilot"), "supports_discount": True, "supports_currency": True},
    "med-opencode": {"folder": os.path.join(REPO_ROOT, "med-opencode"), "supports_discount": True, "supports_currency": True},
}

DISCOUNT_VERSIONS = [name for name, info in VERSIONS.items() if info["supports_discount"]]


def load_module(name, folder):
    module_path = os.path.join(folder, "Kvittoräknaren.py")
    spec = importlib.util.spec_from_file_location("kvittoraknaren_" + name.replace("-", "_"), module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULES = {name: load_module(name, info["folder"]) for name, info in VERSIONS.items()}


class TestAllVersionsCommonBehavior(unittest.TestCase):
    """Behavior every version agrees on, checked once per version via subTest."""

    def test_two_items_100kr_25_percent_moms(self):
        # kontrollerar att två varor à 100 kr med 25 % moms blir 250 kr
        for name, module in MODULES.items():
            with self.subTest(version=name):
                self.assertEqual(module.main("vara1 100, vara2 100", 1.25), 250)

    def test_malformed_item_is_skipped_not_raised(self):
        for name, module in MODULES.items():
            with self.subTest(version=name):
                self.assertEqual(module.main("vara1 100, vara2 inteettpris", 1.25), 125)

    def test_discount_code_rabatt10_reduces_total_by_10_percent_before_moms(self):
        # 200 kr - 10% rabatt = 180 kr, sedan 25% moms = 225 kr
        for name in DISCOUNT_VERSIONS:
            with self.subTest(version=name):
                result = MODULES[name].main("vara1 100, vara2 100", 1.25, "RABATT10")
                self.assertEqual(result, 225)

    def test_unknown_discount_code_gives_no_discount(self):
        for name in DISCOUNT_VERSIONS:
            with self.subTest(version=name):
                result = MODULES[name].main("vara1 100, vara2 100", 1.25, "FELKOD")
                self.assertEqual(result, 250)


class TestDiscountCodeQuirksPerVersion(unittest.TestCase):
    """med-copilot/med-opencode trim+uppercase the discount code; med-claude requires an exact match."""

    def test_med_copilot_and_med_opencode_discount_is_case_insensitive_and_trimmed(self):
        for name in ("med-copilot", "med-opencode"):
            with self.subTest(version=name):
                result = MODULES[name].main("vara1 100", 1.25, " rabatt10 ")
                self.assertEqual(result, 112.5)

    def test_med_claude_discount_is_case_sensitive_exact_match_only(self):
        # bug/quirk: med-claude does a literal dict lookup with no strip/upper,
        # so " rabatt10 " never matches "RABATT10" and no discount is applied
        result = MODULES["med-claude"].main("vara1 100", 1.25, " rabatt10 ")
        self.assertEqual(result, 125)


class TestCurrencyQuirksPerVersion(unittest.TestCase):
    """Currency handling is where the three AI versions diverge most - including real bugs."""

    def test_med_claude_single_item_in_eur_converted_to_sek(self):
        # 10 EUR * 11.5 = 115 kr, sedan 25% moms = 143.75 kr
        result = MODULES["med-claude"].main("vara1 10 EUR", 1.25)
        self.assertEqual(result, 143.75)

    def test_med_claude_converts_per_item_currencies_and_sums_in_sek(self):
        # 100 SEK + 10 EUR (115 kr) + 10 USD (105 kr) = 320 kr, sedan 25% moms = 400 kr
        result = MODULES["med-claude"].main("vara1 100 SEK, vara2 10 EUR, vara3 10 USD", 1.25)
        self.assertEqual(result, 400)

    def test_med_claude_mixed_currency_with_implicit_sek_item(self):
        # 10 SEK + 25 EUR (287.5 kr) + 12 SEK (ingen valuta angiven) = 309.5 kr, sedan 25% moms = 386.875 kr
        result = MODULES["med-claude"].main("milk 10 SEK, bred 25 EUR, eggs 12", 1.25)
        self.assertEqual(result, 386.875)

    def test_med_claude_unknown_per_item_currency_code_causes_item_to_be_skipped(self):
        result = MODULES["med-claude"].main("vara1 100 XXX, vara2 100 SEK", 1.25)
        self.assertEqual(result, 125)

    def test_med_claude_target_currency_usd(self):
        # 100 SEK -> 125 kr efter moms -> 125 / 10.5 USD
        result = MODULES["med-claude"].main("vara1 100", 1.25, target_currency="USD")
        self.assertAlmostEqual(result, 125 / 10.5)

    def test_med_claude_discount_with_multiple_currencies(self):
        # (100 SEK + 10 EUR (115 kr)) = 215 kr, -10% rabatt = 193.5 kr, sedan 25% moms = 241.875 kr
        result = MODULES["med-claude"].main("vara1 100 SEK, vara2 10 EUR", 1.25, "RABATT10")
        self.assertEqual(result, 241.875)

    def test_med_claude_unsupported_target_currency_raises_keyerror(self):
        # bug: target_currency is never validated, so an unknown code crashes instead of a clean error
        with self.assertRaises(KeyError):
            MODULES["med-claude"].main("vara1 100", 1.25, target_currency="GBP")

    def test_med_copilot_validates_currency_but_never_actually_converts_the_total(self):
        # bug: the result is identical regardless of which supported currency is chosen
        for currency in ("SEK", "EUR", "USD"):
            with self.subTest(currency=currency):
                result = MODULES["med-copilot"].main("vara1 100", 1.25, currency=currency)
                self.assertEqual(result, 125)

    def test_med_copilot_currency_is_case_insensitive_and_trimmed(self):
        result = MODULES["med-copilot"].main("vara1 100", 1.25, currency=" eur ")
        self.assertEqual(result, 125)

    def test_med_copilot_unsupported_currency_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "Currency must be SEK, EUR, or USD"):
            MODULES["med-copilot"].main("vara1 100", 1.25, currency="GBP")

    def test_med_opencode_genuinely_converts_the_total(self):
        # 230 SEK med 0% moms -> 230 / 11.5 = 20 EUR; 105 SEK -> 105 / 10.5 = 10 USD
        self.assertAlmostEqual(MODULES["med-opencode"].main("vara1 230", 1.0, None, "EUR"), 20.0)
        self.assertAlmostEqual(MODULES["med-opencode"].main("vara1 105", 1.0, None, "USD"), 10.0)

    def test_med_opencode_currency_is_case_insensitive_and_trimmed(self):
        result = MODULES["med-opencode"].main("vara1 230", 1.0, None, " eur ")
        self.assertAlmostEqual(result, 20.0)

    def test_med_opencode_discount_and_moms_then_currency_conversion(self):
        # (100 + 100) * 0.9 * 1.25 = 225 SEK, konverterat till EUR: 225 / 11.5
        result = MODULES["med-opencode"].main("vara1 100, vara2 100", 1.25, "RABATT10", "EUR")
        self.assertAlmostEqual(result, 225 / 11.5)

    def test_med_opencode_unsupported_currency_raises_value_error(self):
        with self.assertRaises(ValueError):
            MODULES["med-opencode"].main("vara1 100", 1.25, None, "GBP")


class TestMedCopilotCliBehavior(unittest.TestCase):
    """med-copilot's __main__ loop re-prompts on an invalid currency - unique to this version."""

    MODULE_PATH = os.path.join(VERSIONS["med-copilot"]["folder"], "Kvittoräknaren.py")

    def test_cli_displays_selected_currency_with_total(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["vara1 100", "", "USD"]):
            with redirect_stdout(output):
                runpy.run_path(self.MODULE_PATH, run_name="__main__")
        self.assertIn("125.00 USD", output.getvalue())

    def test_cli_defaults_to_sek_when_currency_is_blank(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["vara1 100", "", ""]):
            with redirect_stdout(output):
                runpy.run_path(self.MODULE_PATH, run_name="__main__")
        self.assertIn("125.00 SEK", output.getvalue())

    def test_cli_reprompts_for_unsupported_currency(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["vara1 100", "", "GBP", "EUR"]):
            with redirect_stdout(output):
                runpy.run_path(self.MODULE_PATH, run_name="__main__")
        self.assertIn("Currency must be SEK, EUR, or USD.", output.getvalue())
        self.assertIn("125.00 EUR", output.getvalue())


if __name__ == "__main__":
    unittest.main()


"""
Job Done zug zug
"""
