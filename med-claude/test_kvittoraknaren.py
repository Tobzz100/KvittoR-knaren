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

    def test_discount_code_applied_before_moms(self):
        # 200 kr - 10% rabatt = 180 kr, sedan 25% moms = 225 kr
        result = kvittoraknaren.main("vara1 100, vara2 100", 1.25, "RABATT10")
        self.assertEqual(result, 225)

    def test_invalid_discount_code_gives_no_discount(self):
        result = kvittoraknaren.main("vara1 100, vara2 100", 1.25, "FELKOD")
        self.assertEqual(result, 250)

    def test_no_discount_code_gives_no_discount(self):
        result = kvittoraknaren.main("vara1 100, vara2 100", 1.25)
        self.assertEqual(result, 250)

    def test_item_in_eur_converted_to_sek(self):
        # 10 EUR * 11.5 = 115 kr, sedan 25% moms = 143.75 kr
        result = kvittoraknaren.main("vara1 10 EUR", 1.25)
        self.assertEqual(result, 143.75)

    def test_mixed_currencies_summed_in_sek(self):
        # 100 SEK + 10 EUR (115 kr) + 10 USD (105 kr) = 320 kr, sedan 25% moms = 400 kr
        result = kvittoraknaren.main("vara1 100 SEK, vara2 10 EUR, vara3 10 USD", 1.25)
        self.assertEqual(result, 400)

    def test_target_currency_usd(self):
        # 100 SEK -> 125 kr efter moms -> 125 / 10.5 USD
        result = kvittoraknaren.main("vara1 100", 1.25, target_currency="USD")
        self.assertAlmostEqual(result, 125 / 10.5)

    def test_discount_with_multiple_currencies(self):
        # (100 SEK + 10 EUR (115 kr)) = 215 kr, -10% rabatt = 193.5 kr, sedan 25% moms = 241.875 kr
        result = kvittoraknaren.main("vara1 100 SEK, vara2 10 EUR", 1.25, "RABATT10")
        self.assertEqual(result, 241.875)

    def test_unknown_currency_code_is_skipped(self):
        result = kvittoraknaren.main("vara1 100 XXX, vara2 100 SEK", 1.25)
        self.assertEqual(result, 125)


if __name__ == "__main__":
    unittest.main()
