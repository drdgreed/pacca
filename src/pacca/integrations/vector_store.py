import chromadb
from chromadb.utils import embedding_functions
import os

class GuidelineRetriever:
    def __init__(self):
        # Use a persistent local database
        db_path = os.path.join(os.getcwd(), "pacca_db")
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Collection 1: The Official Rules (NCCN/CMS)
        self.guidelines = self.client.get_or_create_collection(
            name="nccn_guidelines",
            embedding_function=self.embedding_fn
        )
        
        # Collection 2: The Institutional Memory (Human Overrides)
        self.precedents = self.client.get_or_create_collection(
            name="case_precedents",
            embedding_function=self.embedding_fn
        )

    def add_guideline(self, guideline_text: str, source_id: str, metadata: dict):
        # We assume overwrite if ID exists for simplicity
        self.guidelines.upsert(
            documents=[guideline_text],
            metadatas=[metadata],
            ids=[source_id]
        )

    def add_precedent(self, case_summary: str, rationale: str, outcome: str):
        self.precedents.add(
            documents=[f"SCENARIO: {case_summary}\nOUTCOME: {outcome}\nREASON: {rationale}"],
            metadatas=[{"type": "human_override"}],
            ids=[f"prec_{hash(case_summary)}"]
        )

    def query(self, clinical_query: str) -> str:
        # 1. Search Official Rules
        rules = self.guidelines.query(query_texts=[clinical_query], n_results=2)
        
        # 2. Search Past Decisions (Memory)
        memories = self.precedents.query(query_texts=[clinical_query], n_results=1)
        
        context = "OFFICIAL GUIDELINES:\n"
        if rules['documents']:
            for doc in rules['documents'][0]:
                context += f"- {doc}\n"
            
        if memories['documents'] and memories['documents'][0]:
            context += "\nPAST MEDICAL DIRECTOR DECISIONS (PRECEDENTS):\n"
            for doc in memories['documents'][0]:
                context += f"- {doc}\n"
                
        return context
