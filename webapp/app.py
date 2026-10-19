import importlib.util
import os
import subprocess
import sys

from flask import Flask, jsonify, render_template, request

APP_DIR = os.path.dirname(__file__)

VERSIONS = [
    {
        "key": "root",
        "label": "Baseline (original)",
        "folder": "..",
        "supports_discount": False,
        "supports_currency": False,
        "currency_param": None,
        "list_help": "Comma-separated 'item price' pairs, e.g. milk 10, bread 20",
        "quirk": "No discount or currency support; VAT is applied per item inside the loop.",
    },
    {
        "key": "med-claude",
        "label": "Claude",
        "folder": "../med-claude",
        "supports_discount": True,
        "supports_currency": True,
        "currency_param": "target_currency",
        "list_help": "Comma-separated 'item price [CURRENCY]' pairs, e.g. milk 10 SEK, bread 20 EUR, eggs 15",
        "quirk": "Supports per-item currency and converts the total to your target currency "
        "- but an unsupported target currency crashes with an internal error "
        "(shown here as a friendly message instead).",
    },
    {
        "key": "med-copilot",
        "label": "Copilot",
        "folder": "../med-copilot",
        "supports_discount": True,
        "supports_currency": True,
        "currency_param": "currency",
        "list_help": "Comma-separated 'item price' pairs, e.g. milk 10, bread 20",
        "quirk": "Validates the currency and rejects unknown codes, but never actually "
        "converts the total - try SEK vs USD and compare.",
    },
    {
        "key": "med-opencode",
        "label": "OpenCode",
        "folder": "../med-opencode",
        "supports_discount": True,
        "supports_currency": True,
        "currency_param": "currency",
        "list_help": "Comma-separated 'item price' pairs, e.g. milk 10, bread 20",
        "quirk": "Validates currency and genuinely converts the total using its exchange-rate table.",
    },
]

_VERSIONS_BY_KEY = {entry["key"]: entry for entry in VERSIONS}

app = Flask(__name__)


def get_version(key):
    return _VERSIONS_BY_KEY.get(key)


def version_folder_abs(entry):
    return os.path.join(APP_DIR, entry["folder"])


def load_version_module(entry):
    module_path = os.path.join(version_folder_abs(entry), "Kvittoräknaren.py")
    spec = importlib.util.spec_from_file_location("kvittoraknaren_" + entry["key"], module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_version_info(entry):
    return {
        "key": entry["key"],
        "label": entry["label"],
        "supports_discount": entry["supports_discount"],
        "supports_currency": entry["supports_currency"],
        "currency_param": entry["currency_param"],
        "list_help": entry["list_help"],
        "quirk": entry["quirk"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/versions")
def api_versions():
    return jsonify([public_version_info(entry) for entry in VERSIONS])


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    data = request.get_json(silent=True) or {}

    entry = get_version(data.get("version"))
    if entry is None:
        return jsonify({"error": "Unknown version"}), 400

    try:
        moms_percent = float(data.get("moms", 25))
    except (TypeError, ValueError):
        return jsonify({"error": "VAT must be a number"}), 400

    kwargs = {
        "shoppingList": data.get("shopping_list", ""),
        "moms": 1 + moms_percent / 100,
    }

    discount_code = data.get("discount_code")
    if entry["supports_discount"] and discount_code:
        kwargs["discount_code"] = discount_code

    currency = data.get("currency")
    if entry["supports_currency"] and currency:
        kwargs[entry["currency_param"]] = currency

    try:
        module = load_version_module(entry)
        result = module.main(**kwargs)
    except KeyError:
        return jsonify({"error": "This version doesn't recognize that currency."}), 400
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        return jsonify({"error": f"Unexpected error: {error}"}), 400

    return jsonify({"result": result})


@app.route("/api/test/<version>", methods=["POST"])
def api_test(version):
    # Runs the shared tests at the repo root (behavior all four versions agree on)
    # plus the selected version's own test file in its folder, if it has one.
    entry = get_version(version)
    if entry is None:
        return jsonify({"error": "Unknown version"}), 404

    repo_root = os.path.join(APP_DIR, "..")
    test_files = [os.path.join(repo_root, "test_kvittoraknaren.py")]
    version_test_file = os.path.join(version_folder_abs(entry), "test_kvittoraknaren.py")
    if os.path.abspath(version_test_file) != os.path.abspath(test_files[0]) and os.path.exists(version_test_file):
        test_files.append(version_test_file)

    outputs = []
    returncode = 0
    for test_file in test_files:
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Test run timed out"}), 500
        label = os.path.relpath(test_file, repo_root)
        outputs.append(f"== {label} ==\n{result.stdout}{result.stderr}")
        returncode = returncode or result.returncode

    return jsonify(
        {
            "version": version,
            "passed": returncode == 0,
            "returncode": returncode,
            "output": "\n".join(outputs),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)


"""
Job Done zug zug
"""
