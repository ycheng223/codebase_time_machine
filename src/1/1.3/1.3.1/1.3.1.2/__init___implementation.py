from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np

class EmbeddingGenerator:
    """
    Generates embeddings for semantic summaries and code chunks using a
    pre-trained sentence-transformer model.
    """

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initializes the generator and loads the sentence-transformer model.

        On first instantiation, this may download the model which can take time
        and require an internet connection.

        Args:
            model_name (str): The name of the model to use from the
                              sentence-transformers library. 'all-mpnet-base-v2'
                              is a strong general-purpose model.
        """
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(
        self, texts: Union[str, List[str]]
    ) -> np.ndarray:
        """
        Encodes a single text or a list of texts into embedding vectors.

        Args:
            texts (Union[str, List[str]]): The text or texts to encode.
                Can be semantic summaries, code chunks, or other text.

        Returns:
            np.ndarray: A numpy array containing the embedding(s).
            - If the input is a single string, the shape will be (embedding_dim,).
            - If the input is a list of N strings, the shape will be (N, embedding_dim).
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings