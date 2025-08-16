import unittest
from unittest.mock import patch, MagicMock, call
import re
import requests

# Implementation from 1.6.1.1
def extract_ticket_ids(commit_message):
    """
    Extracts ticket IDs (e.g., JIRA-123, PROJ-456) from a commit message string.

    Args:
        commit_message (str): The commit message string to search within.

    Returns:
        list: A list of strings, where each string is a found ticket ID.
              Returns an empty list if no ticket IDs are found.
    """
    # Regex to find patterns like 'PROJ-123': one or more uppercase letters,
    # a hyphen, and one or more digits.
    pattern = r'[A-Z]+-\d+'
    
    # re.findall returns all non-overlapping matches of the pattern in the string
    # as a list of strings.
    return re.findall(pattern, commit_message)

# Implementation from 1.6.1.2
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

# The path to patch needs to be where the name is looked up.
# Since TicketSystemAPIClient is defined in the same file (__main__),
# the lookup path is '__main__.requests.Session'.
@patch('__main__.requests.Session')
class TestTicketSystemIntegration(unittest.TestCase):

    def setUp(self):
        self.base_url = 'https://mock-ticket-system.com'
        self.api_token = 'fake-token'
        self.commit_hash = 'a1b2c3d4'
        self.commit_url = f'https://github.com/example/repo/commit/{self.commit_hash}'

    def test_commit_with_single_ticket_updates_successfully(self, MockSession):
        # Arrange
        mock_session_instance = MockSession.return_value
        
        # Mock GET response for ticket details
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'id': 'PROJ-123', 'status': 'In Progress'}
        
        # Mock POST response for adding a comment
        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {'id': 'comment-567', 'body': f'Related commit: {self.commit_url}'}
        
        mock_session_instance.get.return_value = mock_get_response
        mock_session_instance.post.return_value = mock_post_response

        commit_message = "PROJ-123: Fix critical bug in user authentication"
        comment_body = f"Related commit: {self.commit_url}"

        # Act: This section simulates the core integration logic
        ticket_ids = extract_ticket_ids(commit_message)
        api_client = TicketSystemAPIClient(self.base_url, self.api_token)
        
        # Simulate a workflow: get details, then add a comment
        for ticket_id in ticket_ids:
            details = api_client.get_ticket_details(ticket_id)
            comment_result = api_client.add_comment(ticket_id, comment_body)

        # Assert
        self.assertEqual(ticket_ids, ['PROJ-123'])

        # Check that GET was called correctly
        mock_session_instance.get.assert_called_once_with(f"{self.base_url}/api/v1/tickets/PROJ-123")
        mock_get_response.raise_for_status.assert_called_once()
        self.assertEqual(details, {'id': 'PROJ-123', 'status': 'In Progress'})

        # Check that POST was called correctly
        mock_session_instance.post.assert_called_once_with(
            f"{self.base_url}/api/v1/tickets/PROJ-123/comments",
            json={'body': comment_body}
        )
        mock_post_response.raise_for_status.assert_called_once()
        self.assertEqual(comment_result['id'], 'comment-567')

    def test_commit_with_multiple_tickets_updates_all(self, MockSession):
        # Arrange
        mock_session_instance = MockSession.return_value
        
        # Mock POST to return different values for different tickets
        def post_side_effect(url, json):
            mock_response = MagicMock()
            mock_response.status_code = 201
            if "DEV-456" in url:
                mock_response.json.return_value = {'id': 'comment-1', 'body': json['body']}
            elif "QA-789" in url:
                mock_response.json.return_value = {'id': 'comment-2', 'body': json['body']}
            else:
                mock_response.status_code = 404
            return mock_response
        
        mock_session_instance.post.side_effect = post_side_effect

        commit_message = "Feat: DEV-456, QA-789: Refactor payment module and update test cases"
        comment_body = f"Related commit: {self.commit_url}"

        # Act
        ticket_ids = extract_ticket_ids(commit_message)
        api_client = TicketSystemAPIClient(self.base_url, self.api_token)
        
        results = []
        for ticket_id in ticket_ids:
            results.append(api_client.add_comment(ticket_id, comment_body))

        # Assert
        self.assertCountEqual(ticket_ids, ['DEV-456', 'QA-789'])
        self.assertEqual(mock_session_instance.post.call_count, 2)
        
        expected_calls = [
            call(f"{self.base_url}/api/v1/tickets/DEV-456/comments", json={'body': comment_body}),
            call(f"{self.base_url}/api/v1/tickets/QA-789/comments", json={'body': comment_body})
        ]
        mock_session_instance.post.assert_has_calls(expected_calls, any_order=True)

        self.assertIn({'id': 'comment-1', 'body': comment_body}, results)
        self.assertIn({'id': 'comment-2', 'body': comment_body}, results)
        
        mock_session_instance.get.assert_not_called()

    def test_commit_with_no_tickets_makes_no_api_calls(self, MockSession):
        # Arrange
        mock_session_instance = MockSession.return_value
        commit_message = "docs: Update the project README file"

        # Act
        ticket_ids = extract_ticket_ids(commit_message)
        
        # Simulate the workflow: if there are no tickets, the client isn't called
        if ticket_ids:
            api_client = TicketSystemAPIClient(self.base_url, self.api_token)
            for ticket_id in ticket_ids:
                api_client.add_comment(ticket_id, "some comment")

        # Assert
        self.assertEqual(ticket_ids, [])
        mock_session_instance.get.assert_not_called()
        mock_session_instance.post.assert_not_called()

    def test_api_failure_for_one_ticket_does_not_stop_others(self, MockSession):
        # Arrange
        mock_session_instance = MockSession.return_value
        
        # Mock successful response
        mock_success_response = MagicMock()
        mock_success_response.status_code = 201
        mock_success_response.json.return_value = {'id': 'comment-valid', 'body': 'Success'}
        
        # Mock failed response by configuring its raise_for_status method
        mock_failure_response = MagicMock()
        mock_failure_response.status_code = 404
        mock_failure_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")

        def post_side_effect(url, json):
            if "INVALID-999" in url:
                return mock_failure_response
            elif "VALID-123" in url:
                return mock_success_response
            return MagicMock(status_code=500)

        mock_session_instance.post.side_effect = post_side_effect
        
        commit_message = "Fix INVALID-999 and VALID-123"
        comment_body = f"Related commit: {self.commit_url}"
        
        # Act
        ticket_ids = extract_ticket_ids(commit_message)
        api_client = TicketSystemAPIClient(self.base_url, self.api_token)
        
        successful_updates = []
        failed_updates = []
        
        for ticket_id in ticket_ids:
            try:
                result = api_client.add_comment(ticket_id, comment_body)
                successful_updates.append((ticket_id, result))
            except requests.exceptions.RequestException as e:
                failed_updates.append((ticket_id, e))
        
        # Assert
        self.assertCountEqual(ticket_ids, ['INVALID-999', 'VALID-123'])
        
        self.assertEqual(len(successful_updates), 1)
        self.assertEqual(successful_updates[0][0], 'VALID-123')
        self.assertEqual(successful_updates[0][1], {'id': 'comment-valid', 'body': 'Success'})

        self.assertEqual(len(failed_updates), 1)
        self.assertEqual(failed_updates[0][0], 'INVALID-999')
        self.assertIsInstance(failed_updates[0][1], requests.exceptions.HTTPError)

        # Check that the mock session was called for both, and raise_for_status was triggered
        self.assertEqual(mock_session_instance.post.call_count, 2)
        mock_failure_response.raise_for_status.assert_called_once()
        mock_success_response.raise_for_status.assert_called_once()