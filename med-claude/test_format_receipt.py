import importlib.util
import os
import unittest

MODULE_PATH = os.path.join(os.path.dirname(__file__), "Kvittoräknaren.py")
spec = importlib.util.spec_from_file_location("kvittoraknaren_med_claude", MODULE_PATH)
kvitto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kvitto)


class TestFormatReceipt(unittest.TestCase):

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
        receipt = kvitto.format_receipt([("Ekologiskt mellanrostat kaffe", 100, 25)])
        line = receipt.split("\n")[1]
        self.assertEqual(line, "Ekologiskt mellan...     100,00")
        self.assertEqual(len(line[:20]), 20)

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

    def test_amounts_use_decimal_comma_and_two_decimals(self):
        receipt = kvitto.format_receipt([("Godis", 19.9, 12)])
        self.assertIn("Godis                     19,90", receipt)
        self.assertIn("Moms 12 %                  2,39", receipt)
        self.assertIn("ATT BETALA                22,29", receipt)
        self.assertNotIn(".", receipt.replace("exkl.", ""))


if __name__ == "__main__":
    unittest.main()


"""
Job Done zug zug
"""
