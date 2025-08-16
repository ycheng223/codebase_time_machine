import numpy as np
import json
import os
from typing import List, Dict, Any

def store_embeddings_with_metadata(
    embeddings: np.ndarray,
    metadata: List[Dict[str, Any]],
    embedding_path: str,
    metadata_path: str
) -> None:
    """
    Stores embeddings and their associated metadata to separate files.

    This function saves the numerical embeddings to a .npy file for efficient
    storage and retrieval, and the corresponding metadata to a human-readable
    .json file. It ensures that the number of embeddings matches the number
    of metadata records and creates the necessary directories if they don't exist.

    Args:
        embeddings: A numpy.ndarray of shape (n, d), where n is the number
                    of items and d is the embedding dimension.
        metadata: A list of n dictionaries, where each dictionary contains
                  the metadata for the corresponding embedding.
        embedding_path: The file path to save the embeddings (e.g., 'data/embeddings.npy').
        metadata_path: The file path to save the metadata (e.g., 'data/metadata.json').

    Raises:
        ValueError: If the number of embeddings does not match the number of
                    metadata entries.
    """
    if len(embeddings) != len(metadata):
        raise ValueError(
            f"Mismatch between number of embeddings ({len(embeddings)}) and "
            f"metadata entries ({len(metadata)})."
        )

    # Ensure parent directories exist for the output files
    for path in [embedding_path, metadata_path]:
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

    # Save the embeddings array to a binary file in .npy format
    np.save(embedding_path, embeddings)

    # Save the metadata list to a JSON file
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)