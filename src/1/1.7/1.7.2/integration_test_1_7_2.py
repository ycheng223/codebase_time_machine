import unittest
import sys
import os

# To test the web application, we need to simulate the project structure.
# We'll create temporary files for the modules to be imported.

# --- Create mock implementations based on the problem description ---

database_py_content = """
# A simple in-memory dictionary to act as a database.
db = {}

def save_data(session_id, data):
    \"\"\"Saves data for a given session ID.\"\"\"
    db[session_id] = data

def get_data(session_id):
    \"\"\"Retrieves data for a given session ID.\"\"\"
    return db.get(session_id)

def clear_data():
    \"\"\"Clears all data from the database.\"\"\"
    db.clear()
"""
with open("database.py", "w") as f:
    f.write(database_py_content)

data_processor_py_content = """
import datetime

def process_data(data):
    \"\"\"
    Processes the incoming form data.
    - Converts string values to uppercase.
    - Adds a timestamp.
    \"\"\"
    processed = {}
    for key, value in data.items():
        if isinstance(value, str):
            processed[key] = value.upper()
        else:
            # This path will be taken for missing form fields, which are None
            processed[key] = value
    processed['timestamp'] = datetime.datetime.now().isoformat()
    return processed
"""
with open("data_processor.py", "w") as f:
    f.write(data_processor_py_content)


web_interface_py_content = """
from flask import Flask, render_template_string, request, redirect, url_for, session
import data_processor
import database
import uuid

app = Flask(__name__)
# A secret key is required for session management
app.secret_key = 'a-test-secret-key-for-integration-tests'

HOME_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>User Input</title></head>
<body>
    <h1>Enter Your Details</h1>
    <form action="/submit" method="post">
        <label for="name">Name:</label><br>
        <input type="text" id="name" name="name"><br>
        <label for="email">Email:</label><br>
        <input type="text" id="email" name="email"><br><br>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
'''

RESULTS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Submission Results</title></head>
<body>
    <h1>Data Submitted Successfully</h1>
    {% if data %}
    <p>Name: {{ data.get('name', '') }}</p>
    <p>Email: {{ data.get('email', '') }}</p>
    <p>Submitted at: {{ data.get('timestamp', 'N/A') }}</p>
    {% else %}
    <p>No data found.</p>
    {% endif %}
    <a href="/">Go back</a>
</body>
</html>
'''

@app.route('/')
def home():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template_string(HOME_TEMPLATE)

@app.route('/submit', methods=['POST'])
def submit():
    user_id = session.get('user_id')
    if not user_id:
        # This case is unlikely with Flask's session handling but good practice
        return "Session error, please return to the home page.", 400

    user_data = {
        'name': request.form.get('name'),
        'email': request.form.get('email')
    }

    # This is where the integration happens
    processed_data = data_processor.process_data(user_data)
    database.save_data(user_id, processed_data)

    return redirect(url_for('results'))

@app.route('/results')
def results():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    # Retrieve data from the database component
    data = database.get_data(user_id)
    if not data:
        return "No data found for your session.", 404

    return render_template_string(RESULTS_TEMPLATE, data=data)
"""
with open("web_interface.py", "w") as f:
    f.write(web_interface_py_content)

# --- Now, import the modules for the test ---
import web_interface
import database


class WebInterfaceIntegrationTest(unittest.TestCase):

    def setUp(self):
        """Set up the test environment before each test."""
        # Configure the app for testing
        web_interface.app.config['TESTING'] = True
        web_interface.app.config['WTF_CSRF_ENABLED'] = False
        self.client = web_interface.app.test_client()
        # Ensure a clean state for the in-memory database
        database.clear_data()

    def tearDown(self):
        """Clean up after each test."""
        # You could add cleanup logic here if needed, but clearing
        # the DB in setUp is generally sufficient for this case.
        pass

    def test_home_page_loads_and_creates_session(self):
        """
        Tests if the home page ('/') loads correctly, returns a 200 OK status,
        and contains the expected form elements. This also implicitly tests
        that a session is created for a new user.
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<h1>Enter Your Details</h1>', response.data)
        self.assertIn(b'<form action="/submit" method="post">', response.data)
        self.assertIn(b'name="name"', response.data)
        self.assertIn(b'name="email"', response.data)

    def test_full_workflow_successful_submission_and_retrieval(self):
        """
        Tests the entire user workflow:
        1. Visit home page to establish a session.
        2. Submit valid data via POST to '/submit'.
        3. Check for a redirect to the '/results' page.
        4. Follow the redirect and verify the processed data is displayed.
        5. Directly inspect the database to confirm correct data storage.
        """
        with self.client as c:
            # 1. Establish session
            c.get('/')

            # 2. Submit valid data
            form_data = {'name': 'John Doe', 'email': 'john.doe@example.com'}
            submit_response = c.post('/submit', data=form_data)

            # 3. Check for redirect
            self.assertEqual(submit_response.status_code, 302)
            self.assertTrue(submit_response.location.endswith('/results'))

            # 4. Follow redirect and verify displayed data
            results_response = c.get('/results')
            self.assertEqual(results_response.status_code, 200)
            self.assertIn(b'Data Submitted Successfully', results_response.data)
            # Check for processed (uppercased) data
            self.assertIn(b'Name: JOHN DOE', results_response.data)
            self.assertIn(b'Email: JOHN.DOE@EXAMPLE.COM', results_response.data)
            self.assertIn(b'Submitted at:', results_response.data)

            # 5. Inspect database directly
            # There should be only one session and one entry
            self.assertEqual(len(database.db), 1)
            saved_data = list(database.db.values())[0]
            self.assertEqual(saved_data['name'], 'JOHN DOE')
            self.assertEqual(saved_data['email'], 'JOHN.DOE@EXAMPLE.COM')
            self.assertIn('timestamp', saved_data)

    def test_submission_with_empty_data(self):
        """
        Tests that submitting an empty form still completes the workflow,
        saving empty strings to the database and displaying them on the results page.
        This verifies the system gracefully handles empty but present fields.
        """
        with self.client as c:
            c.get('/')
            form_data = {'name': '', 'email': ''}
            submit_response = c.post('/submit', data=form_data)
            self.assertEqual(submit_response.status_code, 302) # Should still redirect

            results_response = c.get('/results')
            self.assertEqual(results_response.status_code, 200)
            # The page should display the labels but with empty content
            self.assertIn(b'Name: ', results_response.data)
            self.assertIn(b'Email: ', results_response.data)

            # Verify that empty strings were saved in the database
            saved_data = list(database.db.values())[0]
            self.assertEqual(saved_data['name'], '')
            self.assertEqual(saved_data['email'], '')
            self.assertIn('timestamp', saved_data)

    def test_accessing_results_without_submission(self):
        """
        Tests that if a user with a session tries to access '/results' before
        submitting data, they receive a 'not found' message and a 404 status,
        as no data exists for their session in the database.
        """
        with self.client as c:
            # Establish session by visiting home, but don't submit
            c.get('/')
            
            # Directly access results
            response = c.get('/results')
            self.assertEqual(response.status_code, 404)
            self.assertIn(b'No data found for your session.', response.data)

    def test_accessing_results_without_session(self):
        """
        Tests that attempting to access '/results' without a session
        (i.e., without visiting '/' first) results in a redirect to the home page.
        """
        response = self.client.get('/results')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))

    def test_submission_with_missing_form_field_causes_error(self):
        """
        Tests an important integration failure case. If a form field is missing,
        `request.form.get()` returns None. The `data_processor` attempts to call
        `.upper()` on None, which will raise an AttributeError. This test verifies
        that this exception occurs, indicating a lack of input validation.
        In testing mode, Flask propagates exceptions, so we can catch it.
        """
        with self.client as c:
            c.get('/') # Establish session
            
            # Data is missing the 'email' field
            malformed_data = {'name': 'Incomplete Data'}

            # The web_interface will call data_processor, which will raise the error.
            # We assert that this specific exception is raised during the POST request.
            with self.assertRaisesRegex(AttributeError, "'NoneType' object has no attribute 'upper'"):
                c.post('/submit', data=malformed_data)


# --- Clean up mock files ---
def cleanup_files():
    for f in ["database.py", "data_processor.py", "web_interface.py"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == '__main__':
    try:
        # Run the tests
        unittest.main(exit=False)
    finally:
        # Always clean up the files
        cleanup_files()
        # Clean up any generated __pycache__
        if os.path.exists("__pycache__"):
            import shutil
            shutil.rmtree("__pycache__")