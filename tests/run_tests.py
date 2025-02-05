import unittest
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir / 'py'))

# Discover and run tests
loader = unittest.TestLoader()
start_dir = str(root_dir / 'tests')
suite = loader.discover(start_dir, pattern='test_*.py')

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Return proper exit code
sys.exit(not result.wasSuccessful())
