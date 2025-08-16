import unittest
import os
import sys
import shutil
import tempfile
import io

# Assuming the implementation is in a file named 'implementation_1_1_3_2.py'
# If the file has a different name, this import will need to be adjusted.
from implementation_1_1_3_2 import run_automated_tests


class TestCiCdPipelineIntegration(unittest.TestCase):
    """
    Integration tests for the run_automated_tests function.
    This test suite creates a temporary directory structure with mock test
    files to simulate a real-world project environment and verifies that
    the function correctly discovers, runs, and reports the results.
    """

    def setUp(self):
        """
        Set up a temporary directory with various test files before each test.
        """
        # Create a temporary directory to act as the project root
        self.test_dir = tempfile.mkdtemp()

        # Suppress the verbose output from the TextTestRunner
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        # --- Define content for mock test files ---
        self.passing_test_content = """
import unittest
class PassingTest(unittest.TestCase):
    def test_success(self):
        self.assertEqual(1, 1)
"""
        self.failing_test_content = """
import unittest
class FailingTest(unittest.TestCase):
    def test_failure(self):
        self.assertEqual(1, 0, "This test is designed to fail")
"""
        self.error_test_content = """
import unittest
class ErrorTest(unittest.TestCase):
    def test_error(self):
        raise ValueError("This test is designed to cause an error")
"""
        self.another_passing_test_content = """
import unittest
class AnotherPassingTest(unittest.TestCase):
    def test_another_success(self):
        self.assertTrue(True)
"""
        # --- Create the files in the temporary directory ---
        self._create_test_file('test_passing.py', self.passing_test_content)
        self._create_test_file('test_failing.py', self.failing_test_content)
        self._create_test_file('test_error.py', self.error_test_content)
        self._create_test_file('ignore_this_file.py', "print('not a test')")
        self._create_test_file('custom_passing_suite.py', self.another_passing_test_content)

        # Create a subdirectory and a test file within it
        self.subdir_path = os.path.join(self.test_dir, 'module_a')
        os.makedirs(self.subdir_path)
        self._create_test_file(os.path.join(self.subdir_path, 'test_sub_passing.py'), self.passing_test_content)

    def tearDown(self):
        """
        Clean up the temporary directory after each test.
        """
        # Restore stdout and stderr
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        # Remove the temporary directory and all its contents
        shutil.rmtree(self.test_dir)

    def _create_test_file(self, filename, content):
        """Helper function to write content to a file in the temp directory."""
        with open(os.path.join(self.test_dir, filename), 'w') as f:
            f.write(content)

    def test_all_tests_pass(self):
        """
        Verify the function returns True when all discovered tests pass.
        This includes tests in subdirectories.
        """
        # We use a pattern that only discovers the passing tests
        result = run_automated_tests(start_dir=self.test_dir, pattern='test_*passing*.py')
        self.assertTrue(result, "Should return True when all tests pass")

    def test_at_least_one_test_fails(self):
        """
        Verify the function returns False when at least one test fails.
        """
        # This pattern will pick up the passing and the failing test
        result = run_automated_tests(start_dir=self.test_dir, pattern='test_pa*.py,test_fa*.py')
        self.assertFalse(result, "Should return False when a test fails")

    def test_at_least_one_test_errors(self):
        """
        Verify the function returns False when at least one test raises an error.
        """
        # This pattern will pick up the passing and the erroring test
        result = run_automated_tests(start_dir=self.test_dir, pattern='test_pa*.py,test_er*.py')
        self.assertFalse(result, "Should return False when a test causes an error")

    def test_mixed_results_returns_false(self):
        """
        Verify the function returns False when the suite contains a mix of
        passing, failing, and erroring tests.
        """
        # The default pattern will discover all `test_*.py` files
        result = run_automated_tests(start_dir=self.test_dir)
        self.assertFalse(result, "Should return False with mixed passing, failing, and erroring tests")

    def test_no_tests_found(self):
        """
        Verify the function returns True when no tests match the discovery pattern.
        An empty test suite is considered successful.
        """
        result = run_automated_tests(start_dir=self.test_dir, pattern='non_existent_test_*.py')
        self.assertTrue(result, "Should return True when no tests are found")

    def test_custom_pattern(self):
        """
        Verify the function correctly uses a custom file pattern for discovery.
        """
        # This should only discover and run 'custom_passing_suite.py', which passes
        result = run_automated_tests(start_dir=self.test_dir, pattern='custom_*.py')
        self.assertTrue(result, "Should successfully run tests matching the custom pattern")

    def test_empty_directory(self):
        """
        Verify the function returns True when run on an empty directory.
        """
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir)
        result = run_automated_tests(start_dir=empty_dir)
        self.assertTrue(result, "Should return True for an empty directory")