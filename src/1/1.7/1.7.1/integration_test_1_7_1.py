import unittest
from unittest.mock import patch, MagicMock
import os
import io
import contextlib
import tempfile
import shutil
import git

# This test assumes the provided implementations are available in the following modules.
# To run this test, create these files and paste the corresponding code into them.
# File: implementation_1_7_1_2.py
# File: implementation_1_7_1_3.py
from implementation_1_7_1_2 import analyze
from implementation_1_7_1_3 import ask

# A small, public, and relatively stable Git repository for testing
TEST_REPO_URL = "https://github.com/navdeep-G/sample-python-app.git"

class TestCliIntegration(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory that we control for the repository clone
        self.test_dir = tempfile.mkdtemp()
        # Store original OPENAI_API_KEY and set a dummy one for tests
        self.original_api_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key-is-set"

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        # Restore original OPENAI_API_KEY state
        if self.original_api_key is None:
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = self.original_api_key

    @patch('implementation_1_7_1_3.openai.OpenAI')
    @patch('implementation_1_7_1_2.tempfile.TemporaryDirectory')
    def test_full_workflow_analyze_and_ask(self, mock_tempdir, mock_openai_class):
        """
        Tests the primary user workflow: analyzing a repository and then asking a question about it.
        This test verifies the integration between the `analyze` and `ask` functions.
        """
        # --- Arrange ---
        # 1. Mock tempfile.TemporaryDirectory to use our controlled directory.
        # This allows 'analyze' to clone the repo into a path that we can then pass to 'ask'.
        mock_tempdir.return_value.__enter__.return_value = self.test_dir

        # 2. Mock the OpenAI client to avoid making real API calls.
        mock_ai_answer = "The `app.py` file defines a basic Flask web server."
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = mock_ai_answer
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # --- Act & Assert: analyze ---
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            analyze(TEST_REPO_URL)
        analyze_output = stdout_capture.getvalue()

        # Assert that 'analyze' ran correctly and printed expected information
        self.assertIn(f"Analyzing repository: {TEST_REPO_URL}", analyze_output)
        self.assertIn("Cloning complete.", analyze_output)
        self.assertIn("--- Repository Analysis ---", analyze_output)
        self.assertIn("Total commits", analyze_output)
        self.assertIn("Contributors", analyze_output)
        self.assertIn("File Types", analyze_output)
        self.assertIn(".py:", analyze_output)

        # Assert that the repo was actually cloned into our controlled directory
        self.assertTrue(os.path.isdir(os.path.join(self.test_dir, '.git')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'app.py')))

        # --- Act & Assert: ask ---
        question = "What is the purpose of app.py?"
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            ask(question, self.test_dir)
        ask_output = stdout_capture.getvalue()

        # Assert that 'ask' ran its course and printed expected information
        self.assertIn(f"Asking: '{question}'", ask_output)
        self.assertIn("Searching for relevant files...", ask_output)
        self.assertIn("Querying AI assistant...", ask_output)
        self.assertIn("--- AI Answer ---", ask_output)
        self.assertIn(mock_ai_answer, ask_output)

        # Assert that the OpenAI API was called once
        mock_openai_class.assert_called_once()
        mock_client.chat.completions.create.assert_called_once()

        # Inspect the prompt sent to the LLM to ensure it's well-formed
        call_args, call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.get("messages", [])
        user_message = next((m['content'] for m in messages if m['role'] == 'user'), None)

        self.assertIsNotNone(user_message)
        self.assertIn(question, user_message)
        self.assertIn("CONTEXT:", user_message)
        # Check if context from a key file ('app.py') is included in the prompt
        self.assertIn("Content of file: app.py", user_message)
        self.assertIn("from flask import Flask", user_message)

    def test_ask_without_api_key(self):
        """
        Tests that the 'ask' command fails gracefully with a helpful message
        when the OPENAI_API_KEY environment variable is not set.
        """
        # --- Arrange ---
        # Unset the API key for this specific test
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        # --- Act & Assert ---
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            ask("A question that won't be asked", self.test_dir)
        output = stdout_capture.getvalue()
        self.assertIn("Error: OPENAI_API_KEY environment variable not set.", output)

    def test_ask_with_invalid_repo_path(self):
        """
        Tests that the 'ask' command fails gracefully if the provided repository
        path does not exist.
        """
        # --- Arrange ---
        invalid_path = os.path.join(self.test_dir, "non_existent_repo")

        # --- Act & Assert ---
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            ask("A question", invalid_path)
        output = stdout_capture.getvalue()
        self.assertIn(f"Error: Repository path not found at '{invalid_path}'", output)
        self.assertIn("Please use the 'analyze' command on a repository first.", output)

    @patch('implementation_1_7_1_2.git.Repo.clone_from')
    def test_analyze_handles_git_clone_error(self, mock_clone_from):
        """
        Tests that the 'analyze' command handles Git errors during cloning
        and provides a user-friendly error message.
        """
        # --- Arrange ---
        error_message = "Authentication failed for private repository"
        mock_clone_from.side_effect = git.exc.GitCommandError(
            "clone", 128, stderr=error_message
        )
        bad_repo_url = "https://github.com/user/private-repo.git"

        # --- Act & Assert ---
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            analyze(bad_repo_url)
        output = stdout_capture.getvalue()
        self.assertIn(f"Error: Failed to clone repository from '{bad_repo_url}'.", output)
        self.assertIn("Details:", output)
        self.assertIn(error_message, output)

if __name__ == '__main__':
    unittest.main()