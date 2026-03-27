# Chroma / FAISS wrapper
import json
from datetime import datetime
from typing import List, Dict

import chromadb
from chromadb.config import Settings
from docx.document import Document


class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize persistent ChromaDB client
        Schema:
            id
            embedding
            document text
            metadata
        """
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            )
        )
        self.collection_name = "rfp_knowledge"

    # COLLECTION HANDLING

    def get_collection(self, name: str):
        return self.client.get_or_create_collection(name=name)

    def delete_collection(self, name: str):
        self.client.delete_collection(name)
        return {"status": f"{name} deleted"}

    # ADD DOCUMENTS

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict]
    ):
        collection = self.get_collection(collection_name)

        ids = [f"id_{i}_{datetime.utcnow().timestamp()}" for i in range(len(documents))]

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return {
            "status": "documents added",
            "count": len(documents)
        }

    # SIMILARITY SEARCH

    from langchain_core.documents import Document

    def similarity_search(
        self,
        collection_name: str,
        query_embedding,
        k: int = 5
    ):
        collection = self.get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        output = []

        for doc, meta, dist in zip(documents, metadatas, distances):
            score = 1 - dist  # convert distance → similarity
            output.append(
                (Document(page_content=doc, metadata=meta), score)
            )

        return output

    # GET ALL DOCUMENTS

    def get_documents(self, collection_name: str):
        collection = self.get_collection(collection_name)
        return collection.get()

    # HEALTH CHECK
    def health_check(self, collection_name: str):
        collection = self.get_collection(collection_name)
        data = collection.get()

        total_vectors = len(data["ids"]) if data["ids"] else 0

        avg_doc_length = 0
        if data["documents"]:
            lengths = [len(doc) for doc in data["documents"]]
            avg_doc_length = sum(lengths) / len(lengths)

        return {
            "vector_count": total_vectors,
            "avg_doc_length": avg_doc_length,
            "last_checked": str(datetime.utcnow())
        }

    # BACKUP TO JSON

    def backup_collection(self, collection_name: str):
        collection = self.get_collection(collection_name)
        data = collection.get()

        backup_file = f"{collection_name}_backup.json"

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return {
            "status": "backup created",
            "file": backup_file
        }
