import unittest
import ast
import io
import sys

# The implementation to test
def parse_python_code_to_ast(source_code: str):
    """
    Parses a string of Python source code into an Abstract Syntax Tree (AST).

    This function leverages Python's built-in 'ast' module to perform the parsing.
    It is a simple wrapper that includes error handling for invalid syntax.

    Args:
        source_code: A string containing the Python code to be parsed.

    Returns:
        An 'ast.Module' object representing the root of the AST if the parsing
        is successful. Returns None if the source code contains a syntax error.
    """
    try:
        # The ast.parse() function is the core component that builds the tree.
        # It takes the source string and returns the root node of the AST.
        tree = ast.parse(source_code)
        return tree
    except SyntaxError as e:
        # If the source code is not syntactically correct Python,
        # ast.parse() raises a SyntaxError. We catch it here.
        print(f"Error: Invalid syntax in the provided code. Details: {e}")
        return None

class TestParsePythonCodeToAst(unittest.TestCase):

    def setUp(self):
        """Redirect stdout to capture print statements."""
        self.held, sys.stdout = sys.stdout, io.StringIO()

    def tearDown(self):
        """Restore stdout."""
        sys.stdout = self.held

    def test_valid_simple_expression(self):
        """Test parsing of a simple, valid Python expression."""
        code = "x = 1"
        tree = parse_python_code_to_ast(code)
        self.assertIsNotNone(tree)
        self.assertIsInstance(tree, ast.Module)
        self.assertEqual(len(tree.body), 1)
        self.assertIsInstance(tree.body[0], ast.Assign)

    def test_valid_function_definition(self):
        """Test parsing of a valid function definition."""
        code = "def my_function(a, b):\n    return a + b"
        tree = parse_python_code_to_ast(code)
        self.assertIsNotNone(tree)
        self.assertIsInstance(tree, ast.Module)
        self.assertEqual(len(tree.body), 1)
        self.assertIsInstance(tree.body[0], ast.FunctionDef)
        self.assertEqual(tree.body[0].name, "my_function")

    def test_valid_multiline_code(self):
        """Test parsing of valid multi-line code with a class."""
        code = """
class MyClass:
    def __init__(self):
        self.value = 0
"""
        tree = parse_python_code_to_ast(code)
        self.assertIsNotNone(tree)
        self.assertIsInstance(tree, ast.Module)
        self.assertIsInstance(tree.body[0], ast.ClassDef)
        self.assertEqual(tree.body[0].name, "MyClass")

    def test_empty_string(self):
        """Test that an empty string parses to an empty module."""
        code = ""
        tree = parse_python_code_to_ast(code)
        self.assertIsNotNone(tree)
        self.assertIsInstance(tree, ast.Module)
        self.assertEqual(len(tree.body), 0)

    def test_string_with_only_whitespace_and_comments(self):
        """Test that a string with only comments and whitespace parses."""
        code = "# This is a comment\n\n   \t"
        tree = parse_python_code_to_ast(code)
        self.assertIsNotNone(tree)
        self.assertIsInstance(tree, ast.Module)
        self.assertEqual(len(tree.body), 0)

    def test_invalid_syntax(self):
        """Test that code with a syntax error returns None."""
        code = "x = 1 + "
        result = parse_python_code_to_ast(code)
        self.assertIsNone(result)

    def test_incomplete_statement(self):
        """Test that an incomplete statement returns None."""
        code = "def my_func("
        result = parse_python_code_to_ast(code)
        self.assertIsNone(result)

    def test_error_message_on_invalid_syntax(self):
        """Test that a syntax error prints an error message to stdout."""
        invalid_code = "print 'hello'"  # Python 2 syntax
        parse_python_code_to_ast(invalid_code)
        output = sys.stdout.getvalue().strip()
        self.assertTrue(output.startswith("Error: Invalid syntax in the provided code."))
        self.assertIn("Missing parentheses in call to 'print'", output)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)