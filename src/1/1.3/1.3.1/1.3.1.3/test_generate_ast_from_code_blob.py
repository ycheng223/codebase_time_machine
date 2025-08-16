import unittest
import ast
from typing import Optional

# The implementation to test
def generate_ast_from_code_blob(code_blob: str) -> Optional[ast.AST]:
    """
    Generates an Abstract Syntax Tree (AST) from a string of Python code.

    This function takes a string containing source code and attempts to parse
    it into an AST. If the code contains a syntax error, the function
    handles the exception gracefully and returns None.

    Args:
        code_blob: A string containing the Python source code to be parsed.

    Returns:
        An ast.AST object representing the root of the tree if parsing is
        successful, otherwise None.
    """
    try:
        tree = ast.parse(code_blob)
        return tree
    except (SyntaxError, ValueError):
        # A SyntaxError is raised for malformed code.
        # A ValueError can be raised for source code containing null bytes.
        return None

class TestGenerateAstFromCodeBlob(unittest.TestCase):

    def test_parse_simple_function(self):
        """Test parsing a simple function definition."""
        code = "def my_function():\n    pass"
        tree = generate_ast_from_code_blob(code)
        self.assertIsNotNone(tree)
        self.assertIsInstance(tree, ast.AST)
        self.assertEqual(len(tree.body), 1)
        
        node = tree.body[0]
        self.assertIsInstance(node, ast.FunctionDef)
        self.assertEqual(node.name, "my_function")

    def test_parse_function_with_args_and_body(self):
        """Test parsing a function with arguments and a return statement."""
        code = "def add(a, b):\n    return a + b"
        tree = generate_ast_from_code_blob(code)
        self.assertIsNotNone(tree)
        
        node = tree.body[0]
        self.assertIsInstance(node, ast.FunctionDef)
        self.assertEqual(node.name, "add")
        self.assertEqual(len(node.args.args), 2)
        self.assertEqual(node.args.args[0].arg, 'a')
        self.assertEqual(node.args.args[1].arg, 'b')
        self.assertIsInstance(node.body[0], ast.Return)

    def test_parse_simple_class(self):
        """Test parsing a simple class definition."""
        code = "class MyClass:\n    pass"
        tree = generate_ast_from_code_blob(code)
        self.assertIsNotNone(tree)
        self.assertIsInstance(tree, ast.AST)
        self.assertEqual(len(tree.body), 1)

        node = tree.body[0]
        self.assertIsInstance(node, ast.ClassDef)
        self.assertEqual(node.name, "MyClass")

    def test_parse_class_with_method(self):
        """Test parsing a class that contains a method."""
        code = "class Greeter:\n    def say_hello(self):\n        print('Hello')"
        tree = generate_ast_from_code_blob(code)
        self.assertIsNotNone(tree)
        
        class_node = tree.body[0]
        self.assertIsInstance(class_node, ast.ClassDef)
        self.assertEqual(class_node.name, "Greeter")
        self.assertEqual(len(class_node.body), 1)

        method_node = class_node.body[0]
        self.assertIsInstance(method_node, ast.FunctionDef)
        self.assertEqual(method_node.name, "say_hello")

    def test_parse_class_with_inheritance(self):
        """Test parsing a class that inherits from another class."""
        code = "class Child(Parent):\n    pass"
        tree = generate_ast_from_code_blob(code)
        self.assertIsNotNone(tree)

        class_node = tree.body[0]
        self.assertIsInstance(class_node, ast.ClassDef)
        self.assertEqual(class_node.name, "Child")
        self.assertEqual(len(class_node.bases), 1)
        
        base_class = class_node.bases[0]
        self.assertIsInstance(base_class, ast.Name)
        self.assertEqual(base_class.id, "Parent")

    def test_syntax_error_in_function(self):
        """Test that invalid function syntax returns None."""
        code = "def invalid_function(:\n    pass"
        tree = generate_ast_from_code_blob(code)
        self.assertIsNone(tree)

    def test_syntax_error_in_class(self):
        """Test that invalid class syntax returns None."""
        code = "class InvalidClass\n    pass"
        tree = generate_ast_from_code_blob(code)
        self.assertIsNone(tree)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)