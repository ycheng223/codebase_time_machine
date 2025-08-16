import unittest
from unittest.mock import patch, MagicMock
import ast
import re
import os
import openai

# --- Implementations provided for the Semantic Analysis Engine ---

# Component 1: Code Parser (from 1.2.1/1.2.1.2)
def parse_python_code_to_ast(source_code: str):
    """
    Parses a string of Python source code into an Abstract Syntax Tree (AST).
    """
    try:
        return ast.parse(source_code)
    except SyntaxError as e:
        # In a real scenario, we might have more robust error handling.
        # For the test, this is sufficient.
        raise e

# Component 2: Semantic Change Identifier (from 1.2.2/1.2.2.2)
def identify_semantic_changes(old_code: str, new_code: str):
    """
    Identifies semantic changes between two versions of Python code by comparing their ASTs.
    This is a simplified implementation for integration testing purposes.
    """
    changes = []
    try:
        old_tree = parse_python_code_to_ast(old_code)
        new_tree = parse_python_code_to_ast(new_code)
    except SyntaxError:
        return ["Syntax error in one of the code versions."]

    old_nodes = {node.name: node for node in ast.walk(old_tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    new_nodes = {node.name: node for node in ast.walk(new_tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}

    # Check for added and removed top-level definitions
    added = new_nodes.keys() - old_nodes.keys()
    removed = old_nodes.keys() - new_nodes.keys()

    for item in added:
        node_type = "Class" if isinstance(new_nodes[item], ast.ClassDef) else "Function"
        changes.append(f"{node_type} '{item}' was added.")

    for item in removed:
        node_type = "Class" if isinstance(old_nodes[item], ast.ClassDef) else "Function"
        changes.append(f"{node_type} '{item}' was removed.")

    # Check for modified bodies of existing functions/classes
    for name, old_node in old_nodes.items():
        if name in new_nodes:
            new_node = new_nodes[name]
            # ast.dump provides a string representation of the node's structure, ignoring comments/whitespace.
            if ast.dump(old_node.body) != ast.dump(new_node.body):
                node_type = "Class" if isinstance(old_node, ast.ClassDef) else "Function"
                changes.append(f"{node_type} '{name}' body was modified.")
    
    # If no structural changes were found, check for any change at all
    if not changes and ast.dump(old_tree) != ast.dump(new_tree):
        changes.append("Minor non-functional change detected (e.g., docstrings, comments).")
    
    if not changes and old_code != new_code:
         changes.append("Non-semantic change detected (e.g., whitespace).")


    return changes

# Component 3: Commit Summary Generator (from 1.2.3/1.2.3.3)
def generate_commit_summary(diff_text: str, commit_message: str) -> str:
    """
    Generates a high-level summary for a commit using an LLM.
    NOTE: This function makes a real API call which will be mocked in the test.
    """
    # In a real application, the API key would be securely managed.
    # openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f"""
    Based on the user's commit message and the code diff, generate a brief, one-sentence summary of the change.

    Original Commit Message: "{commit_message}"

    Code Diff:
    ```diff
    {diff_text}
    ```

    One-sentence Summary:
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert programmer who writes concise summaries of code changes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=60
        )
        summary = response.choices[0].message['content'].strip()
        return summary
    except Exception as e:
        # In a real scenario, log the error.
        return f"Error generating summary: {str(e)}"

# --- Integration Test ---

class TestSemanticAnalysisEngineIntegration(unittest.TestCase):

    def test_integration_refactor_function(self):
        """
        Tests the full pipeline for a function refactoring scenario.
        1. `identify_semantic_changes` should detect a modified function body.
        2. `generate_commit_summary` should be called with the correct context.
        """
        old_code = """
def calculate_sum(numbers):
    total = 0
    for n in numbers:
        total += n
    return total
"""
        new_code = """
def calculate_sum(numbers):
    # Use a more Pythonic way
    return sum(numbers)
"""
        # Step 1: Identify semantic changes
        semantic_report = identify_semantic_changes(old_code, new_code)
        self.assertEqual(len(semantic_report), 1)
        self.assertIn("Function 'calculate_sum' body was modified.", semantic_report)

        # Step 2: Generate a summary (mocking the OpenAI call)
        diff = """
-    total = 0
-    for n in numbers:
-        total += n
-    return total
+    # Use a more Pythonic way
+    return sum(numbers)
"""
        commit_message = "Refactor: Simplify calculate_sum function"
        expected_summary = "Refactored the `calculate_sum` function to use the built-in `sum()` for improved readability and performance."

        # Mock the OpenAI API call
        mock_openai_response = MagicMock()
        mock_openai_response.choices = [
            {'message': {'content': expected_summary}}
        ]

        with patch('openai.ChatCompletion.create', return_value=mock_openai_response) as mock_create:
            # Call the function that uses the API
            actual_summary = generate_commit_summary(diff, commit_message)

            # Assert the final output is what we expect from the mock
            self.assertEqual(actual_summary, expected_summary)

            # Assert the API was called
            mock_create.assert_called_once()
            
            # Optional: Inspect the prompt sent to the API
            call_args, call_kwargs = mock_create.call_args
            sent_prompt = call_kwargs['messages'][1]['content']
            self.assertIn(commit_message, sent_prompt)
            self.assertIn(diff, sent_prompt)

    def test_integration_add_new_feature(self):
        """
        Tests the full pipeline for adding a new function.
        1. `identify_semantic_changes` should detect a new function.
        2. `generate_commit_summary` should be called to summarize the new feature.
        """
        old_code = """
class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        return [x * 2 for x in self.data]
"""
        new_code = """
class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        return [x * 2 for x in self.data]
    
    def validate(self):
        \"\"\"Validates the data.\"\"\"
        if not isinstance(self.data, list):
            raise TypeError("Data must be a list")
        return True
"""
        # Step 1: Identify semantic changes
        semantic_report = identify_semantic_changes(old_code, new_code)
        self.assertEqual(len(semantic_report), 2)
        # The change identifier sees a modified class body AND a new function.
        # This is plausible behavior for a simple AST walker.
        self.assertIn("Class 'DataProcessor' body was modified.", semantic_report)
        self.assertIn("Function 'validate' was added.", semantic_report)


        # Step 2: Generate a summary
        diff = """
+    
+    def validate(self):
+        \"\"\"Validates the data.\"\"\"
+        if not isinstance(self.data, list):
+            raise TypeError("Data must be a list")
+        return True
"""
        commit_message = "feat: Add validation method to DataProcessor"
        expected_summary = "Introduced a `validate` method to the `DataProcessor` class to ensure input data is a list."

        mock_openai_response = MagicMock()
        mock_openai_response.choices = [{'message': {'content': expected_summary}}]

        with patch('openai.ChatCompletion.create', return_value=mock_openai_response) as mock_create:
            actual_summary = generate_commit_summary(diff, commit_message)

            self.assertEqual(actual_summary, expected_summary)
            mock_create.assert_called_once()
            sent_prompt = mock_create.call_args[1]['messages'][1]['content']
            self.assertIn("Add validation method", sent_prompt)

    def test_integration_no_semantic_change(self):
        """
        Tests the pipeline when only a comment is added.
        1. `identify_semantic_changes` should report no significant changes.
        2. The summary generation can still proceed for documentation updates.
        """
        old_code = """
def get_user(user_id):
    return db.fetch(user_id)
"""
        new_code = """
def get_user(user_id):
    # TODO: Add caching layer here in the future
    return db.fetch(user_id)
"""
        # Step 1: Identify semantic changes
        # Our simple implementation does not distinguish comments well, but it should not find a body modification
        # because the AST structure of the 'return' statement is unchanged.
        # It relies on ast.dump(), which ignores comments.
        semantic_report = identify_semantic_changes(old_code, new_code)
        self.assertEqual(semantic_report, [])


        # Step 2: Even with no semantic changes, we might want a summary for a docs/comment commit.
        diff = """
+    # TODO: Add caching layer here in the future
"""
        commit_message = "docs: Add a TODO comment for future work"
        expected_summary = "Added a TODO comment to the `get_user` function regarding a future caching implementation."

        mock_openai_response = MagicMock()
        mock_openai_response.choices = [{'message': {'content': expected_summary}}]

        with patch('openai.ChatCompletion.create', return_value=mock_openai_response) as mock_create:
            actual_summary = generate_commit_summary(diff, commit_message)
            self.assertEqual(actual_summary, expected_summary)
            mock_create.assert_called_once()
            sent_prompt = mock_create.call_args[1]['messages'][1]['content']
            self.assertIn("Add a TODO comment", sent_prompt)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)