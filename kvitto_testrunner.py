"""Test runner that prints every test with PASS/FAIL, then the failed tests, then a summary.

Usage at the bottom of a test file:

    if __name__ == "__main__":
        unittest.main(testRunner=ReportRunner())

Since it goes through unittest.main, running a single class or test still works,
e.g. `python test_kvittoraknaren.py TestAllVersionsCommonBehavior`.
"""

import sys
import unittest


def _short_name(test):
    # "__main__.TestVatBreakdown.test_x" -> "TestVatBreakdown.test_x"
    return ".".join(test.id().split(".")[-2:])


class ReportResult(unittest.TestResult):

    def __init__(self, stream):
        super().__init__()
        self.stream = stream
        self.outcomes = []  # (name, status, [problem texts])
        self._problems = []
        self._skip_reason = None

    def startTest(self, test):
        super().startTest(test)
        self._problems = []
        self._skip_reason = None

    def _problem(self, label, test, err):
        kind = "FAIL" if issubclass(err[0], test.failureException) else "ERROR"
        return f"{kind} {label}\n{self._exc_info_to_string(err, test)}"

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._problems.append(self._problem(_short_name(test), test, err))

    def addError(self, test, err):
        super().addError(test, err)
        problem = self._problem(_short_name(test), test, err)
        if isinstance(test, unittest.TestCase):
            self._problems.append(problem)
        else:
            # setUpClass/module errors are not tied to a running test
            self._report(str(test), "FAIL", [problem])

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            label = f"{_short_name(test)} {subtest._subDescription()}"
            self._problems.append(self._problem(label, test, err))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._skip_reason = reason

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._problems.append(f"FAIL {_short_name(test)}\nExpected to fail, but passed.\n")

    def stopTest(self, test):
        super().stopTest(test)
        if self._problems:
            status = "FAIL"
        elif self._skip_reason is not None:
            status = "SKIP"
        else:
            status = "PASS"
        self._report(_short_name(test), status, self._problems)

    def _report(self, name, status, problems):
        self.outcomes.append((name, status, list(problems)))
        self.stream.write(f"[{status}] {name}\n")
        self.stream.flush()

    def print_summary(self):
        failed = [o for o in self.outcomes if o[1] == "FAIL"]
        passed = sum(1 for o in self.outcomes if o[1] == "PASS")
        skipped = sum(1 for o in self.outcomes if o[1] == "SKIP")
        line = "=" * 70

        self.stream.write(f"\n{line}\n")
        if failed:
            self.stream.write(f"Failed tests ({len(failed)}):\n")
            for name, _status, _problems in failed:
                self.stream.write(f"  - {name}\n")
            self.stream.write(f"{line}\nDetails:\n")
            for _name, _status, problems in failed:
                for problem in problems:
                    self.stream.write(f"\n{problem}")
        else:
            self.stream.write("Failed tests: none\n")

        summary = f"Ran {len(self.outcomes)} tests: {passed} passed, {len(failed)} failed"
        if skipped:
            summary += f", {skipped} skipped"
        self.stream.write(f"{line}\n{summary}\n{'ALL TESTS PASSED' if not failed else 'SOME TESTS FAILED'}\n")
        self.stream.flush()


class ReportRunner:

    def __init__(self, stream=None):
        self.stream = stream

    def run(self, test):
        result = ReportResult(self.stream or sys.stdout)
        test(result)
        result.print_summary()
        return result


"""
Job Done zug zug
"""
