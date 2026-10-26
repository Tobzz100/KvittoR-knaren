import importlib.util
import io
import os
import runpy
import sys
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kvitto_testrunner import ReportRunner

MODULE_PATH = os.path.join(os.path.dirname(__file__), "Kvittoräknaren.py")
spec = importlib.util.spec_from_file_location("kvittoraknaren_med_claude", MODULE_PATH)
kvitto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kvitto)


class TestDiscountCode(unittest.TestCase):

    def test_discount_is_case_sensitive_exact_match_only(self):
        # bug/quirk: med-claude does a literal dict lookup with no strip/upper,
        # so " rabatt10 " never matches "RABATT10" and no discount is applied
        with redirect_stdout(io.StringIO()):
            result = kvitto.main("vara1 100", 1.25, " rabatt10 ")
        self.assertEqual(result, 125)

    def test_unknown_discount_code_gives_no_discount_and_prints_message(self):
        # koden finns inte i DISCOUNT_CODES, så ett meddelande skrivs ut och fullt pris returneras
        with redirect_stdout(io.StringIO()) as out:
            result = kvitto.main("vara1 100", 1.25, "FINNSINTE")
        self.assertEqual(result, 125)
        self.assertIn("Discount code 'FINNSINTE' does not exist, no discount applied", out.getvalue())

    def test_lookup_discount_returns_rate_for_known_code(self):
        self.assertEqual(kvitto.lookup_discount("RABATT10"), 0.10)

    def test_lookup_discount_returns_zero_for_missing_or_unknown_code(self):
        with redirect_stdout(io.StringIO()) as out:
            for code in (None, "", "FINNSINTE"):
                with self.subTest(code=code):
                    self.assertEqual(kvitto.lookup_discount(code), 0)
        self.assertEqual(out.getvalue().count("does not exist"), 1)

    def test_valid_or_missing_discount_code_prints_no_message(self):
        for code in ("RABATT10", None, ""):
            with self.subTest(code=code):
                with redirect_stdout(io.StringIO()) as out:
                    kvitto.main("vara1 100", 1.25, code)
                self.assertEqual(out.getvalue(), "")


class TestCurrency(unittest.TestCase):

    def test_single_item_in_eur_converted_to_sek(self):
        # 10 EUR * 11.5 = 115 kr, sedan 25% moms = 143.75 kr
        result = kvitto.main("vara1 10 EUR", 1.25)
        self.assertEqual(result, 143.75)

    def test_converts_per_item_currencies_and_sums_in_sek(self):
        # 100 SEK + 10 EUR (115 kr) + 10 USD (105 kr) = 320 kr, sedan 25% moms = 400 kr
        result = kvitto.main("vara1 100 SEK, vara2 10 EUR, vara3 10 USD", 1.25)
        self.assertEqual(result, 400)

    def test_mixed_currency_with_implicit_sek_item(self):
        # 10 SEK + 25 EUR (287.5 kr) + 12 SEK (ingen valuta angiven) = 309.5 kr, sedan 25% moms = 386.875 kr
        result = kvitto.main("milk 10 SEK, bred 25 EUR, eggs 12", 1.25)
        self.assertEqual(result, 386.875)

    def test_unknown_per_item_currency_code_causes_item_to_be_skipped(self):
        result = kvitto.main("vara1 100 XXX, vara2 100 SEK", 1.25)
        self.assertEqual(result, 125)

    def test_target_currency_usd(self):
        # 100 SEK -> 125 kr efter moms -> 125 / 10.5 USD
        result = kvitto.main("vara1 100", 1.25, target_currency="USD")
        self.assertAlmostEqual(result, 125 / 10.5)

    def test_discount_with_multiple_currencies(self):
        # (100 SEK + 10 EUR (115 kr)) = 215 kr, -10% rabatt = 193.5 kr, sedan 25% moms = 241.875 kr
        result = kvitto.main("vara1 100 SEK, vara2 10 EUR", 1.25, "RABATT10")
        self.assertEqual(result, 241.875)

    def test_unsupported_target_currency_raises_keyerror(self):
        # bug: target_currency is never validated, so an unknown code crashes instead of a clean error
        with self.assertRaises(KeyError):
            kvitto.main("vara1 100", 1.25, target_currency="GBP")


class TestFormatReceipt(unittest.TestCase):
    """format_receipt() returns a 31-character-wide receipt as text."""

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
        self.assertEqual(kvitto.format_receipt(items), expected)

    def test_every_line_is_31_characters_wide(self):
        items = [("Kaffe", 100, 25), ("Bröd", 50, 12), ("Bok", 200, 6)]
        for line in kvitto.format_receipt(items).split("\n")[1:]:
            with self.subTest(line=line):
                self.assertEqual(len(line), 31)

    def test_empty_list_gives_inga_varor(self):
        self.assertEqual(kvitto.format_receipt([]), "Inga varor")

    def test_long_name_is_truncated_to_20_chars_ending_with_dots(self):
        line = kvitto.format_receipt([("Ekologiskt mellanrostat kaffe", 100, 25)]).split("\n")[1]
        self.assertEqual(line, "Ekologiskt mellan...     100,00")

    def test_name_of_exactly_20_chars_is_not_truncated(self):
        name = "A" * 20
        line = kvitto.format_receipt([(name, 1, 25)]).split("\n")[1]
        self.assertEqual(line, name + "       1,00")

    def test_only_present_vat_rates_are_shown(self):
        receipt = kvitto.format_receipt([("Bok", 200, 6)])
        self.assertIn("Moms 6 %", receipt)
        self.assertNotIn("Moms 25 %", receipt)
        self.assertNotIn("Moms 12 %", receipt)

    def test_vat_rates_are_sorted_highest_first_and_grouped(self):
        items = [("Bok", 100, 6), ("Kaffe", 100, 25), ("Bröd", 100, 12), ("Te", 100, 25)]
        vat_lines = [l for l in kvitto.format_receipt(items).split("\n") if l.startswith("Moms")]
        self.assertEqual(vat_lines, [
            "Moms 25 %                 50,00",
            "Moms 12 %                 12,00",
            "Moms 6 %                   6,00",
        ])

    def test_discount_is_shown_and_vat_is_calculated_on_discounted_prices(self):
        # -10 %: kaffe 100 -> 90, bröd 50 -> 45; moms 90 * 25 % = 22,50 och 45 * 12 % = 5,40
        receipt = kvitto.format_receipt([("Kaffe", 100, 25), ("Bröd", 50, 12)], 0.10)
        self.assertIn("\n".join([
            "-------------------------------",
            "Rabatt 10 %              -15,00",
            "Summa exkl. moms         135,00",
            "Moms 25 %                 22,50",
            "Moms 12 %                  5,40",
            "-------------------------------",
            "ATT BETALA               162,90",
        ]), receipt)

    def test_item_lines_show_prices_before_discount(self):
        receipt = kvitto.format_receipt([("Kaffe", 100, 25)], 0.10)
        self.assertIn("Kaffe                    100,00", receipt)

    def test_discounted_prices_are_rounded_to_ore_so_the_receipt_adds_up(self):
        # 19,95 * 0,9 = 17,955 -> 17,96, rabatten blir alltså 1,99 och inte 1,995
        receipt = kvitto.format_receipt([("Godis", 19.95, 12)], 0.10)
        self.assertIn("Rabatt 10 %               -1,99", receipt)
        self.assertIn("Summa exkl. moms          17,96", receipt)

    def test_no_discount_line_without_discount(self):
        self.assertNotIn("Rabatt", kvitto.format_receipt([("Kaffe", 100, 25)]))
        self.assertNotIn("Rabatt", kvitto.format_receipt([("Kaffe", 100, 25)], 0))

    def test_amounts_use_decimal_comma_and_two_decimals(self):
        receipt = kvitto.format_receipt([("Godis", 19.9, 12)])
        self.assertIn("Godis                     19,90", receipt)
        self.assertIn("Moms 12 %                  2,39", receipt)
        self.assertIn("ATT BETALA                22,29", receipt)
        self.assertNotIn(".", receipt.replace("exkl.", ""))


class TestVatBreakdown(unittest.TestCase):
    """vat_breakdown() returns {VAT rate: VAT amount}, highest rate first."""

    def test_example_items_give_vat_per_rate(self):
        items = [("Kaffe", 100, 25), ("Bröd", 50, 12), ("Bok", 200, 6)]
        self.assertEqual(kvitto.vat_breakdown(items), {25: Decimal("25.00"), 12: Decimal("6.00"), 6: Decimal("12.00")})

    def test_kaffe_100kr_25_percent_and_brod_50kr_12_percent(self):
        # kaffe 100 kr * 25 % = 25 kr moms, bröd 50 kr * 12 % = 6 kr moms
        items = [("Kaffe", 100, 25), ("Bröd", 50, 12)]
        self.assertEqual(kvitto.vat_breakdown(items), {25: 25, 12: 6})

    def test_all_three_swedish_vat_rates_with_several_items_each(self):
        # 25 %: (100 + 40) * 0,25 = 35,00; 12 %: (50 + 20) * 0,12 = 8,40; 6 %: (200 + 30) * 0,06 = 13,80
        items = [
            ("Kaffe", 100, 25), ("Bröd", 50, 12), ("Bok", 200, 6),
            ("Te", 40, 25), ("Mjölk", 20, 12), ("Tidning", 30, 6),
        ]
        breakdown = kvitto.vat_breakdown(items)
        self.assertEqual(breakdown, {25: Decimal("35.00"), 12: Decimal("8.40"), 6: Decimal("13.80")})
        self.assertEqual(list(breakdown), [25, 12, 6])

    def test_items_with_same_rate_are_summed(self):
        items = [("Kaffe", 100, 25), ("Te", 40, 25)]
        self.assertEqual(kvitto.vat_breakdown(items), {25: Decimal("35.00")})

    def test_rates_are_ordered_highest_first(self):
        items = [("Bok", 100, 6), ("Kaffe", 100, 25), ("Bröd", 100, 12)]
        self.assertEqual(list(kvitto.vat_breakdown(items)), [25, 12, 6])

    def test_vat_is_rounded_half_up_to_two_decimals(self):
        # 19,90 * 12 % = 2,388 -> 2,39; 0,10 * 25 % = 0,025 -> 0,03
        self.assertEqual(kvitto.vat_breakdown([("Godis", 19.9, 12)]), {12: Decimal("2.39")})
        self.assertEqual(kvitto.vat_breakdown([("Tuggummi", 0.1, 25)]), {25: Decimal("0.03")})

    def test_empty_list_gives_empty_breakdown(self):
        self.assertEqual(kvitto.vat_breakdown([]), {})

    def test_zero_percent_vat_is_valid_and_gives_zero_vat(self):
        # 0 % moms finns i Sverige (t.ex. viss export och sjukvård)
        items = [("Kaffe", 100, 25), ("Export", 300, 0)]
        self.assertEqual(kvitto.vat_breakdown(items), {25: Decimal("25.00"), 0: Decimal("0.00")})

    def test_invalid_vat_rate_raises_value_error(self):
        # Sverige har bara momssatserna 25, 12 och 6 %; alla andra satser ska ge ett fel
        for rate in (20, 12.5, -6):
            with self.subTest(rate=rate):
                with self.assertRaises(ValueError):
                    kvitto.vat_breakdown([("Kaffe", 100, 25), ("Konstig vara", 100, rate)])


class TestInvalidPrices(unittest.TestCase):
    """nan, inf, negative and non-numeric prices are rejected instead of giving NaN or negative VAT."""

    INVALID_PRICES = (float("nan"), float("inf"), -100, "abc")

    def test_parse_shopping_list_skips_nan_inf_and_negative_prices(self):
        with redirect_stdout(io.StringIO()) as out:
            parsed = kvitto.parse_shopping_list("mjölk nan, ost inf, bröd -50, smör -5 EUR, kaffe 100")
        self.assertEqual(parsed, [("kaffe", 100.0)])
        self.assertEqual(out.getvalue().count("Skipping invalid item"), 4)

    def test_parse_shopping_list_allows_zero_price(self):
        self.assertEqual(kvitto.parse_shopping_list("gratisprov 0"), [("gratisprov", 0.0)])

    def test_main_ignores_nan_and_negative_prices(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(kvitto.main("vara1 100, vara2 nan, vara3 -50", 1.25), 125)

    def test_vat_breakdown_rejects_invalid_prices_with_value_error(self):
        for price in self.INVALID_PRICES:
            with self.subTest(price=price):
                with self.assertRaisesRegex(ValueError, "Ogiltigt pris"):
                    kvitto.vat_breakdown([("Kaffe", 100, 25), ("Konstig vara", price, 25)])

    def test_format_receipt_rejects_invalid_prices_with_value_error(self):
        for price in self.INVALID_PRICES:
            with self.subTest(price=price):
                with self.assertRaisesRegex(ValueError, "Ogiltigt pris"):
                    kvitto.format_receipt([("Konstig vara", price, 25)])

    def test_zero_price_is_valid(self):
        self.assertEqual(kvitto.vat_breakdown([("Gratisprov", 0, 25)]), {25: Decimal("0.00")})


class TestInventory(unittest.TestCase):
    """items_from_inventory() takes price and VAT rate from INVENTORY, never from the input."""

    def test_known_items_get_price_and_vat_rate_from_inventory(self):
        self.assertEqual(
            kvitto.items_from_inventory("Mjölk, Bok, Tvål"),
            [("Mjölk", 15, 12), ("Bok", 200, 6), ("Tvål", 20, 25)],
        )

    def test_names_are_matched_case_insensitively_and_trimmed(self):
        self.assertEqual(kvitto.items_from_inventory("  mjölk ,BRÖD"), [("Mjölk", 15, 12), ("Bröd", 30, 12)])

    def test_same_item_twice_gives_two_lines(self):
        self.assertEqual(kvitto.items_from_inventory("kaffe, kaffe"), [("Kaffe", 70, 12), ("Kaffe", 70, 12)])

    def test_unknown_item_is_skipped_with_warning(self):
        with redirect_stdout(io.StringIO()) as out:
            items = kvitto.items_from_inventory("mjölk, guld")
        self.assertEqual(items, [("Mjölk", 15, 12)])
        self.assertIn("Skipping unknown item: 'guld'", out.getvalue())

    def test_customer_cannot_set_own_price_or_vat_rate(self):
        # "tvål 1" or "tvål 0%" is not an inventory name, so it is skipped instead of getting a lower price or rate
        with redirect_stdout(io.StringIO()) as out:
            items = kvitto.items_from_inventory("tvål 1, tvål 0%")
        self.assertEqual(items, [])
        self.assertEqual(out.getvalue().count("Skipping unknown item"), 2)

    def test_empty_list_gives_no_items(self):
        self.assertEqual(kvitto.items_from_inventory(""), [])

    def test_every_inventory_item_has_valid_price_and_vat_rate(self):
        for name, (price, vat_percent) in kvitto.INVENTORY.items():
            with self.subTest(name=name):
                self.assertIn(vat_percent, kvitto.VAT_RATES)
                self.assertGreaterEqual(price, 0)


class TestCliReceipt(unittest.TestCase):
    """__main__ lists the inventory and prints a receipt with each item's VAT rate from INVENTORY."""

    def run_cli(self, shopping_list, discount_code=""):
        output = io.StringIO()
        with patch("builtins.input", side_effect=[shopping_list, discount_code]):
            with redirect_stdout(output):
                runpy.run_path(MODULE_PATH, run_name="__main__")
        return output.getvalue()

    def test_parse_shopping_list_returns_names_and_sek_prices(self):
        parsed = kvitto.parse_shopping_list("milk 10 SEK, bred 25 EUR, eggs 12, trasig xyz")
        self.assertEqual(parsed, [("milk", 10.0), ("bred", 287.5), ("eggs", 12.0)])

    def test_cli_lists_available_items(self):
        self.assertIn("Available items: Mjölk, Bröd, Ägg, Kaffe, Tvål, Batterier, Bok, Tidning", self.run_cli(""))

    def test_cli_prints_receipt_with_inventory_vat_rates(self):
        # 15 * 12 % = 1,80; 200 * 6 % = 12,00; 20 * 25 % = 5,00; 235 + 18,80 = 253,80
        output = self.run_cli("mjölk, bok, tvål")
        expected = "\n".join([
            "KVITTO",
            "Mjölk                     15,00",
            "Bok                      200,00",
            "Tvål                      20,00",
            "-------------------------------",
            "Summa exkl. moms         235,00",
            "Moms 25 %                  5,00",
            "Moms 12 %                  1,80",
            "Moms 6 %                  12,00",
            "-------------------------------",
            "ATT BETALA               253,80",
        ])
        self.assertIn(expected, output)

    def test_cli_applies_discount_code(self):
        # -10 %: mjölk 13,50, bok 180,00, tvål 18,00 = 211,50; moms 4,50 + 1,62 + 10,80 = 16,92
        output = self.run_cli("mjölk, bok, tvål", "RABATT10")
        expected = "\n".join([
            "-------------------------------",
            "Rabatt 10 %              -23,50",
            "Summa exkl. moms         211,50",
            "Moms 25 %                  4,50",
            "Moms 12 %                  1,62",
            "Moms 6 %                  10,80",
            "-------------------------------",
            "ATT BETALA               228,42",
        ])
        self.assertIn(expected, output)

    def test_cli_unknown_discount_code_prints_message_and_charges_full_price(self):
        output = self.run_cli("mjölk, bok, tvål", "FINNSINTE")
        self.assertIn("Discount code 'FINNSINTE' does not exist, no discount applied", output)
        self.assertNotIn("Rabatt", output)
        self.assertIn("ATT BETALA               253,80", output)

    def test_cli_skips_unknown_items(self):
        output = self.run_cli("mjölk, guld")
        self.assertIn("Skipping unknown item: 'guld'", output)
        self.assertIn("ATT BETALA                16,80", output)

    def test_cli_with_empty_list_prints_inga_varor(self):
        self.assertIn("Inga varor", self.run_cli(""))


if __name__ == "__main__":
    unittest.main(testRunner=ReportRunner())


"""
Job Done zug zug
"""
