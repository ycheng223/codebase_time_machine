import git
import os
import tempfile
from collections import Counter

def analyze(repo_url):
    """
    Clones a Git repository and performs a simple analysis on it.

    The analysis includes:
    - Total number of commits.
    - List of unique contributors (authors).
    - A breakdown of file types by extension.

    Args:
        repo_url (str): The URL of the Git repository to analyze.
    """
    print(f"Analyzing repository: {repo_url}")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            print(f"Cloning into temporary directory...")
            repo = git.Repo.clone_from(repo_url, temp_dir, depth=100) # Shallow clone for speed
            print("Cloning complete.")
        except git.exc.GitCommandError as e:
            print(f"Error: Failed to clone repository from '{repo_url}'.")
            print(f"Details: {e}")
            return

        # 1. Analyze commit count
        # Note: A shallow clone may not represent the full commit history.
        # To get the full count, remove `depth=100` from clone_from.
        all_commits = list(repo.iter_commits('HEAD'))
        commit_count = len(all_commits)

        # 2. Analyze contributors
        authors = sorted(list({commit.author.name for commit in all_commits}))

        # 3. Analyze file types
        # Use git ls-tree to list all files in the latest commit
        tree = repo.head.commit.tree
        file_paths = [blob.path for blob in tree.traverse() if blob.type == 'blob']
        
        file_extensions = Counter(
            os.path.splitext(f)[1] for f in file_paths if os.path.splitext(f)[1]
        )

        # --- Print Results ---
        print("\n--- Repository Analysis ---")
        print(f"URL: {repo_url}")
        print(f"Total commits (in history analyzed): {commit_count}")
        
        print(f"\nContributors ({len(authors)}):")
        if authors:
            print(", ".join(authors))
        else:
            print("No contributors found.")
            
        print("\nFile Types (Top 10):")
        if not file_extensions:
            print("No files with extensions found.")
        else:
            for ext, count in file_extensions.most_common(10):
                print(f"- {ext if ext else '[No Extension]'}: {count} file(s)")
        print("-------------------------\n")