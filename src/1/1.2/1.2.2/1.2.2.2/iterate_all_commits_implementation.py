import git

def iterate_all_commits(repo_path):
    """
    Creates a generator that iterates through all commits in a Git repository.

    This function opens a Git repository at the given path and yields each
    commit object, starting from the current HEAD and traversing back through
    its history.

    Args:
        repo_path (str): The file system path to the Git repository.

    Yields:
        git.Commit: The next commit object in the repository's history.
    
    Raises:
        git.exc.InvalidGitRepositoryError: If the given path is not a valid Git repository.
        git.exc.NoSuchPathError: If the given path does not exist.
    """
    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
        
        # repo.iter_commits() returns a generator for iterating through commits.
        # By default, it starts from the current HEAD. To iterate through all
        # commits from all branches, you could use repo.iter_commits('--all').
        commit_iterator = repo.iter_commits()
        
        for commit in commit_iterator:
            yield commit
            
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError) as e:
        print(f"Error accessing repository at '{repo_path}': {e}")
        # Re-raise the exception to allow the caller to handle it
        raise