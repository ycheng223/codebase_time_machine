import unittest
from unittest.mock import patch, MagicMock
import os
import openai
import re

# --- IMPLEMENTATIONS TO BE TESTED ---

# Subtask 1.4.3.2 Implementation
def get_llm_response(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Sends a prompt to the OpenAI API and returns the LLM's response.

    This function requires the 'openai' library to be installed and the
    OPENAI_API_KEY environment variable to be set.

    Args:
        prompt (str): The user's input/question for the LLM.
        model (str, optional): The model to use for the completion.
                               Defaults to "gpt-3.5-turbo".

    Returns:
        str: The text content of the LLM's response.

    Raises:
        ValueError: If the OPENAI_API_KEY environment variable is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    try:
        # Initialize the client with the API key
        client = openai.OpenAI(api_key=api_key)

        # Create the API request
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
        )

        # Extract and return the response content
        response_content = chat_completion.choices[0].message.content
        return response_content.strip() if response_content else ""

    except Exception as e:
        # Handle potential API errors or other exceptions
        print(f"An error occurred while communicating with the API: {e}")
        return "Error: Could not retrieve a response from the LLM."


# Components from Subtask 1.4.3.3 Context
class KnowledgeBase:
    """A simple in-memory document store."""
    def __init__(self):
        self.documents = {}

    def add_document(self, doc_id: str, text: str):
        self.documents[doc_id] = text

    def get_document(self, doc_id: str) -> str:
        return self.documents.get(doc_id)
    
    def get_all_documents(self):
        return self.documents.items()

    def clear(self):
        self.documents.clear()

class DocumentIngestor:
    """Handles adding documents to the knowledge base."""
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    def ingest(self, doc_id: str, text: str):
        if not doc_id or not text:
            raise ValueError("Document ID and text cannot be empty.")
        self.kb.add_document(doc_id, text)

class Retriever:
    """
    A simple keyword-based retriever.
    Finds documents that contain any of the words from the query.
    """
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        query_words = set(re.findall(r'\w+', query.lower()))
        if not query_words:
            return []

        scored_docs = []
        for doc_id, text in self.kb.get_all_documents():
            doc_words = set(re.findall(r'\w+', text.lower()))
            common_words = query_words.intersection(doc_words)
            if common_words:
                scored_docs.append((len(common_words), doc_id))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [doc_id for score, doc_id in scored_docs[:top_k]]

# --- NEW COMPONENT INTEGRATING THE LLM ---
# This class replaces the placeholder AnswerGenerator from the context
class LLMAnswerGenerator:
    """
    Generates an answer by creating a prompt from context and calling an LLM.
    """
    def generate(self, query: str, contexts: list[str]) -> str:
        """
        Synthesizes an answer by calling the get_llm_response function.
        """
        if not contexts:
            return "I'm sorry, I could not find any relevant information to answer your question."

        combined_context = "\n---\n".join(contexts)
        
        prompt = (
            "Based on the following context, please provide a concise answer to the user's question.\n\n"
            f"CONTEXT:\n{combined_context}\n\n"
            f"QUESTION:\n{query}\n\n"
            "ANSWER:"
        )
        
        # This is the integration point with the LLM client
        return get_llm_response(prompt)

class QASystem:
    """
    Orchestrates the end-to-end question-answering flow.
    """
    def __init__(self, retriever: Retriever, generator: LLMAnswerGenerator):
        self.retriever = retriever
        self.generator = generator
        self.kb = self.retriever.kb

    def ask(self, question: str) -> str:
        retrieved_doc_ids = self.retriever.retrieve(question)
        
        contexts = []
        for doc_id in retrieved_doc_ids:
            doc_text = self.kb.get_document(doc_id)
            if doc_text:
                contexts.append(doc_text)
        
        answer = self.generator.generate(question, contexts)
        return answer

# --- INTEGRATION TEST ---

class TestLLMIntegrationForAnswerSynthesis(unittest.TestCase):

    def setUp(self):
        """Set up the QA system and ingest documents before each test."""
        # Set a dummy API key to pass the initial check in get_llm_response
        self.original_api_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key-for-integration-test"

        self.kb = KnowledgeBase()
        ingestor = DocumentIngestor(self.kb)
        self.retriever = Retriever(self.kb)
        self.generator = LLMAnswerGenerator()
        self.qa_system = QASystem(self.retriever, self.generator)

        ingestor.ingest(
            doc_id="doc1",
            text="The first programmable computer was the Z1, created by Konrad Zuse in Germany."
        )
        ingestor.ingest(
            doc_id="doc2",
            text="Python is a popular programming language created by Guido van Rossum."
        )
        ingestor.ingest(
            doc_id="doc3",
            text="The Z1 computer was an electromechanical machine with limited programming capabilities."
        )

    def tearDown(self):
        """Clean up environment variables after each test."""
        if self.original_api_key is None:
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = self.original_api_key

    @patch('__main__.get_llm_response')
    def test_successful_end_to_end_synthesis(self, mock_get_llm_response):
        """
        Tests the full flow: retrieval -> prompt generation -> mocked LLM call -> answer.
        """
        # Configure the mock to return a predictable, synthesized answer
        mock_response = "The Z1, created by Konrad Zuse, was the first programmable computer."
        mock_get_llm_response.return_value = mock_response

        question = "Who created the first programmable computer?"
        answer = self.qa_system.ask(question)

        # 1. Verify the LLM function was called
        mock_get_llm_response.assert_called_once()
        
        # 2. Verify the prompt passed to the LLM contains the right information
        call_args, _ = mock_get_llm_response.call_args
        prompt_arg = call_args[0]
        
        self.assertIn("QUESTION:\nWho created the first programmable computer?", prompt_arg)
        # Check that context from both relevant documents is included
        self.assertIn("Konrad Zuse in Germany", prompt_arg) # from doc1
        self.assertIn("electromechanical machine", prompt_arg) # from doc3
        # Check that irrelevant context is excluded
        self.assertNotIn("Python", prompt_arg)

        # 3. Verify the final answer is the one returned by the mocked LLM
        self.assertEqual(answer, mock_response)

    @patch('__main__.get_llm_response')
    def test_no_relevant_documents_retrieved(self, mock_get_llm_response):
        """
        Tests that if the retriever finds no documents, the LLM is not called.
        """
        question = "What is the capital of Argentina?"
        answer = self.qa_system.ask(question)

        # Verify that the system provides a default response without calling the LLM
        mock_get_llm_response.assert_not_called()
        self.assertEqual(answer, "I'm sorry, I could not find any relevant information to answer your question.")

    def test_system_raises_error_if_api_key_is_missing(self):
        """
        Tests that the system correctly propagates the ValueError from get_llm_response
        if the OPENAI_API_KEY is not set.
        """
        # Unset the key for this specific test
        del os.environ["OPENAI_API_KEY"]
        
        question = "Tell me about the Z1 computer."
        
        # The retriever will find documents, so the generator will call get_llm_response,
        # which should then raise the error.
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY environment variable not set."):
            self.qa_system.ask(question)

    @patch('__main__.get_llm_response')
    def test_system_handles_llm_api_failure(self, mock_get_llm_response):
        """
        Tests how the system behaves when get_llm_response returns its error message.
        """
        # Configure the mock to simulate an API failure
        error_message = "Error: Could not retrieve a response from the LLM."
        mock_get_llm_response.return_value = error_message

        question = "Who created Python?"
        answer = self.qa_system.ask(question)

        # Verify the LLM function was called
        mock_get_llm_response.assert_called_once()
        
        # Verify the prompt was constructed correctly
        prompt_arg = mock_get_llm_response.call_args[0][0]
        self.assertIn("Guido van Rossum", prompt_arg)

        # Verify the final answer is the error message from the LLM client
        self.assertEqual(answer, error_message)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)