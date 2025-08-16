import unittest
import git
import ast
from radon.visitors import ComplexityVisitor
import os
import shutil
import tempfile

# The implementation to test is included here for a self-contained unit test file.
def calculate_file_complexity_at_commit(repo_path, file_path, commit_hash):
    """
    Calculates the cyclomatic complexity of a Python file at a specific git commit.

    Args:
        repo_path (str): The file system path to the git repository.
        file_path (str): The relative path to the file within the repository.
        commit_hash (str): The hash of the commit to inspect.

    Returns:
        int: The total cyclomatic complexity of the file, or 0 if the file
             cannot be found, is not a valid Python file, or an error occurs.
    """
    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
        commit = repo.commit(commit_hash)
        
        # Retrieve the file's content (blob) from the specified commit
        blob = commit.tree / file_path
        file_content = blob.data_stream.read().decode('utf-8')

        # Parse the code into an Abstract Syntax Tree (AST)
        tree = ast.parse(file_content)
        
        # Use Radon to visit the AST and calculate complexity
        visitor = ComplexityVisitor.from_ast(tree)
        
        # Sum the complexity of all functions/methods in the file
        total_complexity = sum(block.complexity for block in visitor.blocks)
        
        return total_complexity

    except (git.exc.BadName, KeyError, SyntaxError, ValueError, IsADirectoryError):
        # Handle common errors gracefully:
        # - git.exc.BadName: Invalid commit hash.
        # - KeyError: File not found in the commit's tree.
        # - SyntaxError: The file content is not valid Python code.
        # - ValueError: Decoding error.
        # - IsADirectoryError: The path points to a directory.
        return 0

class TestCalculateFileComplexityAtCommit(unittest.TestCase):

    def setUp(self):
        """Set up a temporary git repository with a few commits for testing."""
        self.repo_path = tempfile.mkdtemp()
        self.repo = git.Repo.init(self.repo_path)
        self.repo.config_writer().set_value("user", "name", "Test User").release()
        self.repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Commit 1: A simple Python file
        self.simple_file_path = "simple.py"
        simple_content = "def my_func(x):\n    if x > 10:\n        return True\n    return False"
        with open(os.path.join(self.repo_path, self.simple_file_path), "w") as f:
            f.write(simple_content)
        self.repo.index.add([self.simple_file_path])
        self.commit1_hash = self.repo.index.commit("Add simple file").hexsha

        # Commit 2: A more complex file and a non-python file
        self.complex_file_path = "complex.py"
        complex_content = (
            "def func_one(a, b):\n"
            "    if a and b:\n"         # +2
            "        return 1\n"
            "    elif a or b:\n"       # +2
            "        return 2\n"
            "    return 0\n"           # Base is 1. Total = 1+2+2 = 5
            "\n"
            "class MyClass:\n"
            "    def method(self, items):\n"
            "        for item in items:\n"  # +1
            "            print(item)\n"   # Base is 1. Total = 2
        )
        with open(os.path.join(self.repo_path, self.complex_file_path), "w") as f:
            f.write(complex_content)
        self.repo.index.add([self.complex_file_path])
        self.commit2_hash = self.repo.index.commit("Add complex file").hexsha

        # Commit 3: A file with a syntax error
        self.syntax_error_file_path = "broken.py"
        syntax_error_content = "def bad_syntax(:\n    pass"
        with open(os.path.join(self.repo_path, self.syntax_error_file_path), "w") as f:
            f.write(syntax_error_content)
        self.repo.index.add([self.syntax_error_file_path])
        self.commit3_hash = self.repo.index.commit("Add file with syntax error").hexsha

        # Commit 4: Add a directory
        self.dir_path = "src"
        os.makedirs(os.path.join(self.repo_path, self.dir_path))
        with open(os.path.join(self.repo_path, self.dir_path, ".gitkeep"), "w") as f:
            f.write("")
        self.repo.index.add([os.path.join(self.dir_path, ".gitkeep")])
        self.commit4_hash = self.repo.index.commit("Add a directory").hexsha


    def tearDown(self):
        """Remove the temporary repository."""
        shutil.rmtree(self.repo_path)

    def test_correct_complexity_simple_file(self):
        """Test complexity calculation for a simple file with one 'if' statement."""
        # 'if' adds 1, base complexity is 1. Total = 2.
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, self.simple_file_path, self.commit1_hash
        )
        self.assertEqual(complexity, 2)

    def test_correct_complexity_complex_file(self):
        """Test complexity calculation for a more complex file."""
        # func_one is 5, MyClass.method is 2. Total = 7.
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, self.complex_file_path, self.commit2_hash
        )
        self.assertEqual(complexity, 7)

    def test_file_not_found_in_commit(self):
        """Test requesting a file that does not exist in the specified commit."""
        # complex.py was added in commit 2, so it's not in commit 1.
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, self.complex_file_path, self.commit1_hash
        )
        self.assertEqual(complexity, 0)

    def test_file_not_in_repo_at_all(self):
        """Test requesting a file that was never in the repository."""
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, "non_existent_file.py", self.commit2_hash
        )
        self.assertEqual(complexity, 0)

    def test_invalid_commit_hash(self):
        """Test using an invalid or non-existent commit hash."""
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, self.simple_file_path, "invalid_hash_12345"
        )
        self.assertEqual(complexity, 0)

    def test_file_with_syntax_error(self):
        """Test a file that contains invalid Python syntax."""
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, self.syntax_error_file_path, self.commit3_hash
        )
        self.assertEqual(complexity, 0)

    def test_path_is_a_directory(self):
        """Test providing a path to a directory instead of a file."""
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, self.dir_path, self.commit4_hash
        )
        self.assertEqual(complexity, 0)

    def test_empty_file(self):
        """Test an empty file, which should have zero complexity."""
        empty_file_path = "empty.py"
        with open(os.path.join(self.repo_path, empty_file_path), "w") as f:
            f.write("")
        self.repo.index.add([empty_file_path])
        commit_hash = self.repo.index.commit("Add empty file").hexsha
        
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, empty_file_path, commit_hash
        )
        self.assertEqual(complexity, 0)

    def test_file_with_no_functions(self):
        """Test a file with no functions or methods, which should have zero complexity."""
        no_func_file_path = "no_func.py"
        content = "a = 1\nb = a + 5\nprint(b)"
        with open(os.path.join(self.repo_path, no_func_file_path), "w") as f:
            f.write(content)
        self.repo.index.add([no_func_file_path])
        commit_hash = self.repo.index.commit("Add file with no functions").hexsha
        
        complexity = calculate_file_complexity_at_commit(
            self.repo_path, no_func_file_path, commit_hash
        )
        self.assertEqual(complexity, 0)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)