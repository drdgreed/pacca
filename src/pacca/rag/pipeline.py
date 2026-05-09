"""
RAG (Retrieval-Augmented Generation) pipeline for clinical guidelines.

Provides semantic search over clinical guidelines using ChromaDB
for vector storage and Anthropic embeddings for similarity matching.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings

from pacca.config import get_logger, get_settings
from pacca.models import ClinicalGuideline, GuidelineChunk, GuidelineSearchResult

logger = get_logger(__name__)


class GuidelineVectorStore:
    """
    Vector store for clinical guidelines using ChromaDB.

    Handles embedding generation, storage, and semantic retrieval
    of guideline content for RAG-based decision support.
    """

    def __init__(
        self,
        collection_name: str = "clinical_guidelines",
        persist_directory: str | None = None,
    ):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory for persistent storage (None for in-memory)
        """
        self.collection_name = collection_name
        self.settings = get_settings()

        # Initialize ChromaDB client
        if persist_directory:
            self._client = chromadb.PersistentClient(
                path=persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        else:
            self._client = chromadb.Client(
                settings=ChromaSettings(anonymized_telemetry=False),
            )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Clinical guidelines for prior authorization"},
        )

        logger.info(
            "vector_store_initialized",
            collection=collection_name,
            persistent=persist_directory is not None,
        )

    @property
    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self._collection.count()

    async def add_guideline(
        self,
        guideline: ClinicalGuideline,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list[str]:
        """
        Add a clinical guideline to the vector store.

        The guideline is chunked into smaller pieces for effective
        semantic retrieval.

        Args:
            guideline: The guideline to add
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between consecutive chunks

        Returns:
            List of chunk IDs created
        """
        # Chunk the guideline content
        chunks = self._chunk_text(
            guideline.full_text,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
        )

        chunk_ids = []
        documents = []
        metadatas = []
        ids = []

        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{guideline.guideline_id}_chunk_{i}"
            chunk_ids.append(chunk_id)

            documents.append(chunk_text)
            metadatas.append(
                {
                    "guideline_id": guideline.guideline_id,
                    "guideline_name": guideline.name,
                    "source": guideline.source,
                    "version": guideline.version,
                    "chunk_index": i,
                    "specialties": ",".join(s.value for s in guideline.specialties),
                    "treatment_categories": ",".join(
                        c.value for c in guideline.treatment_categories
                    ),
                    "effective_date": guideline.effective_date.isoformat(),
                }
            )
            ids.append(chunk_id)

        # Add to ChromaDB (embeddings generated automatically)
        self._collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info(
            "guideline_added_to_vector_store",
            guideline_id=guideline.guideline_id,
            chunks_created=len(chunk_ids),
        )

        return chunk_ids

    async def search(
        self,
        query: str,
        n_results: int = 5,
        specialty_filter: str | None = None,
        treatment_category_filter: str | None = None,
    ) -> list[GuidelineSearchResult]:
        """
        Search for relevant guideline content.

        Args:
            query: The search query (clinical context)
            n_results: Maximum number of results
            specialty_filter: Filter by specialty
            treatment_category_filter: Filter by treatment category

        Returns:
            List of search results with relevance scores
        """
        # Build where clause for filtering
        where_clause = None
        if specialty_filter or treatment_category_filter:
            conditions = []
            if specialty_filter:
                conditions.append({"specialties": {"$contains": specialty_filter}})
            if treatment_category_filter:
                conditions.append(
                    {"treatment_categories": {"$contains": treatment_category_filter}}
                )

            where_clause = conditions[0] if len(conditions) == 1 else {"$and": conditions}

        # Execute search
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []

        # Convert to GuidelineSearchResult objects
        search_results = []

        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                document = results["documents"][0][i] if results["documents"] else ""
                distance = results["distances"][0][i] if results["distances"] else 1.0

                # Convert distance to similarity score (ChromaDB uses L2 distance)
                # Lower distance = more similar, so we invert
                similarity = 1.0 / (1.0 + distance)

                chunk = GuidelineChunk(
                    chunk_id=chunk_id,
                    guideline_id=metadata.get("guideline_id", ""),
                    guideline_name=metadata.get("guideline_name", ""),
                    source=metadata.get("source", ""),
                    content=document,
                    chunk_index=metadata.get("chunk_index", 0),
                )

                search_results.append(
                    GuidelineSearchResult(
                        chunk=chunk,
                        similarity_score=similarity,
                        rank=i + 1,
                    )
                )

        logger.info(
            "vector_search_completed",
            query_length=len(query),
            results_count=len(search_results),
        )

        return search_results

    async def delete_guideline(self, guideline_id: str) -> int:
        """
        Delete a guideline and all its chunks from the vector store.

        Args:
            guideline_id: The guideline to delete

        Returns:
            Number of chunks deleted
        """
        # Find all chunks for this guideline
        results = self._collection.get(
            where={"guideline_id": guideline_id},
            include=[],
        )

        if not results["ids"]:
            return 0

        # Delete the chunks
        self._collection.delete(ids=results["ids"])

        logger.info(
            "guideline_deleted_from_vector_store",
            guideline_id=guideline_id,
            chunks_deleted=len(results["ids"]),
        )

        return len(results["ids"])

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[str]:
        """
        Split text into overlapping chunks.

        Uses sentence boundaries when possible to avoid
        cutting in the middle of sentences.
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Find the end position
            end = start + chunk_size

            # If we're not at the end, try to find a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 20% of the chunk
                search_start = end - int(chunk_size * 0.2)
                last_period = text.rfind(". ", search_start, end)
                last_newline = text.rfind("\n", search_start, end)

                # Use the latest sentence boundary found
                boundary = max(last_period, last_newline)
                if boundary > search_start:
                    end = boundary + 1

            chunks.append(text[start:end].strip())

            # Move start position, accounting for overlap
            start = end - overlap
            start = max(start, 0)

            # Avoid infinite loop for very small texts
            if start >= len(text) - overlap:
                break

        return chunks


class RAGPipeline:
    """
    RAG pipeline for clinical decision support.

    Combines vector search with LLM-based response generation
    to provide evidence-based guideline recommendations.
    """

    def __init__(
        self,
        vector_store: GuidelineVectorStore | None = None,
        persist_directory: str = "./chroma_data",
    ):
        """
        Initialize the RAG pipeline.

        Args:
            vector_store: Pre-configured vector store (created if None)
            persist_directory: Directory for persistent vector storage
        """
        self.vector_store = vector_store or GuidelineVectorStore(
            persist_directory=persist_directory
        )
        self.settings = get_settings()

    async def retrieve_relevant_guidelines(
        self,
        diagnosis_code: str,
        diagnosis_description: str,
        treatment_code: str,
        treatment_description: str,
        treatment_category: str,
        clinical_context: str | None = None,
        n_results: int = 5,
    ) -> str:
        """
        Retrieve relevant guidelines for a clinical case.

        Args:
            diagnosis_code: ICD-10 diagnosis code
            diagnosis_description: Diagnosis description
            treatment_code: Treatment/procedure code
            treatment_description: Treatment description
            treatment_category: Category of treatment
            clinical_context: Additional clinical context
            n_results: Maximum guidelines to retrieve

        Returns:
            Formatted string of relevant guideline excerpts
        """
        # Build search query from clinical information
        query_parts = [
            f"Diagnosis: {diagnosis_code} {diagnosis_description}",
            f"Treatment: {treatment_code} {treatment_description}",
            f"Category: {treatment_category}",
        ]

        if clinical_context:
            query_parts.append(f"Context: {clinical_context}")

        query = "\n".join(query_parts)

        # Search for relevant guidelines
        results = await self.vector_store.search(
            query=query,
            n_results=n_results,
            treatment_category_filter=treatment_category.lower(),
        )

        if not results:
            # Retry without category filter if no results
            results = await self.vector_store.search(
                query=query,
                n_results=n_results,
            )

        if not results:
            return "No specific guidelines found for this clinical scenario."

        # Format results for LLM context
        formatted_results = []

        for result in results:
            chunk = result.chunk
            formatted_results.append(
                f"### {chunk.guideline_name} ({chunk.source})\n"
                f"Relevance Score: {result.similarity_score:.2f}\n\n"
                f"{chunk.content}\n"
            )

        return "\n---\n".join(formatted_results)

    async def add_sample_guidelines(self) -> int:
        """
        Add sample clinical guidelines for demo purposes.

        Returns:
            Number of guidelines added
        """
        from pacca.rag.sample_guidelines import SAMPLE_GUIDELINES

        count = 0
        for guideline in SAMPLE_GUIDELINES:
            await self.vector_store.add_guideline(guideline)
            count += 1

        logger.info("sample_guidelines_loaded", count=count)
        return count
