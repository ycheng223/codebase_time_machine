import numpy as np

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