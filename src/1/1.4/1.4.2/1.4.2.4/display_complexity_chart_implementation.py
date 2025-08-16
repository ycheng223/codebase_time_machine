import requests

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