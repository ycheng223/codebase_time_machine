import unittest
import git
import tempfile
import os
import shutil

# The implementation to test:
# This is included here for context, as per the problem description.
# In a real project, this would be in a separate file and imported.
def parse_commit_diff(commit):
    """
    Parses the diffs for a given commit against its first parent.

    For the initial commit (which has no parents), it shows the diff against an
    empty tree, effectively showing all files as newly added. For merge commits,
    it compares against the first parent.

    Args:
        commit (git.Commit): The commit object to analyze.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents
                    a single file change. Each dictionary contains keys:
                    - 'change_type': e.g., 'A' (Added), 'D' (Deleted),
                                     'M' (Modified), 'R' (Renamed).
                    - 'old_path': The path of the file before the change (or None).
                    - 'new_path': The path of the file after the change (or None).
                    - 'diff_text': The raw text of the diff.
    """
    if commit.parents:
        # Diff against the first parent
        parent = commit.parents[0]
    else:
        # For the initial commit, diff against an empty tree
        parent = git.NULL_TREE

    # The create_patch=True option is crucial to get the textual diff
    diff_index = parent.diff(commit, create_patch=True)

    parsed_diffs = []
    for diff_item in diff_index:
        diff_text = ''
        if diff_item.diff:
            # The diff content is in bytes, so we decode it
            diff_text = diff_item.diff.decode('utf-8', errors='ignore')

        change = {
            'change_type': diff_item.change_type,
            'old_path': diff_item.a_path,
            'new_path': diff_item.b_path,
            'diff_text': diff_text,
        }
        parsed_diffs.append(change)

    return parsed_diffs


class TestParseCommitDiff(unittest.TestCase):
    """
    Unit tests for the parse_commit_diff function.
    """

    def setUp(self):
        """Set up a temporary git repository with a complex history."""
        self.repo_dir = tempfile.mkdtemp()
        self.repo = git.Repo.init(self.repo_dir)
        self.file_path = lambda name: os.path.join(self.repo_dir, name)

        # Configure a dummy user for commits
        with self.repo.config_writer() as cw:
            cw.set_value("user", "name", "Test User")
            cw.set_value("user", "email", "test@example.com")
            cw.release()

        # Helper to create a file and commit it
        def create_commit(filename, content, message, parent_commits=None):
            file_path = self.file_path(filename)
            with open(file_path, "w") as f:
                f.write(content)
            self.repo.index.add([file_path])
            return self.repo.index.commit(message, parent_commits=parent_commits)

        # C1: Initial commit
        self.c1 = create_commit("file1.txt", "Initial content", "Initial commit")

        # Create a feature branch from C1
        feature_branch = self.repo.create_head("feature", self.c1)

        # C2: A second commit on the main branch (modifies file1.txt)
        with open(self.file_path("file1.txt"), "a") as f:
            f.write("\nMore on main.")
        self.repo.index.add(["file1.txt"])
        self.c2 = self.repo.index.commit("Second commit on main")

        # C3: A commit on the feature branch (adds file2.txt)
        self.repo.head.reference = feature_branch
        self.repo.head.reset(index=True, working_tree=True)
        self.c3 = create_commit("file2.txt", "Content for feature", "First commit on feature")

        # Switch back to main and merge the feature branch
        self.repo.head.reference = self.repo.heads.main
        self.repo.head.reset(index=True, working_tree=True)
        self.repo.index.merge_tree(feature_branch, base=self.c1)

        # C4: The merge commit
        self.c4_merge = self.repo.index.commit(
            "Merge feature branch",
            parent_commits=(self.c2, self.c3),
            head=True
        )

    def tearDown(self):
        """Clean up the temporary repository directory."""
        shutil.rmtree(self.repo_dir)

    def test_initial_commit(self):
        """
        Test parsing the diff of the very first commit in a repository.
        """
        diffs = parse_commit_diff(self.c1)
        self.assertEqual(len(diffs), 1)

        change = diffs[0]
        self.assertEqual(change['change_type'], 'A')
        self.assertEqual(change['old_path'], 'file1.txt')
        self.assertEqual(change['new_path'], 'file1.txt')
        self.assertIn('--- /dev/null', change['diff_text'])
        self.assertIn('+++ b/file1.txt', change['diff_text'])
        self.assertIn('+Initial content', change['diff_text'])

    def test_merge_commit_diffs_against_first_parent(self):
        """
        Test that a merge commit is diffed against its first parent,
        showing only the changes from the merged branch.
        """
        # C4's first parent is C2. The diff should show what C3 brought in,
        # which is the addition of file2.txt.
        diffs = parse_commit_diff(self.c4_merge)
        self.assertEqual(len(diffs), 1)

        change = diffs[0]
        self.assertEqual(change['change_type'], 'A')
        self.assertEqual(change['new_path'], 'file2.txt')
        self.assertIn('+Content for feature', change['diff_text'])

    def test_commit_with_modification(self):
        """
        Test a standard commit that modifies an existing file.
        """
        # C2 modified file1.txt, its parent is C1.
        diffs = parse_commit_diff(self.c2)
        self.assertEqual(len(diffs), 1)

        change = diffs[0]
        self.assertEqual(change['change_type'], 'M')
        self.assertEqual(change['old_path'], 'file1.txt')
        self.assertEqual(change['new_path'], 'file1.txt')
        self.assertIn('--- a/file1.txt', change['diff_text'])
        self.assertIn('+++ b/file1.txt', change['diff_text'])
        self.assertIn('+More on main.', change['diff_text'])

    def test_commit_with_multiple_changes(self):
        """
        Test a single commit with added, deleted, and renamed files.
        """
        # Add a new file to be deleted
        with open(self.file_path("to_delete.txt"), "w") as f:
            f.write("delete me")
        self.repo.index.add(["to_delete.txt"])
        setup_commit = self.repo.index.commit("add file to delete")

        # Perform multiple changes
        with open(self.file_path("file1.txt"), "w") as f:
            f.write("new file1 content")
        with open(self.file_path("added_file.txt"), "w") as f:
            f.write("I am new")
        self.repo.index.add(["file1.txt", "added_file.txt"])
        self.repo.index.remove(["to_delete.txt"])
        self.repo.index.move(["file2.txt", "renamed_file2.txt"])
        multi_change_commit = self.repo.index.commit("Multiple changes")

        diffs = parse_commit_diff(multi_change_commit)
        self.assertEqual(len(diffs), 4)

        # Create a dictionary for easy lookup
        changes = {d['new_path'] or d['old_path']: d for d in diffs}

        # Test modification
        mod_change = changes['file1.txt']
        self.assertEqual(mod_change['change_type'], 'M')
        self.assertEqual(mod_change['old_path'], 'file1.txt')
        self.assertIn('+new file1 content', mod_change['diff_text'])

        # Test deletion
        del_change = changes['to_delete.txt']
        self.assertEqual(del_change['change_type'], 'D')
        self.assertEqual(del_change['new_path'], None)
        self.assertIn('-delete me', del_change['diff_text'])

        # Test addition
        add_change = changes['added_file.txt']
        self.assertEqual(add_change['change_type'], 'A')
        self.assertEqual(add_change['old_path'], 'added_file.txt')
        self.assertIn('+I am new', add_change['diff_text'])

        # Test rename
        ren_change = changes['renamed_file2.txt']
        self.assertEqual(ren_change['change_type'], 'R')
        self.assertEqual(ren_change['old_path'], 'file2.txt')
        self.assertEqual(ren_change['new_path'], 'renamed_file2.txt')


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)