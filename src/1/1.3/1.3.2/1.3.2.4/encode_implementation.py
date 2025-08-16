import unittest
from unittest.mock import patch, AsyncMock
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- System Under Test (SUT) ---
# The following code (models, mock clients, and the `get_answer` function) is
# based on the provided context for sibling tasks to create a runnable test file.

# 1. Data Models
class SourceDocument(BaseModel):
    """Represents a source document (e.g., a commit) used for generating an answer."""
    page_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0

class AnswerResponse(BaseModel):
    """The final response object for the Q&A endpoint."""
    answer: str
    session_id: Optional[str] = None
    source_documents: List[SourceDocument] = Field(default_factory=list)

# 2. Mock Clients (placeholders for external services)
class MockEmbeddingProvider:
    """Placeholder for a sentence-transformer or OpenAI embedding model."""
    def encode(self, text: str) -> List[float]:
        return [len(text) / 100.0] * 128

class MockVectorDB:
    """Placeholder for a vector database client like ChromaDB or Pinecone."""
    def query(self, query_embeddings: List[List[float]], n_results: int) -> dict:
        return {
            'ids': [['commit_abc123', 'commit_def456']],
            'documents': [[
                "feat(api): add user profile endpoint\n\n- Implement GET /api/v1/users/me",
                "fix(db): correct indexing on commits table\n\n- The timestamp column was not indexed."
            ]],
            'metadatas': [[
                {'author': 'a@dev.com', 'hash': 'abc123...'},
                {'author': 'b@dev.com', 'hash': 'def456...'}
            ]],
            'distances': [[0.15, 0.32]]
        }

class MockLLM:
    """Placeholder for a Large Language Model client like OpenAI or Anthropic."""
    async def generate(self, prompt: str) -> str:
        return f"Generated answer based on prompt: {prompt[:50]}..."

# 3. Global Client Instances (to be patched in tests)
embedding_model = MockEmbeddingProvider()
vector_db_collection = MockVectorDB()
llm_client = MockLLM()

# 4. The Core Logic Function to be Tested
async def get_answer(query: str, session_id: Optional[str] = None, context: Optional[str] = None) -> 'AnswerResponse':
    """
    Performs a full RAG pipeline:
    1.  Retrieval: Embeds the query and fetches relevant documents (commits).
    2.  Generation: Constructs a prompt with the retrieved documents and generates
        an answer using a Language Model.
    """
    # --- 1. Retrieval Step ---
    search_query = f"{context}\n{query}" if context else query
    query_embedding = embedding_model.encode(search_query)

    results = vector_db_collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    source_documents = []
    if results and results.get('ids') and results['ids'][0]:
        ids, documents, metadatas, distances = (
            results['ids'][0],
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )
        for i in range(len(ids)):
            source_documents.append(
                SourceDocument(
                    page_content=documents[i],
                    metadata=metadatas[i],
                    score=distances[i]
                )
            )

    # --- 2. Generation Step ---
    if not source_documents:
        final_answer = "I could not find any relevant information in the commit history to answer your question."
    else:
        context_str = "\n\n---\n\n".join([doc.page_content for doc in source_documents])
        prompt_template = """
Use the following context from commit history to answer the question at the end.
The context contains excerpts from git commits.
If you don't know the answer, just say that you don't know. Do not try to make up an answer.

Context:
{context}

Question: {question}

Helpful Answer:"""
        prompt = prompt_template.format(context=context_str, question=query)
        final_answer = await llm_client.generate(prompt)

    # --- 3. Construct and return the final response ---
    return AnswerResponse(
        answer=final_answer,
        session_id=session_id,
        source_documents=source_documents
    )


# --- Unit Tests ---

class TestRetrievalAndGenerationLogic(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the get_answer RAG pipeline."""

    @patch(__name__ + '.llm_client', new_callable=AsyncMock)
    @patch(__name__ + '.vector_db_collection')
    @patch(__name__ + '.embedding_model')
    async def test_successful_flow(self, mock_embed, mock_vdb, mock_llm):
        """
        Tests the complete, successful RAG flow from query to answer.
        """
        # Arrange: Configure mocks for a successful path
        mock_embed.encode.return_value = [0.1] * 128
        mock_vdb.query.return_value = {
            'ids': [['commit_123']],
            'documents': [['feat: implement new auth flow']],
            'metadatas': [[{'author': 'test@dev.com'}]],
            'distances': [[0.15]]
        }
        mock_llm.generate.return_value = "The new authentication flow has been implemented."

        # Act: Call the function under test
        query = "What's new with authentication?"
        session_id = "session-abc-123"
        response = await get_answer(query=query, session_id=session_id)

        # Assert: Verify the results
        self.assertIsInstance(response, AnswerResponse)
        self.assertEqual(response.answer, "The new authentication flow has been implemented.")
        self.assertEqual(response.session_id, session_id)
        self.assertEqual(len(response.source_documents), 1)
        self.assertEqual(response.source_documents[0].page_content, "feat: implement new auth flow")

        mock_embed.encode.assert_called_once_with(query)
        mock_vdb.query.assert_called_once()
        mock_llm.generate.assert_called_once()

    @patch(__name__ + '.llm_client', new_callable=AsyncMock)
    @patch(__name__ + '.vector_db_collection')
    @patch(__name__ + '.embedding_model')
    async def test_no_documents_found(self, mock_embed, mock_vdb, mock_llm):
        """
        Tests the behavior when the vector DB returns no relevant documents.
        """
        # Arrange: Configure vector DB to return empty results
        mock_embed.encode.return_value = [0.2] * 128
        mock_vdb.query.return_value = {
            'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]
        }

        # Act: Call the function
        response = await get_answer(query="any info on project X?")

        # Assert: Verify the predefined "not found" message and that LLM was not called
        self.assertEqual(
            response.answer,
            "I could not find any relevant information in the commit history to answer your question."
        )
        self.assertEqual(len(response.source_documents), 0)
        mock_llm.generate.assert_not_called()

    @patch(__name__ + '.llm_client', new_callable=AsyncMock)
    @patch(__name__ + '.vector_db_collection')
    @patch(__name__ + '.embedding_model')
    async def test_prompt_construction(self, mock_embed, mock_vdb, mock_llm):
        """
        Tests that the prompt sent to the LLM is formatted correctly.
        """
        # Arrange: Provide specific documents to check formatting
        doc1_content = "fix(login): resolve password reset bug"
        doc2_content = "feat(ui): add dark mode toggle"
        mock_embed.encode.return_value = [0.3] * 128
        mock_vdb.query.return_value = {
            'ids': [['c1', 'c2']],
            'documents': [[doc1_content, doc2_content]],
            'metadatas': [[{}, {}]],
            'distances': [[0.2, 0.3]]
        }
        query = "summarize recent UI and login changes"

        # Act: Call the function
        await get_answer(query=query)

        # Assert: Check the structure and content of the prompt passed to the LLM
        mock_llm.generate.assert_called_once()
        prompt_arg = mock_llm.generate.call_args.args[0]

        expected_context = f"{doc1_content}\n\n---\n\n{doc2_content}"
        self.assertIn(f"Context:\n{expected_context}", prompt_arg)
        self.assertIn(f"Question: {query}", prompt_arg)
        self.assertTrue(prompt_arg.strip().endswith("Helpful Answer:"))

    @patch(__name__ + '.embedding_model')
    async def test_search_query_uses_context(self, mock_embed):
        """
        Tests that conversational context is prepended to the user query
        before being sent to the embedding model.
        """
        # Arrange: We only need to check the call to the embedding model
        # We can use the default empty return from other mocks
        with patch(__name__ + '.vector_db_collection'), patch(__name__ + '.llm_client'):
            query = "what about the API?"
            context = "We were discussing backend changes."
            expected_search_query = f"{context}\n{query}"

            # Act: Call the function with context
            await get_answer(query=query, context=context)

            # Assert: Verify the argument passed to the embedding model
            mock_embed.encode.assert_called_once_with(expected_search_query)