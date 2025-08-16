import shutil
import git
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

def clone_repository(repo_url: str, cache_dir: 'Path', *, ref: 'Optional[str]' = None, depth: 'Optional[int]' = None, force: bool = False) -> 'Path':
    """
    Clones a remote git repository to a local cache directory.
    If the repository already exists and force is False, it fetches updates
    and checks out the specified reference.

    Args:
        repo_url: The URL of the git repository.
        cache_dir: The base directory for the local cache.
        ref: The branch, tag, or commit to checkout. If the repository is updated,
             this ref is checked out. If None, the current branch is updated.
        depth: If specified, creates a shallow clone with a history truncated to this
               number of commits. This argument is ignored if the repository
               is being updated.
        force: If True, deletes the destination directory if it already exists
               before cloning.

    Returns:
        The path to the cloned repository.

    Raises:
        IOError: If there is an error during the git clone or update operation.
    """
    parsed_url = urlparse(repo_url)
    repo_subpath = Path(parsed_url.netloc) / Path(parsed_url.path.strip('/')).with_suffix('')
    destination_path = cache_dir / repo_subpath

    repo = None
    # Check if a valid repository already exists at the destination
    if not force and destination_path.is_dir():
        try:
            repo = git.Repo(destination_path)
            # Also check if the remote URL matches the one we want
            if repo.remotes.origin.url != repo_url:
                # URL mismatch, this is a different repo. Re-clone required.
                repo = None
        except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
            # The path exists but is not a valid git repo. Re-clone required.
            repo = None

    if repo:
        # A valid repository exists, so we update it.
        try:
            origin = repo.remotes.origin
            # Fetch all updates from the remote, including tags, and prune deleted branches
            origin.fetch(prune=True)

            # If a specific ref is provided, check it out
            if ref:
                repo.git.checkout(ref)
            
            # If the current checkout is a branch (not a detached HEAD), pull changes
            # This will update the working copy to the latest fetched version
            if not repo.head.is_detached:
                origin.pull()

        except git.exc.GitCommandError as e:
            raise IOError(f"Failed to update repository '{repo_url}': {e}") from e
    else:
        # The repository does not exist, is invalid, or a force-clone is requested.
        # So, we (re)clone it.
        if destination_path.exists():
            shutil.rmtree(destination_path)

        clone_kwargs = {}
        if ref:
            clone_kwargs['branch'] = ref
        if depth:
            clone_kwargs['depth'] = depth

        try:
            # Ensure the parent directory exists, as GitPython won't create it.
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            git.Repo.clone_from(
                url=repo_url,
                to_path=destination_path,
                **clone_kwargs
            )
        except git.exc.GitCommandError as e:
            raise IOError(f"Failed to clone repository '{repo_url}': {e}") from e

    return destination_path