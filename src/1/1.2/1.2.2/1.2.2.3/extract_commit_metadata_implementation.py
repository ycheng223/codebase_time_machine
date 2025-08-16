import git

def extract_commit_metadata(commit: git.Commit):
    """
    Extracts specific metadata from a single Git commit object.

    This function takes a GitPython Commit object and returns a dictionary
    containing key pieces of metadata: the commit hash, author information,
    the date of the commit, and the full commit message.

    Args:
        commit (git.Commit): The commit object from which to extract metadata.

    Returns:
        dict: A dictionary with the following keys:
              'hash': The full SHA-1 hash of the commit.
              'author': A string representation of the author (e.g., "Name <email>").
              'date': The authored date in ISO 8601 format.
              'message': The full, stripped commit message.
    """
    metadata = {
        'hash': commit.hexsha,
        'author': f"{commit.author.name} <{commit.author.email}>",
        'date': commit.authored_datetime.isoformat(),
        'message': commit.message.strip()
    }
    return metadata