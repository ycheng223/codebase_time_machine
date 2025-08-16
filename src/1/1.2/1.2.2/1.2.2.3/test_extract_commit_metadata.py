import unittest
import tempfile
import shutil
import os
import git
from datetime import datetime

# Assume the function is in a file named 'commit_extractor.py'
# To run this test, place the implementation in a file named 'commit_extractor.py'
# in the same directory as this test file.
from commit_extractor import extract_commit_metadata

class TestExtractCommitMetadata(unittest.TestCase):

    def setUp(self):
        """Set up a temporary git repository for each test."""
        self.repo_path = tempfile.mkdtemp()
        self.repo = git.Repo.init(self.repo_path)
        # Set a default author for consistent test results
        with self.repo.config_writer() as config:
            config.set_value("user", "name", "Test Author")
            config.set_value("user", "email", "test@example.com")

    def tearDown(self):
        """Remove the temporary repository after each test."""
        shutil.rmtree(self.repo_path)

    def _create_and_commit(self, filename, content, message):
        """Helper function to create a file and commit it."""
        file_path = os.path.join(self.repo_path, filename)
        with open(file_path, "w") as f:
            f.write(content)
        self.repo.index.add([file_path])
        self.repo.index.commit(message)
        return self.repo.head.commit

    def test_initial_commit(self):
        """Test parsing of the very first commit in a repository."""
        commit_message = "Initial commit"
        self._create_and_commit("file1.txt", "hello world", commit_message)

        commits_data = extract_commit_metadata(self.repo_path)

        self.assertEqual(len(commits_data), 1)
        initial_commit = commits_data[0]

        self.assertEqual(initial_commit['author'], 'Test Author')
        self.assertEqual(initial_commit['message'], commit_message)
        self.assertEqual(len(initial_commit['diffs']), 1)

        diff = initial_commit['diffs'][0]
        self.assertEqual(diff['file_path'], 'file1.txt')
        self.assertEqual(diff['change_type'], 'A')  # 'A' for Added
        self.assertIn('--- /dev/null', diff['diff_text'])
        self.assertIn('+++ b/file1.txt', diff['diff_text'])
        self.assertIn('+hello world', diff['diff_text'])

    def test_standard_commit(self):
        """Test parsing of a standard commit that modifies a file."""
        # Initial commit
        self._create_and_commit("file1.txt", "line 1\n", "Initial commit")

        # Standard commit (modification)
        commit_message = "Update file1"
        self._create_and_commit("file1.txt", "line 1\nline 2\n", commit_message)

        commits_data = extract_commit_metadata(self.repo_path)

        # The function returns commits in reverse chronological order
        self.assertEqual(len(commits_data), 2)
        standard_commit = commits_data[0]

        self.assertEqual(standard_commit['author'], 'Test Author')
        self.assertEqual(standard_commit['message'], commit_message)
        self.assertEqual(len(standard_commit['diffs']), 1)

        diff = standard_commit['diffs'][0]
        self.assertEqual(diff['file_path'], 'file1.txt')
        self.assertEqual(diff['change_type'], 'M')  # 'M' for Modified
        self.assertIn('--- a/file1.txt', diff['diff_text'])
        self.assertIn('+++ b/file1.txt', diff['diff_text'])
        self.assertIn('+line 2', diff['diff_text'])

    def test_merge_commit(self):
        """Test parsing of a merge commit."""
        # 1. Initial commit on master
        self._create_and_commit("main.txt", "Initial content", "Initial commit")
        master_branch = self.repo.head.reference

        # 2. Create and checkout a new branch
        feature_branch = self.repo.create_head("feature")
        feature_branch.checkout()

        # 3. Commit on the feature branch
        self._create_and_commit("feature.txt", "Feature content", "Add feature file")

        # 4. Checkout master and make a commit to force a non-fast-forward merge
        master_branch.checkout()
        self._create_and_commit("master_only.txt", "Master change", "Add file on master")

        # 5. Merge the feature branch into master
        merge_message = "Merge branch 'feature'"
        self.repo.git.merge(feature_branch.name, "--no-ff", "-m", merge_message)

        commits_data = extract_commit_metadata(self.repo_path)

        # The first commit in the list should be the merge commit
        merge_commit_data = commits_data[0]
        self.assertEqual(merge_commit_data['message'], merge_message)

        # The implementation diffs against the first parent (the master branch).
        # This diff should show the changes brought in from the merged branch.
        self.assertEqual(len(merge_commit_data['diffs']), 1)
        diff = merge_commit_data['diffs'][0]

        # The change is the addition of 'feature.txt' from the other branch
        self.assertEqual(diff['file_path'], 'feature.txt')
        self.assertEqual(diff['change_type'], 'A') # Added file from the feature branch
        self.assertIn('+Feature content', diff['diff_text'])

    def test_invalid_repo_path(self):
        """Test function with a path that does not exist."""
        invalid_path = os.path.join(self.repo_path, "non_existent_dir")
        result = extract_commit_metadata(invalid_path)
        self.assertEqual(result, [])

    def test_non_git_directory(self):
        """Test function with a valid directory that is not a git repository."""
        non_git_dir = tempfile.mkdtemp()
        try:
            result = extract_commit_metadata(non_git_dir)
            self.assertEqual(result, [])
        finally:
            shutil.rmtree(non_git_dir)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)