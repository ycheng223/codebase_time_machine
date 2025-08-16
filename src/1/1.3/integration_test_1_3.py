import unittest
import os
import ast
import json
import shutil
import tempfile
from typing import Optional, List, Dict, Any

# Assume these components are in modules and are imported.
# For this self-contained test, they are defined directly.

# --- Component 1: AST Generation (from 1.3.1/1.3.1.2) ---

def generate_ast_from_code_blob(code_blob: str) -> Optional[ast.Module]:
    """
    Parses a string of Python code and returns its AST Module.
    Returns None if the code contains a syntax error.
    """
    try:
        return ast.parse(code_blob)
    except SyntaxError:
        return None

# --- Component 2: Code Structure Extraction (from 1.3.2/1.3.2.2) ---

class _CodeStructureVisitor(ast.NodeVisitor):
    """
    An AST visitor that extracts a simplified structure of the code,
    including classes, functions, and their docstrings.
    """
    def __init__(self):
        self.structure: List[Dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.structure.append({
            'type': 'function',
            'name': node.name,
            'docstring': ast.get_docstring(node) or "",
            'start_line': node.lineno,
            'end_line': node.end_lineno
        })
        # Do not visit children of functions to avoid capturing nested functions
        # in this simplified representation.

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.structure.append({
            'type': 'function',
            'name': node.name,
            'docstring': ast.get_docstring(node) or "",
            'start_line': node.lineno,
            'end_line': node.end_lineno
        })

    def visit_ClassDef(self, node: ast.ClassDef):
        self.structure.append({
            'type': 'class',
            'name': node.name,
            'docstring': ast.get_docstring(node) or "",
            'start_line': node.lineno,
            'end_line': node.end_lineno
        })
        # Visit methods inside the class
        self.generic_visit(node)

# --- Component 3: Embedding Generation (from 1.3.3/1.3.3.2) ---
# Note: This requires `sentence-transformers` and `numpy` to be installed.
# It will also download a model on first run, which may take time.

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    # It is efficient to load the model once. Use a small, fast model for testing.
    _model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=tempfile.gettempdir())
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    _SENTENTCE_TRANSFORMERS_AVAILABLE = False
    # Create dummy objects if library is not available to allow test discovery
    np = None
    SentenceTransformer = None
    _model = None

def generate_embeddings(texts: List[str]) -> np.ndarray:
    """
    Generates sentence embeddings for a list of text strings.
    """
    if not _SENTENCE_TRANSFORMERS_AVAILABLE:
        raise unittest.SkipTest("sentence-transformers or numpy not installed, skipping embedding tests.")
    return _model.encode(texts)


# --- Component 4: Storage (from 1.3.3/1.3.3.3) ---

def store_embeddings_with_metadata(
    embeddings: np.ndarray,
    metadata: List[Dict[str, Any]],
    output_path: str,
    base_filename: str
):
    """
    Stores embeddings and their corresponding metadata to files.
    - Embeddings are saved in a .npy file.
    - Metadata is saved in a .json file.
    """
    if not _SENTENCE_TRANSFORMERS_AVAILABLE:
        # This check prevents errors in a minimal test environment
        return

    os.makedirs(output_path, exist_ok=True)
    embedding_file = os.path.join(output_path, f"{base_filename}.npy")
    metadata_file = os.path.join(output_path, f"{base_filename}.json")
    np.save(embedding_file, embeddings)
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)


# --- Integration Test Class ---

class TestSemanticCodeAnalysisIntegration(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and sample code for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.sample_code = """
import sys

class CodeAnalyzer:
    \"\"\"This class analyzes Python code files.\"\"\"

    def __init__(self, file_path: str):
        # This is a constructor without a docstring.
        self.file_path = file_path

    def get_line_count(self) -> int:
        \"\"\"Counts the number of lines in the file.\"\"\"
        with open(self.file_path, 'r') as f:
            return len(f.readlines())

def utility_function(text: str):
    \"\"\"A standalone utility function.\"\"\"
    print(text)

def function_with_no_docstring():
    pass
"""
        self.invalid_code = "def invalid_syntax("

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_full_pipeline_integration(self):
        """
        Tests the end-to-end pipeline: code -> AST -> structure -> embeddings -> storage.
        """
        # 1. Generate AST from a valid code blob
        code_ast = generate_ast_from_code_blob(self.sample_code)
        self.assertIsNotNone(code_ast, "AST generation should succeed for valid code.")
        self.assertIsInstance(code_ast, ast.Module)

        # 2. Extract code structure using the AST visitor
        visitor = _CodeStructureVisitor()
        visitor.visit(code_ast)
        extracted_structure = visitor.structure

        # Verify the number and names of extracted elements (order is fixed by AST traversal)
        self.assertEqual(len(extracted_structure), 5)
        expected_names = ['CodeAnalyzer', '__init__', 'get_line_count', 'utility_function', 'function_with_no_docstring']
        actual_names = [item['name'] for item in extracted_structure]
        self.assertListEqual(actual_names, expected_names)

        # 3. Filter for items with docstrings to be embedded
        metadata_to_embed = [item for item in extracted_structure if item['docstring']]
        docstrings_to_embed = [item['docstring'] for item in metadata_to_embed]

        self.assertEqual(len(metadata_to_embed), 3)
        self.assertEqual(metadata_to_embed[0]['name'], 'CodeAnalyzer')
        self.assertEqual(metadata_to_embed[1]['name'], 'get_line_count')
        self.assertEqual(metadata_to_embed[2]['name'], 'utility_function')

        # 4. Generate embeddings for the docstrings
        embeddings = generate_embeddings(docstrings_to_embed)

        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape[0], len(docstrings_to_embed), "Should have one embedding vector per docstring.")
        self.assertEqual(embeddings.shape[1], 384, "Embedding dimension for 'all-MiniLM-L6-v2' should be 384.")

        # 5. Store embeddings and metadata
        base_filename = "code_analysis_output"
        store_embeddings_with_metadata(embeddings, metadata_to_embed, self.test_dir, base_filename)

        # 6. Verify that the files were created correctly
        expected_npy_path = os.path.join(self.test_dir, f"{base_filename}.npy")
        expected_json_path = os.path.join(self.test_dir, f"{base_filename}.json")

        self.assertTrue(os.path.exists(expected_npy_path), "Embeddings .npy file should be created.")
        self.assertTrue(os.path.exists(expected_json_path), "Metadata .json file should be created.")

        # 7. Load the stored data and verify its contents
        loaded_embeddings = np.load(expected_npy_path)
        with open(expected_json_path, 'r') as f:
            loaded_metadata = json.load(f)

        # Compare the loaded data with the original data
        np.testing.assert_allclose(
            loaded_embeddings,
            embeddings,
            err_msg="Stored embeddings should match generated embeddings."
        )
        self.assertListEqual(
            loaded_metadata,
            metadata_to_embed,
            "Stored metadata should match the original metadata."
        )

    def test_ast_generation_failure(self):
        """
        Tests that the AST generation component correctly handles syntax errors.
        """
        code_ast = generate_ast_from_code_blob(self.invalid_code)
        self.assertIsNone(code_ast, "AST generation should return None for code with syntax errors.")

    def test_pipeline_with_no_docstrings(self):
        """
        Tests the pipeline with code that contains no docstrings.
        """
        code_with_no_docs = "def my_func(a, b):\n    return a + b\n\nclass MyClass:\n    pass"

        # 1. Parse and visit
        code_ast = generate_ast_from_code_blob(code_with_no_docs)
        self.assertIsNotNone(code_ast)
        visitor = _CodeStructureVisitor()
        visitor.visit(code_ast)
        extracted_structure = visitor.structure

        # 2. Filter for items with docstrings
        metadata_to_embed = [item for item in extracted_structure if item['docstring']]
        docstrings_to_embed = [item['docstring'] for item in metadata_to_embed]

        self.assertEqual(len(metadata_to_embed), 0, "Should find no metadata to embed.")
        self.assertEqual(len(docstrings_to_embed), 0, "Should find no docstrings to embed.")

        # 3. Generate embeddings (should be an empty array)
        embeddings = generate_embeddings(docstrings_to_embed)
        self.assertEqual(embeddings.shape, (0,), "Embedding an empty list should result in an empty array.")

        # 4. Store and verify
        base_filename = "no_docs_output"
        store_embeddings_with_metadata(embeddings, metadata_to_embed, self.test_dir, base_filename)
        expected_npy_path = os.path.join(self.test_dir, f"{base_filename}.npy")
        expected_json_path = os.path.join(self.test_dir, f"{base_filename}.json")
        self.assertTrue(os.path.exists(expected_npy_path))
        self.assertTrue(os.path.exists(expected_json_path))

        loaded_embeddings = np.load(expected_npy_path)
        self.assertEqual(loaded_embeddings.shape, (0,))
        with open(expected_json_path, 'r') as f:
            loaded_metadata = json.load(f)
        self.assertEqual(loaded_metadata, [])


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)