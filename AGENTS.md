# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project overview

Kvittoräknaren ("the receipt counter") is a small Swedish-language Python exercise: it parses a shopping list string and sums item prices with VAT (moms) applied.

## Commands

- Run the program: `python Kvittoräknaren.py` (prompts interactively for a shopping list).
- Run tests: `python test_kvittoraknaren.py` or `python -m unittest test_kvittoraknaren.py`.
- Run a single test: `python -m unittest test_kvittoraknaren.TestKvittoraknaren.test_two_items_100kr_25_percent_moms`.

There is no build step, package manifest, or linter configured.

## Architecture

- `Kvittoräknaren.py` contains the entire program: a single `main(shoppingList, moms)` function plus a `__main__` block that reads input and prints the total.
  - Input format: a comma-separated string of `"item price"` pairs (e.g. `"milk 10, bread 20"`). Each entry is split on whitespace and the last token is parsed as the price; malformed entries are skipped with a printed warning rather than raising.
  - `moms` is passed as a multiplier (e.g. `1.25` for 25% VAT), not a percentage, and is applied per-item inside the summing loop.
- `test_kvittoraknaren.py` loads `Kvittoräknaren.py` via `importlib.util` from its file path rather than a normal `import` statement, because the filename contains a non-ASCII character (ä). Any new test file should follow the same dynamic-import pattern instead of trying to `import` the module directly.
- `med-claude/`, `med-copilot/`, and `med-opencode/` each hold an independent, divergent copy of `Kvittoräknaren.py` and `test_kvittoraknaren.py` — the versions produced by that AI tool. They used to live on separate branches and were consolidated into folders on `master`. The root-level `Kvittoräknaren.py`/`test_kvittoraknaren.py` are the original baseline version and are not meant to be kept in sync with the folders.

## Workflow rules

- After any changes to the project, commit, but do not push.
- For new small changes, ask before you add anything to the project.
- Write or update the test py script when new logic is added.
- Run the test before you are done.
- Include a docstring at the end with "Job Done zug zug"
- Everything is committed on `master`. When an AI tool makes changes, it works inside its own folder (e.g. Claude Code edits files under `med-claude/`, not `med-copilot/` or the root scripts) unless the user says otherwise.
