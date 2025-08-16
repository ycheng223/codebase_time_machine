import chromadb
from typing import List, Dict, Any
from embedding_generator import EmbeddingGenerator

class DataIngestionPipeline:
    """
    Processes commit data, generates embeddings, and stores them in a ChromaDB
    vector database.
    """

    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
        db_path: str = "./chroma_db",
        collection_name: str = "commits"
    ):
        """
        Initializes the pipeline with an embedding generator and a connection
        to a ChromaDB collection.

        Args:
            embedding_generator (EmbeddingGenerator): An instance of the class
                responsible for creating embeddings.
            db_path (str): The file path for the persistent ChromaDB storage.
            collection_name (str): The name of the collection to store commits in.
        """
        self.embedding_generator = embedding_generator
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def ingest_commits(self, commits: List[Dict[str, Any]]):
        """
        Processes a batch of commits, generates embeddings for their summaries,
        and upserts them into the vector database.

        The commit dictionary is expected to have at least 'commit_hash' and
        'summary' keys. Other key-value pairs will be stored as metadata.

        Args:
            commits (List[Dict[str, Any]]): A list of commit data, where each
                commit is a dictionary.
        """
        if not commits:
            return

        # Prepare data for batch processing
        commit_ids = [commit['commit_hash'] for commit in commits]
        summaries = [commit['summary'] for commit in commits]
        
        # Use other commit info as metadata, excluding the ID field
        metadatas = [
            {k: v for k, v in commit.items() if k != 'commit_hash'}
            for commit in commits
        ]

        # Generate embeddings in a single batch for efficiency
        embeddings = self.embedding_generator.generate_embeddings(summaries)

        # Upsert the data into the ChromaDB collection.
        # Upserting is idempotent and handles both new inserts and updates for
        # existing IDs.
        self.collection.upsert(
            ids=commit_ids,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            documents=summaries
        )