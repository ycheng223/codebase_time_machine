import unittest
import numpy as np

# Assuming the function to be tested is in the same file or imported.
# For this example, it's defined here for self-containment.
def retrieve_with_vector_and_filter(query_text, filters, dataset, vectorizer, top_k=3):
    """
    Retrieves items by first filtering on structured data and then performing
    a vector search on the filtered subset.

    This strategy is efficient as it reduces the search space for the costly
    vector similarity calculations.

    Args:
        query_text (str): The text query for vector search.
        filters (dict): A dictionary of key-value pairs for structured filtering.
                        e.g., {'category': 'electronics', 'year': 2023}
        dataset (list[dict]): A list of data items. Each item is a dictionary
                              containing metadata and a pre-computed 'vector' key
                              with a numpy array.
        vectorizer (function): A function that takes a text string and returns a
                               numpy array (vector embedding).
        top_k (int): The maximum number of relevant results to return.

    Returns:
        list[dict]: A list of the top_k matching items, sorted by relevance.
    """

    def _cosine_similarity(vec1, vec2):
        """Helper to calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        # Avoid division by zero
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        return dot_product / (norm_vec1 * norm_vec2)

    # Step 1: Apply structured filters to create a smaller candidate pool.
    # This uses a list comprehension for a concise filter operation.
    filtered_candidates = [
        item for item in dataset
        if all(item.get(key) == value for key, value in filters.items())
    ]

    # If no items match the metadata filter, return an empty list.
    if not filtered_candidates:
        return []

    # Step 2: Vectorize the input query text.
    query_vector = vectorizer(query_text)

    # Step 3: Perform vector search on the filtered candidates.
    # This calculates the similarity score for each remaining item.
    scored_results = [
        (_cosine_similarity(query_vector, item['vector']), item)
        for item in filtered_candidates if 'vector' in item
    ]

    # Step 4: Sort the results by similarity score in descending order.
    scored_results.sort(key=lambda x: x[0], reverse=True)

    # Step 5: Return the top_k items (without their scores).
    top_items = [item for score, item in scored_results[:top_k]]

    return top_items


class TestRetrieveWithVectorAndFilter(unittest.TestCase):

    def setUp(self):
        """Set up a mock dataset and vectorizer for all tests."""
        
        # A mock vectorizer that returns predefined vectors for specific queries
        self.mock_vectors = {
            "latest gaming laptops": np.array([1.0, 0.8, 0.2]),
            "ancient rome history": np.array([0.1, 0.2, 0.9]),
            "apple products": np.array([0.9, 0.9, 0.1]),
        }
        
        def mock_vectorizer(text):
            return self.mock_vectors.get(text, np.array([0.0, 0.0, 0.0]))
        
        self.vectorizer = mock_vectorizer

        # A sample dataset with pre-computed vectors and metadata
        self.dataset = [
            {
                'id': 1, 'product': 'Gaming Laptop X', 'category': 'electronics', 'year': 2023,
                'vector': np.array([0.9, 0.85, 0.15])  # High similarity to "laptops"
            },
            {
                'id': 2, 'product': 'Business Laptop Z', 'category': 'electronics', 'year': 2022,
                'vector': np.array([1.0, 0.7, 0.3])   # Highest similarity to "laptops"
            },
            {
                'id': 3, 'product': 'Book on Roman Empire', 'category': 'books', 'year': 1995,
                'vector': np.array([0.1, 0.1, 0.85])  # High similarity to "rome history"
            },
            {
                'id': 4, 'product': 'iPhone 15', 'category': 'electronics', 'year': 2023,
                'vector': np.array([0.8, 0.95, 0.1])  # High similarity to "apple products"
            },
            {
                'id': 5, 'product': 'Documentary on Rome', 'category': 'film', 'year': 2023,
                'vector': np.array([0.2, 0.3, 0.95])  # Highest similarity to "rome history"
            },
            {
                'id': 6, 'product': 'A filtered item without a vector key', 'category': 'electronics', 'year': 2023,
            }
        ]

    def test_basic_retrieval_with_single_filter(self):
        """Test retrieving items with a filter that yields multiple results."""
        query_text = "latest gaming laptops"
        filters = {'category': 'electronics'}
        
        results = retrieve_with_vector_and_filter(
            query_text, filters, self.dataset, self.vectorizer
        )
        
        self.assertEqual(len(results), 3)
        result_ids = [item['id'] for item in results]
        # Expected order based on cosine similarity with [1.0, 0.8, 0.2]:
        # id 2: Business Laptop Z -> ~0.99
        # id 1: Gaming Laptop X -> ~0.98
        # id 4: iPhone 15 -> ~0.94
        self.assertEqual(result_ids, [2, 1, 4])

    def test_filter_returns_no_candidates(self):
        """Test that an empty list is returned if the filter matches no items."""
        query_text = "any query"
        filters = {'category': 'nonexistent_category'}
        
        results = retrieve_with_vector_and_filter(
            query_text, filters, self.dataset, self.vectorizer
        )
        
        self.assertEqual(len(results), 0)
        self.assertIsInstance(results, list)

    def test_retrieval_with_multiple_filters(self):
        """Test that multiple filters are correctly applied before vector search."""
        query_text = "apple products"
        filters = {'category': 'electronics', 'year': 2023}
        
        results = retrieve_with_vector_and_filter(
            query_text, filters, self.dataset, self.vectorizer
        )
        
        # Only items 1 and 4 match the filters. Item 6 has no vector.
        self.assertEqual(len(results), 2)
        result_ids = [item['id'] for item in results]
        
        # Expected order based on similarity to [0.9, 0.9, 0.1]:
        # id 4: iPhone 15 -> ~0.99
        # id 1: Gaming Laptop X -> ~0.98
        self.assertEqual(result_ids, [4, 1])

    def test_top_k_parameter_limits_results(self):
        """Test that top_k correctly limits the number of returned items."""
        query_text = "latest gaming laptops"
        filters = {'category': 'electronics'}
        
        results = retrieve_with_vector_and_filter(
            query_text, filters, self.dataset, self.vectorizer, top_k=1
        )
        
        self.assertEqual(len(results), 1)
        # Item 2 has the highest cosine similarity
        self.assertEqual(results[0]['id'], 2)

    def test_search_with_no_filters(self):
        """Test that an empty filter dict results in a search over the entire dataset."""
        query_text = "ancient rome history"
        filters = {} # No filters
        
        results = retrieve_with_vector_and_filter(
            query_text, filters, self.dataset, self.vectorizer
        )
        
        result_ids = [item['id'] for item in results]
        # Should search all items with vectors and return the top 3 most similar
        # Expected order based on similarity to [0.1, 0.2, 0.9]:
        # id 5: Documentary on Rome -> ~0.99
        # id 3: Book on Roman Empire -> ~0.98
        # id 2: Business Laptop Z -> ~0.44
        self.assertEqual(result_ids, [5, 3, 2])

    def test_item_without_vector_key_is_ignored(self):
        """Test that filtered candidates lacking a 'vector' key are gracefully ignored."""
        query_text = "apple products"
        filters = {'year': 2023}
        
        results = retrieve_with_vector_and_filter(
            query_text, filters, self.dataset, self.vectorizer
        )
        
        # Items 1, 4, 5, 6 match the filter. Item 6 has no vector.
        # So search is performed on 1, 4, 5.
        result_ids = [item['id'] for item in results]
        
        # Item 6 should not be in the results
        self.assertNotIn(6, result_ids)
        self.assertEqual(len(results), 3)
        # Expected order: 4, 1, 5
        self.assertEqual(result_ids, [4, 1, 5])

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)