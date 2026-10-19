# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project overview

Kvittoräknaren ("the receipt counter") is a small Swedish-language Python exercise: it parses a shopping list string and sums item prices with VAT (moms) applied.

## Commands

- Run the program: `python Kvittoräknaren.py` (prompts interactively for a shopping list).
- Run the shared tests (behavior all four versions agree on): `python test_kvittoraknaren.py`.
- Run one version's own tests: `python med-claude/test_kvittoraknaren.py` (likewise `med-copilot/`, `med-opencode/`).
- Run a single test: `python -m unittest test_kvittoraknaren.TestAllVersionsCommonBehavior.test_two_items_100kr_25_percent_moms` (for a folder's file, run it from inside that folder, e.g. `cd med-claude; python -m unittest test_kvittoraknaren.TestVatBreakdown`).
- Install the website's dependency: `pip install -r requirements.txt` (first time only).
- Run the comparison website: `python webapp/app.py` (serves at `http://127.0.0.1:5000`), or double-click `start_webapp.bat` to start the server in its own window and open the page automatically.
- Run the website's own tests: `python webapp/test_app.py` or `python -m unittest webapp/test_app.py`.

Every test file ends with `unittest.main(testRunner=ReportRunner())`, using `kvitto_testrunner.py` at the repo root: it prints each test as `[PASS]`/`[FAIL]`/`[SKIP]`, then a list of failed tests with tracebacks, then a `Ran N tests: X passed, Y failed` summary (exit code 1 on failure). Test files outside the root add the repo root to `sys.path` to import it. New test files should do the same. (`python -m unittest ...` still works but uses the standard unittest output.)

There is no build step or linter configured. `requirements.txt` lists the repo's only dependency (Flask), used solely by `webapp/`.

## Architecture

- `Kvittoräknaren.py` contains the entire program: a single `main(shoppingList, moms)` function plus a `__main__` block that reads input and prints the total.
  - Input format: a comma-separated string of `"item price"` pairs (e.g. `"milk 10, bread 20"`). Each entry is split on whitespace and the last token is parsed as the price; malformed entries are skipped with a printed warning rather than raising.
  - `moms` is passed as a multiplier (e.g. `1.25` for 25% VAT), not a percentage, and is applied per-item inside the summing loop.
- `med-claude/`, `med-copilot/`, and `med-opencode/` each hold an independent, divergent copy of `Kvittoräknaren.py` — the version produced by that AI tool — plus that version's own `test_kvittoraknaren.py`. They used to live on separate branches and were consolidated into folders on `master`. The root-level `Kvittoräknaren.py` is the original baseline version and is not meant to be kept in sync with the folders.
- Tests are split per version. All test files load `Kvittoräknaren.py` via `importlib.util` from its file path rather than a normal `import` statement, because the filename contains a non-ASCII character (ä); any new test logic should follow the same dynamic-import pattern.
  - `test_kvittoraknaren.py` at the repo root holds only `TestAllVersionsCommonBehavior`: behavior all four versions (root + the three folders) share, looped over every version with `subTest` (e.g. the basic VAT calculation, discount code RABATT10). The baseline root version has no tests beyond these.
  - `med-claude/test_kvittoraknaren.py`: discount/currency quirks (exact-match discount code, per-item currencies, unvalidated `target_currency` raising `KeyError`), `TestFormatReceipt` (`format_receipt()`, a 31-character-wide receipt string with per-VAT-rate lines), `TestVatBreakdown` (`vat_breakdown()`, `{VAT rate: VAT amount}` as `Decimal`s, highest rate first, used by `format_receipt()`), and `TestCliReceipt` (the CLI prints that receipt with 25 % moms on every item).
  - `med-copilot/test_kvittoraknaren.py`: trimmed/case-insensitive discount code, the bug where currency is validated but never converted, and `TestCliBehavior` for its currency retry loop.
  - `med-opencode/test_kvittoraknaren.py`: trimmed/case-insensitive discount code and real currency conversion of the total.
  - When a version's script logic changes, update that version's own test file. Only add to the root file for behavior every version shares.
- `webapp/` is a small Flask website that lets you run and compare all four versions above through a browser: pick a version from a dropdown (labeled by which AI built it, with a one-line blurb on its quirks/bugs), fill in a form whose fields adapt to what that version's `main()` actually supports (discount code, `currency` vs `target_currency`), see the computed total or a friendly error message, and run tests from a button to see pass/fail output (it runs the shared root `test_kvittoraknaren.py` plus the selected version's own `test_kvittoraknaren.py`, not the other versions' tests). It dynamically imports each version's script using the same `importlib.util` pattern described above, and never edits any of the four version folders. It's an agreed cross-cutting exception to the per-folder ownership rule below, since it spans all four versions by design.

## Workflow rules

- After any changes to the project, commit, but do not push.
- For new small changes, ask before you add anything to the project.
- Write or update the test py script when new logic is added.
- Run the test before you are done.
- Include a docstring at the end with "Job Done zug zug"
- Everything is committed on `master`. When an AI tool makes changes, it works inside its own folder (e.g. Claude Code edits files under `med-claude/`, not `med-copilot/` or the root scripts) unless the user says otherwise.
