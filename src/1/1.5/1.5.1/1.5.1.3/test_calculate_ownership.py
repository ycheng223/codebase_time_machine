import unittest

# The implementation to test
def calculate_ownership(change_history):
    """
    Calculates code ownership based on lines changed and author frequency.

    Args:
        change_history (list of dict): A list where each dictionary represents
                                      a change and must contain 'author',
                                      'lines_added', and 'lines_deleted' keys.
                                      Example: [{'author': 'dev1', 'lines_added': 10, 'lines_deleted': 2}]

    Returns:
        dict: A dictionary where keys are author names and values are another
              dictionary containing the total 'lines_changed' and the
              'commit_count' (author frequency).
              Example: {'dev1': {'lines_changed': 12, 'commit_count': 1}}
    """
    ownership_data = {}

    for change in change_history:
        author = change.get('author')
        if not author:
            continue

        # Ensure author is in the dictionary
        if author not in ownership_data:
            ownership_data[author] = {
                'lines_changed': 0,
                'commit_count': 0
            }

        # Calculate lines changed for this specific commit
        lines_changed = change.get('lines_added', 0) + change.get('lines_deleted', 0)

        # Update the author's totals
        ownership_data[author]['lines_changed'] += lines_changed
        ownership_data[author]['commit_count'] += 1

    return ownership_data

class TestCalculateOwnership(unittest.TestCase):

    def test_empty_history(self):
        """Test with an empty list of changes."""
        self.assertEqual(calculate_ownership([]), {})

    def test_single_author_single_commit(self):
        """Test a single commit by a single author."""
        history = [{'author': 'dev1', 'lines_added': 10, 'lines_deleted': 5}]
        expected = {'dev1': {'lines_changed': 15, 'commit_count': 1}}
        self.assertDictEqual(calculate_ownership(history), expected)

    def test_single_author_multiple_commits(self):
        """Test multiple commits by the same author."""
        history = [
            {'author': 'dev1', 'lines_added': 10, 'lines_deleted': 5},
            {'author': 'dev1', 'lines_added': 20, 'lines_deleted': 2}
        ]
        expected = {'dev1': {'lines_changed': 37, 'commit_count': 2}}
        self.assertDictEqual(calculate_ownership(history), expected)

    def test_multiple_authors(self):
        """Test a mix of commits from different authors."""
        history = [
            {'author': 'dev1', 'lines_added': 10, 'lines_deleted': 5},
            {'author': 'dev2', 'lines_added': 100, 'lines_deleted': 50},
            {'author': 'dev1', 'lines_added': 20, 'lines_deleted': 2}
        ]
        expected = {
            'dev1': {'lines_changed': 37, 'commit_count': 2},
            'dev2': {'lines_changed': 150, 'commit_count': 1}
        }
        self.assertDictEqual(calculate_ownership(history), expected)

    def test_commit_missing_author_key(self):
        """Test a commit dictionary that is missing the 'author' key."""
        history = [
            {'lines_added': 10, 'lines_deleted': 5},  # This should be skipped
            {'author': 'dev1', 'lines_added': 100, 'lines_deleted': 50}
        ]
        expected = {'dev1': {'lines_changed': 150, 'commit_count': 1}}
        self.assertDictEqual(calculate_ownership(history), expected)

    def test_commit_with_empty_or_none_author(self):
        """Test commits where the author value is None or an empty string."""
        history = [
            {'author': None, 'lines_added': 10, 'lines_deleted': 5},
            {'author': '', 'lines_added': 20, 'lines_deleted': 10},
            {'author': 'dev1', 'lines_added': 100, 'lines_deleted': 50}
        ]
        expected = {'dev1': {'lines_changed': 150, 'commit_count': 1}}
        self.assertDictEqual(calculate_ownership(history), expected)

    def test_commit_missing_line_change_keys(self):
        """Test commits that are missing 'lines_added' or 'lines_deleted' keys."""
        history = [
            {'author': 'dev1', 'lines_added': 10},  # missing deleted
            {'author': 'dev1', 'lines_deleted': 5},  # missing added
            {'author': 'dev1'},                   # missing both
            {'author': 'dev2', 'lines_added': 1, 'lines_deleted': 1}
        ]
        expected = {
            'dev1': {'lines_changed': 15, 'commit_count': 3},
            'dev2': {'lines_changed': 2, 'commit_count': 1}
        }
        self.assertDictEqual(calculate_ownership(history), expected)

    def test_commits_with_zero_values(self):
        """Test commits where line changes are zero."""
        history = [
            {'author': 'dev1', 'lines_added': 0, 'lines_deleted': 0},
            {'author': 'dev2', 'lines_added': 10, 'lines_deleted': 0},
            {'author': 'dev3', 'lines_added': 0, 'lines_deleted': 5}
        ]
        expected = {
            'dev1': {'lines_changed': 0, 'commit_count': 1},
            'dev2': {'lines_changed': 10, 'commit_count': 1},
            'dev3': {'lines_changed': 5, 'commit_count': 1}
        }
        self.assertDictEqual(calculate_ownership(history), expected)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)