import unittest
# Assuming the function to be tested is in a file named 'semantic_diff.py'
# from semantic_diff import identify_semantic_changes
# For the purpose of this task, the function is assumed to be available in the scope.

# SIBLING TASK (1.2.2.2) CONTEXT provides this function
import ast
import re

def identify_semantic_changes(old_code: str, new_code: str):
    """
    Identifies semantic changes between two Python code snippets.

    Detects 'Function Added', 'Function Removed', 'Class Renamed',
    'Dependency Changed' and other similar changes.

    Args:
        old_code: A string containing the old version of the Python code.
        new_code: A string containing the new version of the Python code.

    Returns:
        A list of strings describing the identified semantic changes.
    """

    class CodeVisitor(ast.NodeVisitor):
        """A node visitor to extract top-level functions, classes, and imports."""
        def __init__(self):
            self.functions = {}  # Maps function name to its AST node
            self.classes = {}    # Maps class name to its AST node
            self.dependencies = set()

        def visit_FunctionDef(self, node):
            self.functions[node.name] = node
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            self.classes[node.name] = node
            self.generic_visit(node)

        def visit_Import(self, node):
            for alias in node.names:
                self.dependencies.add(alias.name)
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if node.module:
                self.dependencies.add(node.module)
            self.generic_visit(node)

    changes = []
    try:
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
    except SyntaxError as e:
        return [f"Syntax error in code: {e}"]

    old_visitor = CodeVisitor()
    old_visitor.visit(old_tree)

    new_visitor = CodeVisitor()
    new_visitor.visit(new_tree)

    # 1. Compare Dependencies
    added_deps = sorted(list(new_visitor.dependencies - old_visitor.dependencies))
    removed_deps = sorted(list(old_visitor.dependencies - new_visitor.dependencies))
    for dep in added_deps:
        changes.append(f"Dependency Added: {dep}")
    for dep in removed_deps:
        changes.append(f"Dependency Removed: {dep}")

    # Regex to remove location markers (lineno, col_offset) from AST dump
    location_regex = re.compile(r'(, |)lineno=\d+, col_offset=\d+(, end_lineno=\d+, end_col_offset=\d+|)')

    def get_normalized_dump(node):
        """Get a string representation of a node's body, ignoring location."""
        dump = ast.dump(node.body)
        return location_regex.sub('', dump)

    def find_structure_changes(old_items, new_items, item_type):
        """Compare dictionaries of structures (functions/classes) to find changes."""
        old_names = set(old_items.keys())
        new_names = set(new_items.keys())

        removed_names = old_names - new_names
        added_names = new_names - old_names

        handled_additions = set()
        handled_removals = set()

        # Attempt to detect renames by comparing normalized body structures
        for old_name in removed_names:
            old_node = old_items[old_name]
            old_body_dump = get_normalized_dump(old_node)

            for new_name in added_names:
                if new_name in handled_additions:
                    continue

                new_node = new_items[new_name]
                new_body_dump = get_normalized_dump(new_node)

                if old_body_dump == new_body_dump and old_body_dump != "[]":
                    changes.append(f"{item_type} Renamed: '{old_name}' to '{new_name}'")
                    handled_removals.add(old_name)
                    handled_additions.add(new_name)
                    break

        # Report remaining items as simple additions or removals
        for name in sorted(list(added_names - handled_additions)):
            changes.append(f"{item_type} Added: {name}")
        for name in sorted(list(removed_names - handled_removals)):
            changes.append(f"{item_type} Removed: {name}")

    # 2. Compare Functions
    find_structure_changes(old_visitor.functions, new_visitor.functions, "Function")

    # 3. Compare Classes
    find_structure_changes(old_visitor.classes, new_visitor.classes, "Class")

    return changes


class TestSemanticDiff(unittest.TestCase):
    """Unit tests for the identify_semantic_changes function."""

    def test_no_changes(self):
        """Test that identical code results in no changes."""
        code = """
import os
def my_function():
    print("Hello")
class MyClass:
    pass
"""
        self.assertEqual(identify_semantic_changes(code, code), [])

    def test_function_added(self):
        """Test detection of a new function."""
        old_code = "pass"
        new_code = "def new_func():\n    return 42"
        self.assertEqual(identify_semantic_changes(old_code, new_code), ["Function Added: new_func"])

    def test_function_removed(self):
        """Test detection of a removed function."""
        old_code = "def old_func():\n    return 42"
        new_code = "pass"
        self.assertEqual(identify_semantic_changes(old_code, new_code), ["Function Removed: old_func"])

    def test_function_renamed(self):
        """Test detection of a renamed function with an identical body."""
        old_code = "def old_name():\n    return 1 + 2"
        new_code = "def new_name():\n    return 1 + 2"
        self.assertEqual(identify_semantic_changes(old_code, new_code), ["Function Renamed: 'old_name' to 'new_name'"])

    def test_function_body_changed_not_detected(self):
        """Test that a change in a function's body is not detected if the name is the same."""
        old_code = "def my_func():\n    return 1"
        new_code = "def my_func():\n    return 2"
        self.assertEqual(identify_semantic_changes(old_code, new_code), [])

    def test_class_added(self):
        """Test detection of a new class."""
        old_code = "pass"
        new_code = "class NewClass:\n    pass"
        self.assertEqual(identify_semantic_changes(old_code, new_code), ["Class Added: NewClass"])

    def test_class_removed(self):
        """Test detection of a removed class."""
        old_code = "class OldClass:\n    pass"
        new_code = "pass"
        self.assertEqual(identify_semantic_changes(old_code, new_code), ["Class Removed: OldClass"])

    def test_class_renamed(self):
        """Test detection of a renamed class with an identical body."""
        old_code = "class OldClassName:\n    def method(self):\n        return 'hello'"
        new_code = "class NewClassName:\n    def method(self):\n        return 'hello'"
        self.assertEqual(identify_semantic_changes(old_code, new_code), ["Class Renamed: 'OldClassName' to 'NewClassName'"])

    def test_dependency_added(self):
        """Test detection of added dependencies."""
        old_code = "import os"
        new_code = "import os\nimport sys\nfrom collections import defaultdict"
        expected = ["Dependency Added: collections", "Dependency Added: sys"]
        self.assertEqual(identify_semantic_changes(old_code, new_code), expected)

    def test_dependency_removed(self):
        """Test detection of removed dependencies."""
        old_code = "import os\nimport sys"
        new_code = "import os"
        self.assertEqual(identify_semantic_changes(old_code, new_code), ["Dependency Removed: sys"])

    def test_multiple_changes(self):
        """Test a combination of various changes."""
        old_code = """
import os
class OldClass:
    def method(self): pass
def func_to_remove(): pass
def func_to_rename():
    print("hello")
"""
        new_code = """
import sys
from my_lib import a
class RenamedClass:
    def method(self): pass
def func_to_add(): return True
def func_renamed():
    print("hello")
"""
        expected = [
            'Dependency Added: my_lib',
            'Dependency Added: sys',
            'Dependency Removed: os',
            "Function Renamed: 'func_to_rename' to 'func_renamed'",
            'Function Added: func_to_add',
            'Function Removed: func_to_remove',
            "Class Renamed: 'OldClass' to 'RenamedClass'",
        ]
        self.assertEqual(identify_semantic_changes(old_code, new_code), expected)

    def test_syntax_error_handling(self):
        """Test that syntax errors are caught and reported."""
        old_code = "def valid_func(): pass"
        new_code = "def invalid_func() return"
        result = identify_semantic_changes(old_code, new_code)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith("Syntax error in code:"))

    def test_cosmetic_changes_are_ignored(self):
        """Test that changes in comments, whitespace, etc., are ignored."""
        old_code = "def my_func(a,b):\n    # This is a comment\n    return a+b"
        new_code = "# A different comment\ndef my_func( a, b ):\n    \n    return a + b"
        self.assertEqual(identify_semantic_changes(old_code, new_code), [])

    def test_empty_inputs(self):
        """Test behavior with empty code strings."""
        self.assertEqual(identify_semantic_changes("", ""), [])
        self.assertEqual(identify_semantic_changes("", "import os"), ["Dependency Added: os"])
        self.assertEqual(identify_semantic_changes("def f(): pass", ""), ["Function Removed: f"])

    def test_rename_fails_with_docstring_change(self):
        """Test that a rename is not detected if the docstring (part of body) changes."""
        old_code = "def old_func():\n    '''Old doc.'''\n    return 1"
        new_code = "def new_func():\n    '''New doc.'''\n    return 1"
        expected = ["Function Added: new_func", "Function Removed: old_func"]
        self.assertEqual(identify_semantic_changes(old_code, new_code), expected)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)