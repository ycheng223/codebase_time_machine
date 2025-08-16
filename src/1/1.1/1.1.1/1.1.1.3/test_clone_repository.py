import unittest
import os
import shutil
import tempfile
import git

# Implementation to test:
def clone_repository(repo_url: str, destination_path: str | None = None, branch: str | None = None) -> str:
    """
    Clones a remote Git repository to a specified local path using GitPython.

    Args:
        repo_url: The URL of the Git repository to clone.
        destination_path: The local path where the repository should be cloned.
                          If None, a directory with the repository's name is
                          created in the current working directory.
        branch: The specific branch to clone. If None, the default branch is cloned.

    Returns:
        The absolute path to the cloned repository's working directory.

    Raises:
        git.exc.GitCommandError: If the git clone command fails for any reason
                                 (e.g., authentication error, repository not found,
                                 destination path already exists and is not an
                                 empty directory).
    """
    clone_kwargs = {}
    if branch:
        clone_kwargs['branch'] = branch

    # The `clone_from` method handles the destination_path being None by creating
    # a directory in the current working directory based on the repo name.
    # It returns a Repo object on success.
    repo = git.Repo.clone_from(
        url=repo_url,
        to_path=destination_path,
        **clone_kwargs
    )
    
    # The `working_dir` attribute of the Repo object contains the path to the
    # root of the newly cloned repository.
    cloned_path = repo.working_dir
    
    # Ensure the returned path is absolute for consistency.
    return os.path.abspath(cloned_path)


class TestCloneRepository(unittest.TestCase):
    
    # A public, lightweight repository for testing purposes.
    TEST_REPO_URL = "https://github.com/gitpython-developers/gitpython-test-repo.git"

    def setUp(self):
        """Create a temporary directory before each test."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove the temporary directory after each test."""
        shutil.rmtree(self.test_dir)

    def test_clone_success_specific_path(self):
        """Test successful cloning to a specified destination path."""
        dest_path = os.path.join(self.test_dir, "my_repo")
        cloned_path = clone_repository(self.TEST_REPO_URL, destination_path=dest_path)
        
        self.assertEqual(os.path.abspath(dest_path), cloned_path)
        self.assertTrue(os.path.isdir(cloned_path))
        self.assertTrue(os.path.isdir(os.path.join(cloned_path, ".git")), "A .git directory should exist")

    def test_clone_success_default_path(self):
        """Test successful cloning to a default path (in current working directory)."""
        repo_name = "gitpython-test-repo"  # as derived from the URL
        expected_path = os.path.join(self.test_dir, repo_name)
        
        # Change CWD to the temp directory for this test
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.addCleanup(os.chdir, original_cwd)

        cloned_path = clone_repository(self.TEST_REPO_URL, destination_path=None)

        self.assertEqual(os.path.abspath(expected_path), cloned_path)
        self.assertTrue(os.path.isdir(cloned_path))
        self.assertTrue(os.path.isdir(os.path.join(cloned_path, ".git")))
        
    def test_clone_success_with_specific_branch(self):
        """Test successfully cloning a specific branch."""
        dest_path = os.path.join(self.test_dir, "repo_specific_branch")
        branch_to_clone = "old-master"
        
        cloned_path = clone_repository(self.TEST_REPO_URL, dest_path, branch=branch_to_clone)
        
        self.assertTrue(os.path.isdir(cloned_path))
        
        # Verify the correct branch was checked out
        repo = git.Repo(cloned_path)
        self.assertEqual(repo.active_branch.name, branch_to_clone)

    def test_clone_failure_invalid_url(self):
        """Test that cloning fails with an invalid repository URL."""
        invalid_url = "https://example.com/non/existent/repo.git"
        dest_path = os.path.join(self.test_dir, "invalid_repo")
        
        with self.assertRaises(git.exc.GitCommandError):
            clone_repository(invalid_url, destination_path=dest_path)
        
        self.assertFalse(os.path.exists(dest_path), "Destination path should not be created on failure")

    def test_clone_failure_destination_exists_and_not_empty(self):
        """Test that cloning fails if the destination path exists and is not empty."""
        dest_path = os.path.join(self.test_dir, "existing_dir")
        os.makedirs(dest_path)
        # Create a file to make the directory non-empty
        with open(os.path.join(dest_path, "dummy.txt"), "w") as f:
            f.write("This directory is not empty.")
            
        with self.assertRaises(git.exc.GitCommandError) as cm:
            clone_repository(self.TEST_REPO_URL, destination_path=dest_path)
        
        # Optionally, check the error message
        self.assertIn("already exists and is not an empty directory", str(cm.exception))


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)