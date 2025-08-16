import requests

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