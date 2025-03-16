"""Run tests with colored and indented output."""

import functools
import sys
import unittest
from pathlib import Path


def skip_external_api(func):
    """Skip external API tests based on environment configuration.

    This is a decorator.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        should_run = "--run-external-api-tests" in sys.argv
        if not should_run:
            skip_reason = f"Skipping external API test: {func.__name__}\n"
            self.skipTest(skip_reason)
        return func(self, *args, **kwargs)

    return wrapper


class ColorTextTestResult(unittest.TextTestResult):
    """Custom test result with colored and indented output."""

    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    INDENT = "  "

    def startTest(self, test):  # noqa: N802
        """Display the test class name and method name before running the test."""
        self.stream.write(f"\n{self.BLUE}{test.__class__.__name__}:{self.RESET}\n")
        self.stream.write(f"{self.INDENT}{test._testMethodName} ... ")
        super().startTest(test)

    def addSuccess(self, test):  # noqa: N802
        """Display a green checkmark for successful tests."""
        self.stream.write(f"{self.GREEN}✓{self.RESET}\n")
        super().addSuccess(test)

    def addError(self, test, err):  # noqa: N802
        """Display a red error mark for tests with errors."""
        self.stream.write(f"{self.RED}✗ ERROR{self.RESET}\n")
        super().addError(test, err)

    def addFailure(self, test, err):  # noqa: N802
        """Display a red failure mark for failed tests."""
        self.stream.write(f"{self.RED}✗ FAIL{self.RESET}\n")
        super().addFailure(test, err)

    def addSkip(self, test, reason):  # noqa: N802
        """Display a yellow skip mark for skipped tests."""
        self.stream.write(f"{self.YELLOW}⚪ SKIP{self.RESET}\n")
        super().addSkip(test, reason)

    def printErrorList(self, flavour, errors):  # noqa: N802
        """Format and print a list of errors with proper indentation and colors."""
        for test, err in errors:
            self.stream.writeln(
                self.BOLD + self.RED + f"=== {flavour}: {test} ===" + self.RESET
            )
            # Indent error messages
            err_lines = str(err).split("\n")
            indented_err = "\n".join(f"{self.INDENT}{line}" for line in err_lines)
            self.stream.writeln(indented_err)


class ColorTextTestRunner(unittest.TextTestRunner):
    """Custom test runner using the colored result class.

    ColorTextTestRunner extends the standard TextTestRunner from unittest
    but enhances test output with colors and improved formatting.
    It displays tests in a hierarchical format with colorized results:
    - Green checkmarks (✓) for passed tests
    - Red X marks (✗) for failed tests
    - Indented and colorized error messages
    - Blue test class names
    - Bold and colored summary statistics

    This makes test output much more readable and allows quick visual
    identification of test status.
    """

    resultclass = ColorTextTestResult  # type: ignore


def main():
    """Discover and run tests with colored output, then display a summary."""
    # Add project root to path
    root_dir = Path(__file__).parent.parent
    sys.path.append(str(root_dir / "py"))

    # Discover and run tests
    suite = unittest.TestLoader().discover(str(root_dir / "tests"), pattern="test_*.py")

    # Original code with ColorText formatting
    result = ColorTextTestRunner(verbosity=2, stream=sys.stdout, descriptions=True).run(
        suite
    )

    # Print summary
    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failed - errors - skipped

    print("\n" + "=" * 70)
    print(f"{ColorTextTestResult.BOLD}Test Summary:{ColorTextTestResult.RESET}")
    print(f"{ColorTextTestResult.GREEN}Passed: {passed}{ColorTextTestResult.RESET}")
    if failed:
        print(f"{ColorTextTestResult.RED}Failed: {failed}{ColorTextTestResult.RESET}")
    if errors:
        print(f"{ColorTextTestResult.RED}Errors: {errors}{ColorTextTestResult.RESET}")
    if skipped:
        print(
            f"{ColorTextTestResult.YELLOW}Skipped: {skipped}{ColorTextTestResult.RESET}"
        )
    print(f"Total tests run: {total}")
    print("=" * 70)

    return not result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(main())
