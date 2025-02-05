import unittest
import sys
from pathlib import Path

import unittest
import sys
from pathlib import Path

class ColorTextTestResult(unittest.TextTestResult):
    """Custom test result with colored and indented output"""

    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    INDENT = "  "

    def startTest(self, test):
        self.stream.write(f'\n{self.BLUE}{test.__class__.__name__}:{self.RESET}\n')
        self.stream.write(f'{self.INDENT}{test._testMethodName} ... ')
        super().startTest(test)

    def addSuccess(self, test):
        self.stream.write(f'{self.GREEN}✓{self.RESET}\n')
        super().addSuccess(test)

    def addError(self, test, err):
        self.stream.write(f'{self.RED}✗ ERROR{self.RESET}\n')
        super().addError(test, err)

    def addFailure(self, test, err):
        self.stream.write(f'{self.RED}✗ FAIL{self.RESET}\n')
        super().addFailure(test, err)

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.BOLD + self.RED + f"=== {flavour}: {test} ===" + self.RESET)
            # Indent error messages
            err_lines = str(err).split('\n')
            indented_err = '\n'.join(f"{self.INDENT}{line}" for line in err_lines)
            self.stream.writeln(indented_err)


class ColorTextTestRunner(unittest.TextTestRunner):
    """Custom test runner using the colored result class"""
    resultclass = ColorTextTestResult

def main():
    # Add project root to path
    root_dir = Path(__file__).parent.parent
    sys.path.append(str(root_dir / 'py'))

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = str(root_dir / 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Use our custom runner
    runner = ColorTextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True
    )

    result = runner.run(suite)

    # Print summary
    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors

    print("\n" + "="*70)
    print(f"{ColorTextTestResult.BOLD}Test Summary:{ColorTextTestResult.RESET}")
    print(f"{ColorTextTestResult.GREEN}Passed: {passed}{ColorTextTestResult.RESET}")
    if failed:
        print(f"{ColorTextTestResult.RED}Failed: {failed}{ColorTextTestResult.RESET}")
    if errors:
        print(f"{ColorTextTestResult.RED}Errors: {errors}{ColorTextTestResult.RESET}")
    print(f"Total tests run: {total}")
    print("="*70)

    # Return proper exit code
    return not result.wasSuccessful()

if __name__ == "__main__":
    sys.exit(main())
