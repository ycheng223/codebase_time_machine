import os
import tempfile
import git
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

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
        raise RuntimeError(f"Failed to clone repository from '{repository_url}'. Error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while cloning '{repository_url}': {e}") from e