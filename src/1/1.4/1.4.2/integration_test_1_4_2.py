import unittest
import requests
import io
import sys
from unittest.mock import patch, Mock

# --- Implementation 1.4.2.2 ---
def display_ownership_chart(api_url, company_id):
    """
    Fetches ownership data for a company from an API and prints a text-based chart.

    This function performs the entire process:
    1. Fetches hierarchical ownership data from a specified API endpoint.
    2. Processes the data.
    3. Prints a formatted, tree-like chart to the console.

    Args:
        api_url (str): The full URL of the API endpoint to fetch data from.
                       Example: 'https://api.example.com/v1/ownership/TICKER'
        company_id (str): A unique identifier for the company, used for display purposes.
    """
    # 1. Fetch data from the API
    try:
        response = requests.get(api_url, timeout=10)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch data for {company_id}: {e}")
        return
    except ValueError:
        print(f"Error: Failed to decode JSON response for {company_id}.")
        return

    # 2. Define a recursive helper to print the ownership tree
    def _print_node(node, prefix="", is_last=True):
        """Recursively prints a node and its children."""
        # Use box-drawing characters for the tree structure
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{node.get('ownerName', 'N/A')} ({node.get('stake', 0):.1f}%)")

        # Prepare the prefix for the children
        child_prefix = prefix + ("    " if is_last else "│   ")
        subsidiaries = node.get('subsidiaries', [])
        
        # Recursively call for each child
        for i, sub_node in enumerate(subsidiaries):
            is_child_last = (i == len(subsidiaries) - 1)
            _print_node(sub_node, prefix=child_prefix, is_last=is_child_last)

    # 3. Process and display the chart
    company_name = data.get('companyName', company_id)
    ownership_structure = data.get('ownership', [])

    if not ownership_structure:
        print(f"No ownership data found for {company_name}.")
        return

    print(f"Ownership Chart for: {company_name}")
    for i, owner in enumerate(ownership_structure):
        is_owner_last = (i == len(ownership_structure) - 1)
        _print_node(owner, prefix="", is_last=is_owner_last)

# --- Implementation 1.4.2.4 ---
def display_complexity_chart(api_url, company_id):
    """
    Fetches company complexity data from an API and prints a text-based chart.

    This function fetches data about a company's operational complexity,
    including an overall score and a breakdown by area, and displays it
    in a formatted summary with text-based bar charts for visual representation.

    Args:
        api_url (str): The full URL of the API endpoint to fetch data from.
                       Example: 'https://api.example.com/v1/complexity/TICKER'
        company_id (str): A unique identifier for the company, used for display purposes.
    """
    # 1. Fetch data from the API
    try:
        response = requests.get(api_url, timeout=10)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch complexity data for {company_id}: {e}")
        return
    except ValueError:
        print(f"Error: Failed to decode JSON response for {company_id}.")
        return

    # 2. Extract data from the response, with defaults for missing keys
    company_name = data.get('companyName', company_id)
    overall_score = data.get('complexityScore')
    breakdown = data.get('breakdown', [])

    # 3. Print the chart header
    print(f"Complexity Chart for: {company_name}")
    print("=" * 45)

    if overall_score is not None:
        print(f"Overall Complexity Score: {overall_score}/100")
    
    if not breakdown:
        print("\nNo complexity breakdown data available.")
        return

    # 4. Define a helper to generate a text-based progress bar
    def _create_bar(score, total_chars=25):
        """Creates a text-based bar representation of a score."""
        if not isinstance(score, (int, float)) or not 0 <= score <= 100:
            return "[Invalid Score Data]"
        filled_chars = int((score / 100) * total_chars)
        empty_chars = total_chars - filled_chars
        return f"[{'█' * filled_chars}{'░' * empty_chars}]"

    # 5. Iterate through the complexity breakdown and print each item
    for item in breakdown:
        print("-" * 45)
        area = item.get('area', 'Unnamed Area')
        score = item.get('score')
        details = item.get('details', 'No details provided.')

        print(f"Area: {area}")
        if score is not None:
            bar = _create_bar(score)
            # Pad the score string to align the bars
            score_str = f"Score: {score}/100".ljust(15)
            print(f"{score_str} {bar}")
        
        print(f"Details: {details}")
    
    print("=" * 45)

class TestFrontendVisualizationIntegration(unittest.TestCase):

    def setUp(self):
        # Redirect stdout to capture print statements
        self.held_stdout = sys.stdout
        sys.stdout = io.StringIO()

        # Mock data for a fictional company "INNO"
        self.company_id = "INNO"
        self.ownership_url = f"https://api.test.com/v1/ownership/{self.company_id}"
        self.complexity_url = f"https://api.test.com/v1/complexity/{self.company_id}"
        
        self.mock_ownership_data = {
            "companyName": "Innovate Corp",
            "ownership": [
                {
                    "ownerName": "Global Investments Inc.",
                    "stake": 45.5,
                    "subsidiaries": [
                        {"ownerName": "Alpha Fund", "stake": 25.0},
                        {"ownerName": "Beta Fund", "stake": 20.5}
                    ]
                },
                {"ownerName": "Founder's Trust", "stake": 30.0},
                {"ownerName": "Public Float", "stake": 24.5}
            ]
        }
        
        self.mock_complexity_data = {
            "companyName": "Innovate Corp",
            "complexityScore": 78,
            "breakdown": [
                {
                    "area": "Supply Chain",
                    "score": 92,
                    "details": "High dependency on international suppliers."
                },
                {
                    "area": "Regulatory",
                    "score": 65,
                    "details": "Operates in multiple jurisdictions with varying compliance needs."
                }
            ]
        }

    def tearDown(self):
        # Restore stdout
        sys.stdout = self.held_stdout

    @patch('requests.get')
    def test_full_report_successful_integration(self, mock_get):
        """
        Tests the integrated workflow of fetching and displaying both ownership
        and complexity charts for a single company. This simulates a user
        viewing a complete company report.
        """
        # Configure mock to return different data based on the URL requested
        def get_side_effect(url, timeout):
            mock_response = Mock()
            if url == self.ownership_url:
                mock_response.json.return_value = self.mock_ownership_data
            elif url == self.complexity_url:
                mock_response.json.return_value = self.mock_complexity_data
            else:
                mock_response.status_code = 404
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")
            return mock_response
        
        mock_get.side_effect = get_side_effect

        # --- Execute the integrated workflow ---
        display_ownership_chart(self.ownership_url, self.company_id)
        # Add a separator for clarity in the combined output
        print("\n---\n")
        display_complexity_chart(self.complexity_url, self.company_id)

        # --- Assertions on the combined output ---
        output = sys.stdout.getvalue()

        # Check for ownership chart content
        self.assertIn("Ownership Chart for: Innovate Corp", output)
        self.assertIn("├── Global Investments Inc. (45.5%)", output)
        self.assertIn("│   └── Beta Fund (20.5%)", output)
        self.assertIn("└── Public Float (24.5%)", output)
        
        # Check for the separator
        self.assertIn("\n---\n", output)

        # Check for complexity chart content
        self.assertIn("Complexity Chart for: Innovate Corp", output)
        self.assertIn("Overall Complexity Score: 78/100", output)
        self.assertIn("Area: Supply Chain", output)
        self.assertIn("[███████████████████████░░]", output) # 92/100 * 25 chars
        self.assertIn("Details: Operates in multiple jurisdictions with varying compliance needs.", output)

        # Verify that both API endpoints were called
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_any_call(self.ownership_url, timeout=10)
        mock_get.assert_any_call(self.complexity_url, timeout=10)

    @patch('requests.get')
    def test_ownership_chart_with_missing_data(self, mock_get):
        """Tests that the ownership chart handles missing and empty data gracefully."""
        mock_response = Mock()
        mock_data = {
            "companyName": "Incomplete Data Inc.",
            "ownership": [
                {"ownerName": "Data Holder LLC"}, # Missing stake
                {"stake": 15.0}, # Missing ownerName
                {"ownerName": "Solo Owner", "stake": 25.0} # No subsidiaries key
            ]
        }
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response

        display_ownership_chart(self.ownership_url, self.company_id)
        output = sys.stdout.getvalue()

        self.assertIn("Ownership Chart for: Incomplete Data Inc.", output)
        self.assertIn("├── Data Holder LLC (0.0%)", output)
        self.assertIn("├── N/A (15.0%)", output)
        self.assertIn("└── Solo Owner (25.0%)", output)

    @patch('requests.get')
    def test_complexity_chart_with_invalid_score(self, mock_get):
        """Tests that the complexity chart handles non-numeric scores in the breakdown."""
        mock_response = Mock()
        mock_data = {
            "companyName": "Faulty Data Corp",
            "complexityScore": 50,
            "breakdown": [
                {"area": "Valid Area", "score": 75},
                {"area": "Invalid Area", "score": "HIGH"},
                {"area": "No Score Area"}
            ]
        }
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response

        display_complexity_chart(self.complexity_url, self.company_id)
        output = sys.stdout.getvalue()
        
        self.assertIn("Area: Valid Area", output)
        self.assertIn("[██████████████████░░░░░░░]", output) # 75/100 * 25 chars
        self.assertIn("Area: Invalid Area", output)
        self.assertIn("[Invalid Score Data]", output)
        self.assertIn("Area: No Score Area", output)
        # Check that score and bar are not printed for "No Score Area"
        self.assertNotIn("Score:", output.split("Area: No Score Area")[1])

    @patch('requests.get')
    def test_no_data_found_scenarios(self, mock_get):
        """Tests the components' behavior when the API returns empty data lists."""
        mock_response = Mock()
        
        # Scenario 1: No ownership data
        mock_response.json.return_value = {"companyName": "Innovate Corp", "ownership": []}
        mock_get.return_value = mock_response
        display_ownership_chart(self.ownership_url, self.company_id)
        self.assertIn("No ownership data found for Innovate Corp.", sys.stdout.getvalue())

        # Reset stdout for the next test
        sys.stdout = io.StringIO()

        # Scenario 2: No complexity breakdown
        mock_response.json.return_value = {"companyName": "Innovate Corp", "complexityScore": 80, "breakdown": []}
        display_complexity_chart(self.complexity_url, self.company_id)
        output = sys.stdout.getvalue()
        self.assertIn("Overall Complexity Score: 80/100", output)
        self.assertIn("\nNo complexity breakdown data available.", output)
        
    @patch('requests.get')
    def test_api_and_network_failures(self, mock_get):
        """Tests that both components handle various API and network errors correctly."""
        # --- Test HTTP 404 Error ---
        mock_get.side_effect = requests.exceptions.RequestException("404 Client Error")
        
        display_ownership_chart(self.ownership_url, self.company_id)
        self.assertIn(f"Error: Failed to fetch data for {self.company_id}", sys.stdout.getvalue())
        
        sys.stdout = io.StringIO() # Reset stdout
        display_complexity_chart(self.complexity_url, self.company_id)
        self.assertIn(f"Error: Failed to fetch complexity data for {self.company_id}", sys.stdout.getvalue())

        # --- Test JSON Decode Error ---
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.side_effect = [mock_response, mock_response] # Provide a mock for each call

        sys.stdout = io.StringIO() # Reset stdout
        display_ownership_chart(self.ownership_url, self.company_id)
        self.assertIn(f"Error: Failed to decode JSON response for {self.company_id}.", sys.stdout.getvalue())

        sys.stdout = io.StringIO() # Reset stdout
        display_complexity_chart(self.complexity_url, self.company_id)
        self.assertIn(f"Error: Failed to decode JSON response for {self.company_id}.", sys.stdout.getvalue())


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)