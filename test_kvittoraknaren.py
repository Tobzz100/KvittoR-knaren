import importlib.util
import io
import os
import runpy
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
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


class TestMedClaudeFormatReceipt(unittest.TestCase):
    """med-claude's format_receipt() returns a 31-character-wide receipt as text - unique to this version."""

    def format_receipt(self, items):
        return MODULES["med-claude"].format_receipt(items)

    def test_example_receipt_matches_exactly(self):
        items = [("Kaffe", 100, 25), ("Bröd", 50, 12), ("Bok", 200, 6)]
        expected = "\n".join([
            "KVITTO",
            "Kaffe                    100,00",
            "Bröd                      50,00",
            "Bok                      200,00",
            "-------------------------------",
            "Summa exkl. moms         350,00",
            "Moms 25 %                 25,00",
            "Moms 12 %                  6,00",
            "Moms 6 %                  12,00",
            "-------------------------------",
            "ATT BETALA               393,00",
        ])
        self.assertEqual(self.format_receipt(items), expected)

    def test_every_line_is_31_characters_wide(self):
        items = [("Kaffe", 100, 25), ("Bröd", 50, 12), ("Bok", 200, 6)]
        for line in self.format_receipt(items).split("\n")[1:]:
            with self.subTest(line=line):
                self.assertEqual(len(line), 31)

    def test_empty_list_gives_inga_varor(self):
        self.assertEqual(self.format_receipt([]), "Inga varor")

    def test_long_name_is_truncated_to_20_chars_ending_with_dots(self):
        line = self.format_receipt([("Ekologiskt mellanrostat kaffe", 100, 25)]).split("\n")[1]
        self.assertEqual(line, "Ekologiskt mellan...     100,00")

    def test_name_of_exactly_20_chars_is_not_truncated(self):
        name = "A" * 20
        line = self.format_receipt([(name, 1, 25)]).split("\n")[1]
        self.assertEqual(line, name + "       1,00")

    def test_only_present_vat_rates_are_shown(self):
        receipt = self.format_receipt([("Bok", 200, 6)])
        self.assertIn("Moms 6 %", receipt)
        self.assertNotIn("Moms 25 %", receipt)
        self.assertNotIn("Moms 12 %", receipt)

    def test_vat_rates_are_sorted_highest_first_and_grouped(self):
        items = [("Bok", 100, 6), ("Kaffe", 100, 25), ("Bröd", 100, 12), ("Te", 100, 25)]
        vat_lines = [l for l in self.format_receipt(items).split("\n") if l.startswith("Moms")]
        self.assertEqual(vat_lines, [
            "Moms 25 %                 50,00",
            "Moms 12 %                 12,00",
            "Moms 6 %                   6,00",
        ])

    def test_amounts_use_decimal_comma_and_two_decimals(self):
        receipt = self.format_receipt([("Godis", 19.9, 12)])
        self.assertIn("Godis                     19,90", receipt)
        self.assertIn("Moms 12 %                  2,39", receipt)
        self.assertIn("ATT BETALA                22,29", receipt)
        self.assertNotIn(".", receipt.replace("exkl.", ""))


class TestMedClaudeVatBreakdown(unittest.TestCase):
    """med-claude's vat_breakdown() returns {VAT rate: VAT amount}, highest rate first."""

    def vat_breakdown(self, items):
        return MODULES["med-claude"].vat_breakdown(items)

    def test_example_items_give_vat_per_rate(self):
        items = [("Kaffe", 100, 25), ("Bröd", 50, 12), ("Bok", 200, 6)]
        self.assertEqual(self.vat_breakdown(items), {25: Decimal("25.00"), 12: Decimal("6.00"), 6: Decimal("12.00")})

    def test_kaffe_100kr_25_percent_and_brod_50kr_12_percent(self):
        # kaffe 100 kr * 25 % = 25 kr moms, bröd 50 kr * 12 % = 6 kr moms
        items = [("Kaffe", 100, 25), ("Bröd", 50, 12)]
        self.assertEqual(self.vat_breakdown(items), {25: 25, 12: 6})

    def test_items_with_same_rate_are_summed(self):
        items = [("Kaffe", 100, 25), ("Te", 40, 25)]
        self.assertEqual(self.vat_breakdown(items), {25: Decimal("35.00")})

    def test_rates_are_ordered_highest_first(self):
        items = [("Bok", 100, 6), ("Kaffe", 100, 25), ("Bröd", 100, 12)]
        self.assertEqual(list(self.vat_breakdown(items)), [25, 12, 6])

    def test_vat_is_rounded_half_up_to_two_decimals(self):
        # 19,90 * 12 % = 2,388 -> 2,39; 0,10 * 25 % = 0,025 -> 0,03
        self.assertEqual(self.vat_breakdown([("Godis", 19.9, 12)]), {12: Decimal("2.39")})
        self.assertEqual(self.vat_breakdown([("Tuggummi", 0.1, 25)]), {25: Decimal("0.03")})

    def test_empty_list_gives_empty_breakdown(self):
        self.assertEqual(self.vat_breakdown([]), {})


class TestMedClaudeCliReceipt(unittest.TestCase):
    """med-claude's __main__ prints a receipt with 25 % moms on every item, prices converted to SEK."""

    MODULE_PATH = os.path.join(VERSIONS["med-claude"]["folder"], "Kvittoräknaren.py")

    def run_cli(self, shopping_list):
        output = io.StringIO()
        with patch("builtins.input", side_effect=[shopping_list]):
            with redirect_stdout(output):
                runpy.run_path(self.MODULE_PATH, run_name="__main__")
        return output.getvalue()

    def test_parse_shopping_list_returns_names_and_sek_prices(self):
        parsed = MODULES["med-claude"].parse_shopping_list("milk 10 SEK, bred 25 EUR, eggs 12, trasig xyz")
        self.assertEqual(parsed, [("milk", 10.0), ("bred", 287.5), ("eggs", 12.0)])

    def test_cli_prints_receipt_with_25_percent_moms(self):
        output = self.run_cli("milk 10 SEK, bred 25 EUR, eggs 12")
        expected = "\n".join([
            "KVITTO",
            "milk                      10,00",
            "bred                     287,50",
            "eggs                      12,00",
            "-------------------------------",
            "Summa exkl. moms         309,50",
            "Moms 25 %                 77,38",
            "-------------------------------",
            "ATT BETALA               386,88",
        ])
        self.assertIn(expected, output)

    def test_cli_with_empty_list_prints_inga_varor(self):
        self.assertIn("Inga varor", self.run_cli(""))


if __name__ == "__main__":
    unittest.main()


"""
Job Done zug zug
"""
