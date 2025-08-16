import unittest
import ast

# The implementation to be tested
class _CodeStructureVisitor(ast.NodeVisitor):
    """
    An AST visitor that extracts a structured representation of classes,
    methods, and functions from a Python code string.
    """
    def __init__(self):
        self.structure = {"_GLOBAL_": {}}
        self._current_class_name = None

    def visit_ClassDef(self, node):
        self._current_class_name = node.name
        self.structure[node.name] = {}
        self.generic_visit(node)
        self._current_class_name = None

    def _process_function(self, node):
        params = [arg.arg for arg in node.args.args]
        signature = {"params": params, "lineno": node.lineno}

        if self._current_class_name:
            self.structure[self._current_class_name][node.name] = signature
        else:
            self.structure["_GLOBAL_"][node.name] = signature

    def visit_FunctionDef(self, node):
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._process_function(node)
        self.generic_visit(node)

# The test class for the __init__ method
class TestCodeStructureVisitorInit(unittest.TestCase):

    def test_initialization(self):
        """
        Tests the __init__ method of _CodeStructureVisitor to ensure
        the instance is initialized with the correct default attributes.
        """
        # Create an instance of the visitor
        visitor = _CodeStructureVisitor()

        # 1. Test the 'structure' attribute
        # It should be a dictionary with a single key "_GLOBAL_"
        # which maps to an empty dictionary.
        expected_structure = {"_GLOBAL_": {}}
        self.assertIsInstance(visitor.structure, dict, "structure attribute should be a dictionary")
        self.assertEqual(visitor.structure, expected_structure, "structure attribute not initialized correctly")

        # 2. Test the '_current_class_name' attribute
        # It should be initialized to None.
        self.assertIsNone(visitor._current_class_name, "_current_class_name attribute should be None")