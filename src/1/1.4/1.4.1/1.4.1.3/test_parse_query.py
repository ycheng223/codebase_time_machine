import unittest
import sys
import os

# Add the path to the function to be tested
# This assumes the function is in a file in the same directory or a known path
# For this example, we'll define the function directly to ensure it's available.

from typing import Any, Dict, Optional
import re

def parse_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parses a natural language query to extract intent, keywords, and entities.

    Args:
        query: The natural language query string.
        context: Optional dictionary for providing context (not used in this implementation).

    Returns:
        A dictionary containing the parsed components:
        - 'intent': The determined user intent (e.g., 'evolution', 'pattern', 'auth').
        - 'keywords': A list of significant words from the query.
        - 'entities': A dictionary of identified entities (e.g., terms in quotes).
        - 'original_query': The original query string.
    """
    # --- 1. Define Rules & Knowledge Base ---

    # Define intents and their associated trigger words as sets for efficient lookup
    INTENT_TRIGGERS = {
        'evolution': {'evolution', 'history', 'changes', 'log', 'commit'},
        'pattern': {'pattern', 'find', 'search', 'grep', 'match', 'regex'},
        'auth': {'auth', 'authentication', 'login', 'user', 'whoami', 'access'}
    }

    # Define common stop words to be ignored during keyword extraction
    STOP_WORDS = {
        'a', 'an', 'the', 'is', 'in', 'on', 'for', 'with', 'show', 'me', 'what',
        'of', 'tell', 'about', 'give', 'list', 'i', 'to', 'and', 'my'
    }

    # --- 2. Initialization ---

    result = {
        'intent': 'unknown',  # Default intent if no triggers are found
        'keywords': [],
        'entities': {},
        'original_query': query
    }

    lower_query = query.lower()
    # Tokenize the query, preserving quoted phrases and words with special chars like '.' or '-'
    tokens = set(re.findall(r'[\w\.-]+|"[^"]*"', lower_query))

    # --- 3. Intent Recognition ---

    detected_intent_triggers = set()
    # Simple "first match wins" intent recognition logic
    for intent, triggers in INTENT_TRIGGERS.items():
        if not triggers.isdisjoint(tokens):
            result['intent'] = intent
            detected_intent_triggers = triggers
            break

    # --- 4. Entity Extraction ---

    # A simple entity recognizer for terms enclosed in double quotes
    quoted_phrases = re.findall(r'"(.*?)"', query)
    if quoted_phrases:
        result['entities']['term'] = quoted_phrases

    # --- 5. Keyword Extraction ---

    # Identify tokens that are part of extracted entities
    entity_tokens = set()
    for phrase in quoted_phrases:
        entity_tokens.update(phrase.lower().split())

    keywords = []
    # Re-iterate through original token order for keyword list
    for token in re.findall(r'[\w\.-]+|"[^"]*"', lower_query):
        # Clean token by removing quotes for individual checks
        clean_token = token.strip('"')

        # Add to keywords if it's not a stop word, an intent trigger, or part of an entity
        if (clean_token and
                clean_token not in STOP_WORDS and
                clean_token not in detected_intent_triggers and
                clean_token not in entity_tokens):
            keywords.append(clean_token)

    # Remove duplicates while preserving the order
    result['keywords'] = list(dict.fromkeys(keywords))

    return result


class TestParseQuery(unittest.TestCase):

    def test_simple_evolution_intent(self):
        query = "show me the commit history of main.py"
        expected = {
            'intent': 'evolution',
            'keywords': ['main.py'],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_simple_pattern_intent(self):
        query = "search for 'TODO' in the code"
        expected = {
            'intent': 'pattern',
            'keywords': ["'todo'", 'code'],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_simple_auth_intent(self):
        query = "tell me the user for this file"
        expected = {
            'intent': 'auth',
            'keywords': ['this', 'file'],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_unknown_intent(self):
        query = "what is the status of this system"
        expected = {
            'intent': 'unknown',
            'keywords': ['status', 'this', 'system'],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_intent_precedence(self):
        # 'commit'/'log' (evolution) should be detected before 'search' (pattern)
        query = "show the commit log and search for users"
        expected = {
            'intent': 'evolution',
            'keywords': ['search', 'users'],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_single_quoted_entity(self):
        query = "find all instances of \"MyClass.new\""
        expected = {
            'intent': 'pattern',
            'keywords': ['all', 'instances'],
            'entities': {'term': ['MyClass.new']},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_multiple_quoted_entities(self):
        query = "grep for \"foo bar\" and \"baz\""
        expected = {
            'intent': 'pattern',
            'keywords': [],
            'entities': {'term': ['foo bar', 'baz']},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_complex_query_with_all_components(self):
        query = "search for \"error message\" in file.log and also auth details"
        expected = {
            'intent': 'pattern',
            'keywords': ['file.log', 'also', 'auth', 'details'],
            'entities': {'term': ['error message']},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_empty_query(self):
        query = ""
        expected = {
            'intent': 'unknown',
            'keywords': [],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_query_with_only_stop_words(self):
        query = "show me a list of the"
        expected = {
            'intent': 'unknown',
            'keywords': [],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_mixed_case_query(self):
        query = "Show ME the LOG for main.py"
        expected = {
            'intent': 'evolution',
            'keywords': ['main.py'],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_keywords_with_special_chars(self):
        query = "find version-1.2.3 in my-file.log"
        expected = {
            'intent': 'pattern',
            'keywords': ['version-1.2.3', 'my-file.log'],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_keyword_order_and_uniqueness(self):
        query = "search file.txt for a pattern and search file.txt again"
        expected = {
            'intent': 'pattern',
            'keywords': ['file.txt', 'again'],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_query_with_only_entity(self):
        query = "\"a quoted term\""
        expected = {
            'intent': 'unknown',
            'keywords': [],
            'entities': {'term': ['a quoted term']},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

    def test_no_keywords_left(self):
        query = "show me the log"
        expected = {
            'intent': 'evolution',
            'keywords': [],
            'entities': {},
            'original_query': query
        }
        self.assertDictEqual(parse_query(query), expected)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)