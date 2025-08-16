import unittest

def run_automated_tests(start_dir='.', pattern='test_*.py'):
    """
    Discovers and runs tests using Python's unittest framework.

    This function provides a basic automated testing workflow by searching a
    directory for test files that match a specific pattern, running the
    tests found, and printing a summary of the results to the console.

    Args:
        start_dir (str): The directory to start test discovery from.
                         Defaults to the current directory.
        pattern (str): The pattern used to identify test files. Defaults
                       to 'test_*.py'.

    Returns:
        bool: True if all discovered tests pass, False otherwise.
    """
    # 1. Create a TestLoader instance to discover tests
    loader = unittest.TestLoader()

    # 2. Discover tests from the specified directory and pattern
    suite = loader.discover(start_dir=start_dir, pattern=pattern)

    # 3. Create a TextTestRunner to execute the tests
    # verbosity=2 provides detailed output for each test
    runner = unittest.TextTestRunner(verbosity=2)

    # 4. Run the test suite
    result = runner.run(suite)

    # 5. Return a boolean indicating if the test run was successful
    # The wasSuccessful() method returns True if all tests passed
    return result.wasSuccessful()