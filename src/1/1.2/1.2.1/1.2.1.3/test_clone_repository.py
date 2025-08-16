import unittest
import os
import tempfile
import shutil
import git
from unittest.mock import patch, MagicMock
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

# The implementation to test
def clone_repository(repository_url: str, local_path: Optional[str] = None, branch: Optional[str] = None, depth: Optional[int] = None, auth: Optional[Tuple[str, str]] = None) -> str:
    """
    Clones a remote git repository to a local path using GitPython.

    Args:
        repository_url: The URL of the git repository to clone (e.g., https, ssh).
        local_path: The local directory to clone into. If None, a new temporary
                    directory will be created.
        branch: The specific branch to clone. If None, the default branch is cloned.
        depth: If specified, creates a shallow clone with a history truncated
               to the specified number of commits.
        auth: A tuple of (username, password/token) for authentication over HTTPS.

    Returns:
        The absolute path to the root of the cloned repository.

    Raises:
        RuntimeError: If the cloning process fails for any reason (e.g.,
                      authentication failure, repository not found, path exists).
    """
    url_to_clone = repository_url
    if auth and urlparse(repository_url).scheme in ('http', 'https'):
        username, password = auth
        parsed_url = urlparse(repository_url)
        netloc = f"{username}:{password}@{parsed_url.hostname}"
        if parsed_url.port:
            netloc += f":{parsed_url.port}"
        
        url_parts = list(parsed_url)
        url_parts[1] = netloc
        url_to_clone = urlunparse(url_parts)

    target_path = local_path if local_path is not None else tempfile.mkdtemp()

    clone_kwargs = {}
    if branch:
        clone_kwargs['branch'] = branch
    if depth is not None:
        clone_kwargs['depth'] = depth

    try:
        repo = git.Repo.clone_from(
            url=url_to_clone,
            to_path=target_path,
            **clone_kwargs
        )
        return os.path.abspath(repo.working_dir)
    except git.exc.GitCommandError as e:
        # Clean up the potentially created but empty directory on failure
        if local_path is None and os.path.exists(target_path):
             shutil.rmtree(target_path)
        raise RuntimeError(f"Failed to clone repository from '{repository_url}'. Error: {e}") from e
    except Exception as e:
        if local_path is None and os.path.exists(target_path):
             shutil.rmtree(target_path)
        raise RuntimeError(f"An unexpected error occurred while cloning '{repository_url}': {e}") from e

# Unit tests for the clone_repository function
class TestCloneRepository(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for cloning into."""
        self.temp_dir = tempfile.mkdtemp()
        self.dirs_to_cleanup = [self.temp_dir]
        # A known small public repository for testing
        self.public_repo_url = "https://github.com/gitpython-developers/GitPython.git"

    def tearDown(self):
        """Clean up all created temporary directories."""
        for path in self.dirs_to_cleanup:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)

    def test_clone_public_repo_success(self):
        """Test cloning a public repository successfully into a new temp directory."""
        cloned_path = clone_repository(self.public_repo_url)
        self.dirs_to_cleanup.append(cloned_path) # Ensure cleanup

        self.assertTrue(os.path.isdir(cloned_path))
        self.assertTrue(os.path.isdir(os.path.join(cloned_path, '.git')), "'.git' directory not found in cloned path.")

    def test_clone_public_repo_to_specific_path(self):
        """Test cloning a public repository into a specified local path."""
        cloned_path = clone_repository(self.public_repo_url, local_path=self.temp_dir)
        
        self.assertEqual(os.path.abspath(self.temp_dir), cloned_path)
        self.assertTrue(os.path.isdir(os.path.join(cloned_path, '.git')))

    def test_clone_public_repo_with_branch_and_depth(self):
        """Test cloning a public repository with specific branch and depth."""
        # Use a branch that is likely to exist and a shallow clone
        branch_name = 'main'
        depth = 1
        cloned_path = clone_repository(
            self.public_repo_url,
            local_path=self.temp_dir,
            branch=branch_name,
            depth=depth
        )
        
        self.assertTrue(os.path.isdir(os.path.join(cloned_path, '.git')))
        
        # Verify the branch and depth
        repo = git.Repo(cloned_path)
        self.assertEqual(str(repo.active_branch), branch_name)
        
        # A shallow clone of depth 1 will have exactly one commit in its log
        commit_count = len(list(repo.iter_commits()))
        self.assertEqual(commit_count, 1)

    @patch('git.Repo.clone_from')
    def test_clone_private_repo_with_auth(self, mock_clone_from):
        """Test that authentication credentials are correctly embedded in the URL for a private repo."""
        private_repo_url = "https://github.com/myuser/private-repo.git"
        username = "testuser"
        token = "testtoken123"
        
        # Mock the return value of clone_from to simulate a successful clone
        mock_repo = MagicMock()
        mock_repo.working_dir = self.temp_dir
        mock_clone_from.return_value = mock_repo
        
        clone_repository(
            private_repo_url,
            local_path=self.temp_dir,
            auth=(username, token)
        )
        
        mock_clone_from.assert_called_once()
        
        # Check the arguments passed to the mocked function
        call_args, call_kwargs = mock_clone_from.call_args
        expected_url = f"https://{username}:{token}@github.com/myuser/private-repo.git"
        
        self.assertEqual(call_kwargs.get('url'), expected_url)
        self.assertEqual(call_kwargs.get('to_path'), self.temp_dir)

    def test_clone_non_existent_repo_fails(self):
        """Test that cloning a non-existent repository raises a RuntimeError."""
        invalid_url = "https://github.com/nonexistentuser/nonexistentrepo.git"
        
        with self.assertRaises(RuntimeError) as context:
            clone_repository(invalid_url, local_path=self.temp_dir)
        
        self.assertIn("Failed to clone repository", str(context.exception))

    @patch('git.Repo.clone_from')
    def test_clone_private_repo_auth_failure(self, mock_clone_from):
        """Test that an authentication failure during clone raises a RuntimeError."""
        private_repo_url = "https://github.com/myuser/private-repo.git"
        
        # Configure the mock to simulate a Git command error (e.g., auth failure)
        mock_clone_from.side_effect = git.exc.GitCommandError(
            'clone', 'fatal: Authentication failed'
        )
        
        with self.assertRaises(RuntimeError) as context:
            clone_repository(
                private_repo_url,
                local_path=self.temp_dir,
                auth=("baduser", "badtoken")
            )
        
        self.assertIn("Failed to clone repository", str(context.exception))
        self.assertIn("Authentication failed", str(context.exception))
        
        # The function should not have created the directory if it failed
        self.assertFalse(os.listdir(self.temp_dir))

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)