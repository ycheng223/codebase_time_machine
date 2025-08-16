import ast
from typing import Optional

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