import unittest
from unittest import mock
from datetime import datetime, timedelta
import requests

# ASSUMED IMPLEMENTATIONS BASED ON PROVIDED SIGNATURES
# These functions are provided here to make the test executable and self-contained.
# The test is designed to verify the interaction between these components.

# --- 1.4.1 Data Aggregation ---

def aggregate_lines_changed_per_author(commits_data):
    """
    Aggregates lines changed per author.
    Assumes commits_data is a list of dicts, each with 'author',
    'lines_added', and 'lines_deleted' keys.
    """
    author_stats = {}
    for commit in commits_data:
        author = commit.get('author')
        lines_changed = commit.get('lines_added', 0) + commit.get('lines_deleted', 0)
        if author:
            author_stats[author] = author_stats.get(author, 0) + lines_changed
    return author_stats

def aggregate_complexity_over_time(commits_data):
    """
    Aggregates a complexity metric over time.
    Assumes commits_data is a list of dicts, each with 'timestamp' (ISO format)
    and 'cyclomatic_complexity'.
    Returns a sorted list of dictionaries.
    """
    complexity_data = []
    for commit in commits_data:
        timestamp_str = commit.get('timestamp')
        complexity = commit.get('cyclomatic_complexity')
        if timestamp_str and complexity is not None:
            complexity_data.append({
                'timestamp': timestamp_str,
                'complexity': complexity
            })
    
    # Sort by timestamp to ensure chronological order
    complexity_data.sort(key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')))
    return complexity_data

# --- 1.4.2 Data Visualization ---
# For testability, we assume the display functions use a plotting utility.
# We will mock this utility to verify it's called correctly.
class PlottingUtility:
    def show_bar_chart(self, data, title=""):
        # In a real application, this would render a bar chart.
        pass

    def show_line_chart(self, data, title=""):
        # In a real application, this would render a line chart.
        pass

# A global instance of our plotting utility that the display functions will use.
plotter = PlottingUtility()

def display_ownership_chart(api_url, company_id):
    """
    Fetches ownership data and displays it as a bar chart.
    """
    try:
        response = requests.get(f"{api_url}/ownership/{company_id}")
        response.raise_for_status()
        data = response.json()
        plotter.show_bar_chart(data, title=f"Code Ownership for Company {company_id}")
        return True
    except requests.exceptions.RequestException as e:
        # In a real app, might log this error.
        return False

def display_complexity_chart(api_url, company_id):
    """
    Fetches company complexity data and displays it as a line chart.
    """
    try:
        response = requests.get(f"{api_url}/complexity/{company_id}")
        response.raise_for_status()
        data = response.json()
        plotter.show_line_chart(data, title=f"Code Complexity Over Time for Company {company_id}")
        return True
    except requests.exceptions.RequestException as e:
        return False


# --- INTEGRATION TEST ---

class TestDataVisualizationIntegration(unittest.TestCase):

    def setUp(self):
        """Set up common test data and constants."""
        self.api_url = "http://fakeapi.test.com/api/v1"
        self.company_id = "comp_123"
        
        # Sample raw data that will be fed into the aggregation functions.
        now = datetime.utcnow()
        self.sample_commits_data = [
            {
                'author': 'Alice',
                'lines_added': 100,
                'lines_deleted': 20,
                'timestamp': (now - timedelta(days=3)).isoformat() + 'Z',
                'cyclomatic_complexity': 15
            },
            {
                'author': 'Bob',
                'lines_added': 50,
                'lines_deleted': 50,
                'timestamp': (now - timedelta(days=2)).isoformat() + 'Z',
                'cyclomatic_complexity': 25
            },
            {
                'author': 'Alice',
                'lines_added': 75,
                'lines_deleted': 5,
                'timestamp': (now - timedelta(days=1)).isoformat() + 'Z',
                'cyclomatic_complexity': 20
            },
            {
                'author': 'Charlie',
                'lines_added': 10,
                'lines_deleted': 0,
                'timestamp': now.isoformat() + 'Z',
                'cyclomatic_complexity': 18
            }
        ]

    def test_aggregation_to_visualization_pipeline(self):
        """
        Tests the complete flow:
        1. Aggregate raw commit data.
        2. Mock an API that serves this aggregated data.
        3. Call display functions that fetch from the mock API.
        4. Verify that the visualization utility is called with the correct data.
        """
        # Step 1: Run the aggregation functions to get the expected results.
        # This data will be used to set up the mock API's response.
        expected_ownership_data = aggregate_lines_changed_per_author(self.sample_commits_data)
        expected_complexity_data = aggregate_complexity_over_time(self.sample_commits_data)

        # Expected results for assertion
        self.assertEqual(expected_ownership_data, {'Alice': 200, 'Bob': 100, 'Charlie': 10})
        self.assertEqual(len(expected_complexity_data), 4)
        self.assertEqual(expected_complexity_data[0]['complexity'], 15)
        self.assertEqual(expected_complexity_data[3]['complexity'], 18)

        # Step 2: Set up a side effect function for mocking `requests.get`.
        # This allows us to return different data based on the URL being requested.
        def mock_api_get(url, *args, **kwargs):
            mock_response = mock.Mock()
            if url == f"{self.api_url}/ownership/{self.company_id}":
                mock_response.status_code = 200
                mock_response.json.return_value = expected_ownership_data
                return mock_response
            elif url == f"{self.api_url}/complexity/{self.company_id}":
                mock_response.status_code = 200
                mock_response.json.return_value = expected_complexity_data
                return mock_response
            
            # Default case for unexpected URLs
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")
            return mock_response

        # Step 3: Patch external dependencies (requests and the plotting utility).
        with mock.patch('requests.get', side_effect=mock_api_get) as mock_get, \
             mock.patch.object(plotter, 'show_bar_chart') as mock_show_bar, \
             mock.patch.object(plotter, 'show_line_chart') as mock_show_line:

            # Step 4: Call the display functions, which will trigger the mocked dependencies.
            ownership_success = display_ownership_chart(self.api_url, self.company_id)
            complexity_success = display_complexity_chart(self.api_url, self.company_id)

            # --- Assertions ---

            # Check that the functions reported success
            self.assertTrue(ownership_success, "display_ownership_chart should return True on success")
            self.assertTrue(complexity_success, "display_complexity_chart should return True on success")

            # Verify that `requests.get` was called for both endpoints.
            expected_calls = [
                mock.call(f"{self.api_url}/ownership/{self.company_id}"),
                mock.call(f"{self.api_url}/complexity/{self.company_id}")
            ]
            mock_get.assert_has_calls(expected_calls, any_order=True)
            self.assertEqual(mock_get.call_count, 2)
            
            # Verify that the bar chart for ownership was called once with the correct aggregated data.
            mock_show_bar.assert_called_once()
            call_args, call_kwargs = mock_show_bar.call_args
            self.assertEqual(call_args[0], expected_ownership_data)
            self.assertIn('title', call_kwargs)
            
            # Verify that the line chart for complexity was called once with the correct aggregated data.
            mock_show_line.assert_called_once()
            call_args, call_kwargs = mock_show_line.call_args
            self.assertEqual(call_args[0], expected_complexity_data)
            self.assertIn('title', call_kwargs)

    def test_api_failure_scenario(self):
        """
        Tests that display functions handle API failures gracefully.
        The integration here is between the `requests` call and the function's error handling.
        """
        # Configure the mock to simulate a server error
        with mock.patch('requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
            mock_get.return_value = mock_response

            # Call the display functions and expect them to fail gracefully
            ownership_success = display_ownership_chart(self.api_url, self.company_id)
            complexity_success = display_complexity_chart(self.api_url, self.company_id)

            # Assert that the functions returned False, indicating failure
            self.assertFalse(ownership_success, "display_ownership_chart should return False on API error")
            self.assertFalse(complexity_success, "display_complexity_chart should return False on API error")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)