import ast

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

def _get_code_structure(code_string):
    """
    Parses a string of Python code and returns its structure.
    Returns None if the code has a syntax error.
    """
    try:
        tree = ast.parse(code_string)
        visitor = _CodeStructureVisitor()
        visitor.visit(tree)
        return visitor.structure
    except SyntaxError:
        return None

def identify_semantic_changes(code_before, code_after):
    """
    Identifies semantic changes between two Python code snippets.

    This function parses two versions of Python code into Abstract Syntax Trees
    (ASTs) and compares their structures to identify changes such as added,
    removed, or modified classes, methods, and functions. A change in a
    function or method's signature is detected by comparing its parameter list.
    Class and function renames are reported as a removal and an addition.

    Args:
        code_before (str): The original source code string.
        code_after (str): The modified source code string.

    Returns:
        list[str]: A list of human-readable strings describing the detected
                   semantic changes. Returns an error message if parsing fails.
    """
    changes = []
    
    struct_before = _get_code_structure(code_before)
    struct_after = _get_code_structure(code_after)

    if struct_before is None or struct_after is None:
        return ["Error: Could not parse one or both code snippets due to a syntax error."]

    # Compare Classes
    before_classes = set(struct_before.keys()) - {"_GLOBAL_"}
    after_classes = set(struct_after.keys()) - {"_GLOBAL_"}

    for class_name in sorted(before_classes - after_classes):
        changes.append(f"REMOVED: Class '{class_name}' was removed.")
        
    for class_name in sorted(after_classes - before_classes):
        changes.append(f"ADDED: Class '{class_name}' was added.")
        
    # Compare Methods in common classes
    for class_name in sorted(before_classes & after_classes):
        before_methods = set(struct_before[class_name].keys())
        after_methods = set(struct_after[class_name].keys())

        for method_name in sorted(before_methods - after_methods):
            changes.append(f"REMOVED: Method '{method_name}' from class '{class_name}' was removed.")
            
        for method_name in sorted(after_methods - before_methods):
            changes.append(f"ADDED: Method '{method_name}' to class '{class_name}' was added.")
            
        for method_name in sorted(before_methods & after_methods):
            sig_before = struct_before[class_name][method_name]["params"]
            sig_after = struct_after[class_name][method_name]["params"]
            if sig_before != sig_after:
                changes.append(
                    f"MODIFIED: Signature of method '{method_name}' in class '{class_name}' changed from {sig_before} to {sig_after}."
                )

    # Compare Global Functions
    before_globals = set(struct_before["_GLOBAL_"].keys())
    after_globals = set(struct_after["_GLOBAL_"].keys())

    for func_name in sorted(before_globals - after_globals):
        changes.append(f"REMOVED: Global function '{func_name}' was removed.")
        
    for func_name in sorted(after_globals - before_globals):
        changes.append(f"ADDED: Global function '{func_name}' was added.")
        
    for func_name in sorted(before_globals & after_globals):
        sig_before = struct_before["_GLOBAL_"][func_name]["params"]
        sig_after = struct_after["_GLOBAL_"][func_name]["params"]
        if sig_before != sig_after:
            changes.append(
                f"MODIFIED: Signature of global function '{func_name}' changed from {sig_before} to {sig_after}."
            )
            
    return changes