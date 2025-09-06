import chromadb
from chromadb.utils import embedding_functions

class KnowledgeBase:
    def __init__(self, persist_dir="backend/data"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            "compliance_rules",
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )

    def add_rule(self, text: str, rule_id: str):
        self.collection.add(documents=[text], ids=[rule_id])

    def query(self, text: str):
        return self.collection.query(query_texts=[text], n_results=2)
