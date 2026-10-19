import importlib.util
import os
import unittest

from kvitto_testrunner import ReportRunner

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
    """Behavior every version agrees on, checked once per version via subTest.

    Version-specific tests live in each folder's own test_kvittoraknaren.py.
    """

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


if __name__ == "__main__":
    unittest.main(testRunner=ReportRunner())


"""
Job Done zug zug
"""
