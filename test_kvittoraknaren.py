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


if __name__ == "__main__":
    unittest.main()
