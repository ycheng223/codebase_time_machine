import unittest
import ast
import re

# Implementation from Subtask 1.2.2.2: Semantic Diffing Module
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


class TestSemanticDiffIntegration(unittest.TestCase):
    """
    Integration tests for the semantic diffing module.
    These tests simulate realistic, complex code changes involving multiple
    semantic modifications at once, verifying that the `identify_semantic_changes`
    function correctly identifies the complete set of changes.
    """

    def test_major_refactoring_scenario(self):
        """
        Tests a realistic refactoring scenario including additions, removals,
        renames for both functions and classes, and dependency changes.
        """
        old_code = """
import os
import re

class UserData:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def display(self):
        return f"{self.name} <{self.email}>"

def get_user(user_id):
    # Imagine fetching from a DB
    return UserData("Test User", "test@example.com")

def update_user_data(user):
    print("Updating user...")
    user.name = user.name.upper()

def _legacy_connect():
    # Deprecated
    pass
"""
        new_code = """
import os
from typing import List

class UserProfile: # Renamed from UserData
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def display(self):
        return f"{self.name} <{self.email}>"

class Settings: # New class
    def __init__(self):
        self.theme = "dark"

def _validate_email(email): # New helper function
    return "@" in email

def fetch_user_by_id(user_id): # Renamed from get_user
    # Imagine fetching from a DB
    return UserProfile("Test User", "test@example.com")

def update_user_data(user): # Body changed, should not be detected
    print("Now updating user in a new way...")
    user.name = user.name.title()
"""

        expected_changes = [
            "Dependency Added: typing",
            "Dependency Removed: re",
            "Function Added: _validate_email",
            "Function Removed: _legacy_connect",
            "Function Renamed: 'get_user' to 'fetch_user_by_id'",
            "Class Added: Settings",
            "Class Renamed: 'UserData' to 'UserProfile'",
        ]
        
        actual_changes = identify_semantic_changes(old_code, new_code)
        self.assertCountEqual(actual_changes, expected_changes)

    def test_code_cleanup_and_reorganization(self):
        """
        Tests a scenario where code is moved, comments are changed, and unused
        elements are removed. The diff should only report the removals.
        """
        old_code = """
# This module handles calculations
import math

def calculate_area(radius):
    \"\"\"Calculate the area of a circle.\"\"\"
    return math.pi * radius ** 2

class UnusedShape:
    def __init__(self):
        self.sides = 0

def calculate_circumference(radius):
    # A function to get circumference
    return 2 * math.pi * radius
"""
        new_code = """
# Module for geometry calculations
import math

def calculate_circumference(radius):
    \"\"\"
    Calculate the circumference of a circle given its radius.
    \"\"\"
    return 2 * math.pi * radius

def calculate_area(radius): # Moved and docstring changed
    \"\"\"Calculate the area of a circle.\"\"\"
    return math.pi * radius ** 2
"""
        
        expected_changes = [
            "Class Removed: UnusedShape",
        ]

        # The body of `calculate_circumference` has a changed docstring and comment
        # which is part of the AST body. The implementation does not detect this,
        # which is the expected behavior based on its design. Re-ordering of
        # functions should also be ignored.
        actual_changes = identify_semantic_changes(old_code, new_code)
        self.assertCountEqual(actual_changes, expected_changes)

    def test_multiple_renames_and_additions(self):
        """
        Tests the rename detection logic when multiple functions are renamed,
        and new functions are added simultaneously.
        """
        old_code = """
def process_data():
    # Does complex thing A
    return 1

def calculate_stats():
    # Does complex thing B
    return [1, 2, 3]

def old_utility():
    pass
"""
        new_code = """
def run_processing(): # Renamed from process_data
    # Does complex thing A
    return 1

def generate_report(): # Renamed from calculate_stats
    # Does complex thing B
    return [1, 2, 3]

def new_feature(): # Added
    return True
"""
        expected_changes = [
            "Function Renamed: 'calculate_stats' to 'generate_report'",
            "Function Renamed: 'process_data' to 'run_processing'",
            "Function Added: new_feature",
            "Function Removed: old_utility",
        ]
        actual_changes = identify_semantic_changes(old_code, new_code)
        self.assertCountEqual(actual_changes, expected_changes)

    def test_no_semantic_change_with_reordering_and_formatting(self):
        """
        Verifies that reordering top-level definitions and changing whitespace
        or import order does not result in any detected changes.
        """
        old_code = """
import os
import sys

def func_a():
    return 1

class MyClass:
    pass

def func_b():
    return 2
"""
        new_code = """
import sys
import os # Order of imports changed

# Code has been re-ordered and whitespace added
def func_b():
    return 2

class MyClass:

    pass

def func_a():

    return 1
"""
        expected_changes = []
        actual_changes = identify_semantic_changes(old_code, new_code)
        self.assertCountEqual(actual_changes, expected_changes)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)