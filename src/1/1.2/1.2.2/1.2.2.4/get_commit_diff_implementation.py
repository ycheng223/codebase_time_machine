import git
from typing import List, Dict

def get_commit_diff(commit: git.Commit) -> Dict[str, List[str]]:
    """
    Extracts file diffs (added, modified, deleted) for a given commit.

    This function compares the commit with its first parent to determine the
    changes. For the initial commit (which has no parents), all files are
    considered 'added'. For merge commits, it compares against the first parent.

    Args:
        commit (git.Commit): The commit object to analyze.

    Returns:
        dict: A dictionary with keys 'added', 'modified', and 'deleted',
              each containing a list of file paths affected in the commit.
    """
    # If the commit has no parents, it's the initial commit.
    # The diff is against an empty tree.
    if not commit.parents:
        parent = git.NULL_TREE
    else:
        # For regular and merge commits, diff against the first parent.
        parent = commit.parents[0]

    # Get the diff between the parent and the current commit.
    # create_patch=False is an optimization as we only need the file paths.
    diffs = parent.diff(commit, create_patch=False)

    file_changes = {
        'added': [],
        'modified': [],
        'deleted': []
    }

    for diff in diffs:
        # diff.a_path is the path in the parent, diff.b_path is in the commit.
        if diff.change_type == 'A':  # Added
            file_changes['added'].append(diff.b_path)
        elif diff.change_type == 'D':  # Deleted
            file_changes['deleted'].append(diff.a_path)
        elif diff.change_type == 'M':  # Modified
            file_changes['modified'].append(diff.a_path)
        elif diff.change_type == 'R':  # Renamed
            # A rename is often treated as a delete of the old path and an add of the new.
            file_changes['deleted'].append(diff.a_path)
            file_changes['added'].append(diff.b_path)
        elif diff.change_type == 'T': # Type change (e.g., file to symlink)
            file_changes['modified'].append(diff.a_path)
            
    return file_changes