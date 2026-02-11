"""Embedding generation and FAISS vector search service."""

import logging
import numpy as np
from typing import List, Tuple, Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Global cache for Sentence-BERT model and FAISS index
_model = None
_faiss_index = None
_id_to_idx_mapping = {}  # Maps embedding IDs to FAISS indices
_idx_to_id_mapping = {}  # Maps FAISS indices to embedding IDs


class EmbeddingsManager:
    """Manages Sentence-BERT embeddings and FAISS vector indexing."""

    EMBEDDING_DIM = 384
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self):
        """Initialize embeddings manager, loading model on first call."""
        global _model, _faiss_index

        if _model is None:
            self._load_model()

        if _faiss_index is None:
            self._initialize_faiss_index()

    @staticmethod
    def _load_model():
        """Load Sentence-BERT model on first use."""
        global _model
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading Sentence-BERT model: {EmbeddingsManager.MODEL_NAME}")
            _model = SentenceTransformer(EmbeddingsManager.MODEL_NAME)
            logger.info("Model loaded successfully")
        except ImportError:
            raise RuntimeError("sentence-transformers not installed. Install with: pip install sentence-transformers")
        except Exception as e:
            logger.error(f"Failed to load Sentence-BERT model: {e}")
            raise

    @staticmethod
    def _initialize_faiss_index():
        """Initialize FAISS flat L2 index for 384-dimensional vectors."""
        global _faiss_index
        try:
            import faiss
            logger.info(f"Initializing FAISS index with {EmbeddingsManager.EMBEDDING_DIM} dimensions")
            _faiss_index = faiss.IndexFlatL2(EmbeddingsManager.EMBEDDING_DIM)
            logger.info("FAISS index initialized")
        except ImportError:
            raise RuntimeError("faiss not installed. Install with: pip install faiss-cpu")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            raise

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate a 384-dimensional embedding for text using Sentence-BERT.

        Args:
            text: Input text (job description or resume)

        Returns:
            384-dimensional numpy array (normalized)

        Raises:
            ValueError: If text is empty or too short
        """
        if not text or len(text.strip()) < 20:
            raise ValueError("Text too short for embedding (minimum 20 characters)")

        try:
            # Encode text to embedding (returns normalized vectors by default)
            embedding = _model.encode(text.strip(), convert_to_numpy=True)
            logger.debug(f"Generated embedding with shape {embedding.shape}")
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise ValueError(f"Embedding generation failed: {str(e)}")

    async def add_job_embedding(self, job_id: str, job_text: str, db: AsyncSession):
        """
        Generate and save embedding for a job.

        Args:
            job_id: UUID of the job
            job_text: Job description text (for embedding generation)
            db: AsyncSession for database operations

        Returns:
            Created Embedding model instance
        """
        try:
            from app.models.models import Embedding as EmbeddingModel

            # Generate embedding
            embedding_vector = self.generate_embedding(job_text)

            # Add to FAISS index
            index_id = len(_idx_to_id_mapping)
            _faiss_index.add(np.array([embedding_vector]))
            _idx_to_id_mapping[index_id] = job_id
            _id_to_idx_mapping[job_id] = index_id

            # Save to database
            embedding_record = EmbeddingModel(
                id=str(uuid4()),
                parent_type="job",
                parent_id=job_id,
                model_name=self.MODEL_NAME,
                vector=embedding_vector.tolist()  # Store as list in JSONB
            )
            db.add(embedding_record)
            await db.commit()
            await db.refresh(embedding_record)

            logger.info(f"Saved job embedding for job_id: {job_id}")
            return embedding_record

        except Exception as e:
            logger.error(f"Failed to add job embedding: {e}")
            await db.rollback()
            raise

    async def add_resume_embedding(self, resume_id: str, resume_text: str, db: AsyncSession):
        """
        Generate and save embedding for a resume.

        Args:
            resume_id: UUID of the resume
            resume_text: Resume parsed text (for embedding generation)
            db: AsyncSession for database operations

        Returns:
            Created Embedding model instance
        """
        try:
            from app.models.models import Embedding as EmbeddingModel

            # Generate embedding
            embedding_vector = self.generate_embedding(resume_text)

            # Add to FAISS index
            index_id = len(_idx_to_id_mapping)
            _faiss_index.add(np.array([embedding_vector]))
            _idx_to_id_mapping[index_id] = resume_id
            _id_to_idx_mapping[resume_id] = index_id

            # Save to database
            embedding_record = EmbeddingModel(
                id=str(uuid4()),
                parent_type="resume",
                parent_id=resume_id,
                model_name=self.MODEL_NAME,
                vector=embedding_vector.tolist()  # Store as list in JSONB
            )
            db.add(embedding_record)
            await db.commit()
            await db.refresh(embedding_record)

            logger.info(f"Saved resume embedding for resume_id: {resume_id}")
            return embedding_record

        except Exception as e:
            logger.error(f"Failed to add resume embedding: {e}")
            await db.rollback()
            raise

    def search_similar_jobs(self, resume_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find top_k most similar jobs to a resume using FAISS.

        Args:
            resume_embedding: 384-dimensional resume embedding vector
            top_k: Number of results to return

        Returns:
            List of (job_id, similarity_score) tuples sorted by score descending
        """
        try:
            if _faiss_index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return []

            # FAISS returns distances (L2), need to convert to similarity
            distances, indices = _faiss_index.search(
                np.array([resume_embedding]).astype(np.float32),
                min(top_k, _faiss_index.ntotal)
            )

            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx != -1 and idx in _idx_to_id_mapping:
                    job_id = _idx_to_id_mapping[idx]
                    # Convert L2 distance to similarity score (0-1 range)
                    similarity = 1.0 / (1.0 + distance)
                    results.append((job_id, float(similarity)))

            # Sort by similarity descending
            results.sort(key=lambda x: x[1], reverse=True)
            logger.debug(f"Found {len(results)} similar jobs")
            return results

        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []

    def search_similar_resumes(self, job_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find top_k most similar resumes to a job using FAISS.

        Args:
            job_embedding: 384-dimensional job embedding vector
            top_k: Number of results to return

        Returns:
            List of (resume_id, similarity_score) tuples sorted by score descending
        """
        try:
            if _faiss_index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return []

            # FAISS returns distances (L2), need to convert to similarity
            distances, indices = _faiss_index.search(
                np.array([job_embedding]).astype(np.float32),
                min(top_k, _faiss_index.ntotal)
            )

            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx != -1 and idx in _idx_to_id_mapping:
                    resume_id = _idx_to_id_mapping[idx]
                    # Convert L2 distance to similarity score (0-1 range)
                    similarity = 1.0 / (1.0 + distance)
                    results.append((resume_id, float(similarity)))

            # Sort by similarity descending
            results.sort(key=lambda x: x[1], reverse=True)
            logger.debug(f"Found {len(results)} similar resumes")
            return results

        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []

    async def rebuild_index_from_db(self, db: AsyncSession):
        """
        Rebuild FAISS index from all embeddings in database.
        Called on service startup for stateless deployment.

        Args:
            db: AsyncSession for database operations
        """
        global _idx_to_id_mapping, _id_to_idx_mapping, _faiss_index

        try:
            from app.models.models import Embedding as EmbeddingModel

            logger.info("Rebuilding FAISS index from database")

            # Clear existing mappings and index
            _idx_to_id_mapping.clear()
            _id_to_idx_mapping.clear()
            _faiss_index.reset()

            # Fetch all embeddings from database ordered by parent_type, parent_id
            result = await db.execute(
                select(EmbeddingModel).order_by(EmbeddingModel.parent_type, EmbeddingModel.parent_id)
            )
            embeddings = result.scalars().all()

            if not embeddings:
                logger.info("No embeddings found in database")
                return

            # Rebuild index
            for idx, embedding_record in enumerate(embeddings):
                embedding_vector = np.array(embedding_record.vector, dtype=np.float32)
                _faiss_index.add(np.array([embedding_vector]))
                _idx_to_id_mapping[idx] = embedding_record.parent_id
                _id_to_idx_mapping[embedding_record.parent_id] = idx

            logger.info(f"Rebuilt FAISS index with {len(embeddings)} embeddings")

        except Exception as e:
            logger.error(f"Failed to rebuild FAISS index: {e}")
            raise
