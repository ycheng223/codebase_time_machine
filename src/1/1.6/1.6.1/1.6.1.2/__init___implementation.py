import requests

class TicketSystemAPIClient:
    """
    A simple API client for a generic ticket system.
    
    Handles authentication and provides methods for common actions like
    fetching ticket details and adding comments. It assumes a RESTful API
    with bearer token authentication.
    """
    def __init__(self, base_url, api_token):
        """
        Initializes the API client.

        Args:
            base_url (str): The base URL of the ticket system API
                            (e.g., 'https://api.jira.com').
            api_token (str): The API token for authentication.
        """
        if not base_url:
            raise ValueError("base_url cannot be empty.")
        if not api_token:
            raise ValueError("api_token cannot be empty.")
            
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def get_ticket_details(self, ticket_id):
        """
        Retrieves the details for a specific ticket.

        Args:
            ticket_id (str): The ID of the ticket (e.g., 'PROJ-123').

        Returns:
            dict: A dictionary containing the ticket details from the API.
        
        Raises:
            requests.exceptions.RequestException: For connection errors or HTTP error responses.
        """
        # This is a generic, plausible API endpoint structure.
        # It would need to be adapted for a specific system like Jira or Linear.
        url = f"{self.base_url}/api/v1/tickets/{ticket_id}"
        
        try:
            response = self.session.get(url)
            # Raise an HTTPError for bad responses (4xx client error or 5xx server error)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Re-raise the exception to be handled by the caller
            raise e

    def add_comment(self, ticket_id, comment_body):
        """
        Adds a comment to a specific ticket.

        Args:
            ticket_id (str): The ID of the ticket to comment on.
            comment_body (str): The text content of the comment.

        Returns:
            dict: A dictionary representing the newly created comment from the API.

        Raises:
            requests.exceptions.RequestException: For connection errors or HTTP error responses.
        """
        url = f"{self.base_url}/api/v1/tickets/{ticket_id}/comments"
        payload = {'body': comment_body}
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise e