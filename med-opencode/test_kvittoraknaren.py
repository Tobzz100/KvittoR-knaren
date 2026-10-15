import importlib.util
import os
import unittest

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
        # 10 % rabatt dras innan momsen: (100 + 100) * 0.9 * 1.25 = 225
        result = kvittoraknaren.main("vara1 100, vara2 100", 1.25, "RABATT10")
        self.assertEqual(result, 225)

    def test_discount_code_is_case_insensitive_and_ignores_surrounding_spaces(self):
        # " rabatt10 " ska tolkas som RABATT10: 100 * 0.9 * 1.25 = 112.5
        result = kvittoraknaren.main("vara1 100", 1.25, " rabatt10 ")
        self.assertEqual(result, 112.5)

    def test_unknown_discount_code_does_not_change_total(self):
        result = kvittoraknaren.main("vara1 100", 1.25, "OGILTIG")
        self.assertEqual(result, 125)

    def test_default_currency_is_sek(self):
        # utan valuta-argument ska resultatet vara oförändrat (bakåtkompatibilitet)
        result = kvittoraknaren.main("vara1 100, vara2 100", 1.25)
        self.assertEqual(result, 250)

    def test_eur_conversion(self):
        # 230 SEK med 0 moms blir 230 / 11.5 = 20 EUR
        result = kvittoraknaren.main("vara1 230", 1.0, None, "EUR")
        self.assertAlmostEqual(result, 20.0)

    def test_usd_conversion(self):
        # 105 SEK med 0 moms blir 105 / 10.5 = 10 USD
        result = kvittoraknaren.main("vara1 105", 1.0, None, "USD")
        self.assertAlmostEqual(result, 10.0)

    def test_discount_and_moms_then_currency(self):
        # (100 + 100) * 0.9 * 1.25 = 225 SEK, konverterat till EUR: 225 / 11.5
        result = kvittoraknaren.main("vara1 100, vara2 100", 1.25, "RABATT10", "EUR")
        self.assertAlmostEqual(result, 225 / 11.5)

    def test_currency_is_case_insensitive_and_ignores_surrounding_spaces(self):
        result = kvittoraknaren.main("vara1 230", 1.0, None, " eur ")
        self.assertAlmostEqual(result, 20.0)

    def test_unknown_currency_raises(self):
        with self.assertRaises(ValueError):
            kvittoraknaren.main("vara1 100", 1.25, None, "GBP")


if __name__ == "__main__":
    unittest.main()
