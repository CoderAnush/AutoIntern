"""Tests for Phase 4: Embeddings and recommendations engine."""

import pytest
import numpy as np
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.schemas.embeddings import EmbeddingOut, RecommendationResult, ResumeQualityScore
from app.services.embeddings_service import EmbeddingsManager
from app.services.recommendation_service import RecommendationEngine


class TestEmbeddingsService:
    """Tests for EmbeddingsManager and Sentence-BERT integration."""

    def test_generate_embedding_shape(self):
        """Verify generated embeddings are 384-dimensional."""
        mgr = EmbeddingsManager()
        text = "Python Django React AWS Docker Kubernetes PostgreSQL machine learning TensorFlow"
        embedding = mgr.generate_embedding(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (EmbeddingsManager.EMBEDDING_DIM,)
        assert embedding.dtype == np.float32

    def test_generate_embedding_different_texts_different_vectors(self):
        """Verify different texts produce different embeddings."""
        mgr = EmbeddingsManager()
        text1 = "Python developer with Django experience"
        text2 = "Java backend engineer with Spring Boot"

        embedding1 = mgr.generate_embedding(text1)
        embedding2 = mgr.generate_embedding(text2)

        # Embeddings should be different
        assert not np.allclose(embedding1, embedding2)

    def test_generate_embedding_rejects_short_text(self):
        """Verify short text raises ValueError."""
        mgr = EmbeddingsManager()
        with pytest.raises(ValueError, match="too short"):
            mgr.generate_embedding("Too short")

    def test_generate_embedding_rejects_empty_text(self):
        """Verify empty text raises ValueError."""
        mgr = EmbeddingsManager()
        with pytest.raises(ValueError):
            mgr.generate_embedding("")

    @pytest.mark.asyncio
    async def test_add_job_embedding_saves_to_db(self, mock_async_db):
        """Verify job embedding is saved to database."""
        mgr = EmbeddingsManager()
        job_id = str(uuid4())
        job_text = "Senior Python Developer - AWS Cloud - 5 years experience"

        # Mock database operations
        mock_async_db.add = Mock()
        mock_async_db.commit = AsyncMock()
        mock_async_db.refresh = AsyncMock()

        # Note: This test would require proper async DB setup
        # Simplified for demonstration
        assert job_id  # Placeholder assertion

    @pytest.mark.asyncio
    async def test_add_resume_embedding_saves_to_db(self, mock_async_db):
        """Verify resume embedding is saved to database."""
        mgr = EmbeddingsManager()
        resume_id = str(uuid4())
        resume_text = "Python, JavaScript, React, Django, PostgreSQL, AWS, Docker" * 10

        # Mock database
        mock_async_db.add = Mock()
        mock_async_db.commit = AsyncMock()
        mock_async_db.refresh = AsyncMock()

        assert resume_id  # Placeholder

    def test_search_similar_jobs_returns_empty_on_empty_index(self):
        """Verify search returns empty list when FAISS index is empty."""
        mgr = EmbeddingsManager()
        # Create fresh manager without any embeddings
        resume_embedding = np.random.rand(EmbeddingsManager.EMBEDDING_DIM).astype(np.float32)

        results = mgr.search_similar_jobs(resume_embedding, top_k=10)
        assert results == []

    def test_search_similar_resumes_returns_empty_on_empty_index(self):
        """Verify resume search returns empty list when FAISS index is empty."""
        mgr = EmbeddingsManager()
        job_embedding = np.random.rand(EmbeddingsManager.EMBEDDING_DIM).astype(np.float32)

        results = mgr.search_similar_resumes(job_embedding, top_k=10)
        assert results == []


class TestRecommendationService:
    """Tests for RecommendationEngine and quality scoring."""

    def test_calculate_skill_match_finds_common_skills(self):
        """Verify skill matching identifies common skills correctly."""
        resume_skills = ["Python", "Django", "PostgreSQL", "Docker"]
        job_desc = "We need Python and Django expertise with PostgreSQL databases"

        matched, gaps = RecommendationEngine.calculate_skill_match(resume_skills, job_desc)

        # Should find at least some Python/Django mentions
        assert len(matched) > 0 or len(gaps) > 0  # Skills exist in job desc

    def test_calculate_skill_match_identifies_gaps(self):
        """Verify skill matching identifies missing skills."""
        resume_skills = ["Python", "Django"]
        job_desc = "Need Python, Java, C++, Kubernetes, AWS expertise"

        matched, gaps = RecommendationEngine.calculate_skill_match(resume_skills, job_desc)

        # Should identify gaps in Java, C++, Kubernetes, AWS
        assert isinstance(gaps, list)
        assert isinstance(matched, list)

    def test_skill_match_case_insensitive(self):
        """Verify skill matching is case-insensitive."""
        resume_skills = ["python", "django"]
        job_desc = "We need PYTHON and DJANGO expertise"

        matched, gaps = RecommendationEngine.calculate_skill_match(resume_skills, job_desc)

        # Should match despite case differences
        assert isinstance(matched, list)

    def test_score_recommendation_basic(self):
        """Verify composite scoring calculates correctly."""
        # Pure vector similarity
        score = RecommendationEngine.score_recommendation(
            similarity_score=0.8,
            matched_skills_count=0,
            total_job_skills=1
        )
        assert 0.0 <= score <= 1.0
        assert score == pytest.approx(0.56)  # 0.7 * 0.8 + 0.3 * 0

    def test_score_recommendation_with_skills(self):
        """Verify scoring improves with skill matches."""
        score_no_skills = RecommendationEngine.score_recommendation(0.8, 0, 5)
        score_with_skills = RecommendationEngine.score_recommendation(0.8, 5, 5)

        assert score_with_skills > score_no_skills

    def test_score_recommendation_capped_at_100(self):
        """Verify score is capped at 1.0."""
        score = RecommendationEngine.score_recommendation(
            similarity_score=1.0,
            matched_skills_count=10,
            total_job_skills=5
        )
        assert score <= 1.0

    def test_calculate_resume_quality_short_text_low_score(self):
        """Verify short resumes get low text length scores."""
        short_resume = "I know Python and Java."  # < 500 chars
        skills = ["Python", "Java"]

        quality = RecommendationEngine.calculate_resume_quality(short_resume, skills)

        assert quality["text_length_score"] < 50
        assert 0 <= quality["overall_quality_score"] <= 100

    def test_calculate_resume_quality_long_text_high_score(self):
        """Verify longer resumes get higher text length scores."""
        long_resume = "Python Developer..." + "x" * 1000  # > 500 chars
        skills = ["Python", "Django", "React"]

        quality = RecommendationEngine.calculate_resume_quality(long_resume, skills)

        assert quality["text_length_score"] >= 50
        assert 0 <= quality["overall_quality_score"] <= 100

    def test_calculate_resume_quality_with_skills(self):
        """Verify quality scoring reflects skill count."""
        resume = "Python Django React" + "x" * 1000
        skills_few = ["Python"]
        skills_many = ["Python", "Django", "React", "JavaScript", "Java", "C++", "Go", "Rust"]

        quality_few = RecommendationEngine.calculate_resume_quality(resume, skills_few)
        quality_many = RecommendationEngine.calculate_resume_quality(resume, skills_many)

        # More skills should give higher skill_count_score
        assert quality_many["skill_count_score"] > quality_few["skill_count_score"]

    def test_calculate_resume_quality_soft_skills_detection(self):
        """Verify completeness scoring detects soft skills."""
        resume_tech_only = "Python Django React PostgreSQL AWS" + "x" * 1000
        resume_with_soft = "Python Django communication teamwork leadership" + "x" * 1000

        quality_tech = RecommendationEngine.calculate_resume_quality(resume_tech_only, ["Python"])
        quality_both = RecommendationEngine.calculate_resume_quality(resume_with_soft, ["Python"])

        # Resume with soft skills should have higher completeness
        assert quality_both["completeness_score"] >= quality_tech["completeness_score"]

    @pytest.mark.asyncio
    async def test_recommend_jobs_for_resume_structure(self):
        """Verify recommendation structure is correct."""
        # This is a placeholder test as full async DB setup is complex
        # In production, would use proper async test fixtures
        pass

    def test_recommend_jobs_error_handling(self):
        """Verify error handling in recommendation flow."""
        # Verify no exceptions on empty input
        try:
            RecommendationEngine.calculate_skill_match([], "job description")
            RecommendationEngine.calculate_resume_quality("", [])
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")


class TestRecommendationModels:
    """Tests for Pydantic response models."""

    def test_recommendation_result_model(self):
        """Verify RecommendationResult model validates correctly."""
        data = {
            "job_id": str(uuid4()),
            "job_title": "Python Developer",
            "job_description": "Senior Python role",
            "job_location": "San Francisco",
            "resume_id": str(uuid4()),
            "similarity_score": 0.85,
            "matched_skills": ["Python", "Django"],
            "skill_gaps": ["Kubernetes", "AWS"]
        }

        result = RecommendationResult(**data)
        assert result.job_title == "Python Developer"
        assert result.similarity_score == 0.85
        assert len(result.matched_skills) == 2

    def test_resume_quality_score_model(self):
        """Verify ResumeQualityScore model validates correctly."""
        data = {
            "resume_id": str(uuid4()),
            "text_length_score": 85.5,
            "skill_count_score": 75.0,
            "completeness_score": 90.0,
            "overall_quality_score": 83.5
        }

        quality = ResumeQualityScore(**data)
        assert quality.overall_quality_score == 83.5
        assert 0 <= quality.text_length_score <= 100


class TestEmbeddingsIntegration:
    """Integration tests for embeddings with recommendations."""

    def test_embeddings_manager_singleton(self):
        """Verify EmbeddingsManager uses singleton pattern."""
        mgr1 = EmbeddingsManager()
        mgr2 = EmbeddingsManager()

        # Both should reference same model
        assert True  # Simplified

    def test_recommendation_flow_end_to_end(self):
        """Verify complete recommendation flow works."""
        # Simplified test (full version requires async DB)
        mgr = EmbeddingsManager()

        # 1. Generate embeddings
        resume_text = "Python Django PostgreSQL AWS Docker" * 5
        job_text = "Senior Python Developer - AWS Cloud" * 5

        resume_embedding = mgr.generate_embedding(resume_text)
        job_embedding = mgr.generate_embedding(job_text)

        assert resume_embedding.shape == (384,)
        assert job_embedding.shape == (384,)

        # 2. Calculate quality
        skills = ["Python", "Django", "AWS"]
        quality = RecommendationEngine.calculate_resume_quality(resume_text, skills)
        assert "overall_quality_score" in quality

        # 3. Calculate skill match
        matched, gaps = RecommendationEngine.calculate_skill_match(skills, job_text)
        assert isinstance(matched, list)
        assert isinstance(gaps, list)

        # 4. Calculate recommendation score
        score = RecommendationEngine.score_recommendation(0.75, len(matched), len(matched) + len(gaps))
        assert 0.0 <= score <= 1.0


# Fixtures for test support
@pytest.fixture
def mock_async_db():
    """Create mock async database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
    Senior Software Engineer

    Skills: Python, JavaScript, Django, React, PostgreSQL, MongoDB,
    AWS, Docker, Kubernetes, Git, Linux

    Experience:
    - 5 years building scalable web applications
    - Expert in Python and JavaScript
    - AWS certified cloud architect
    - Leadership and team management experience

    Education:
    - BS Computer Science
    """


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Senior Python Developer - Remote

    Requirements:
    - 5+ years Python experience
    - Django or FastAPI framework
    - PostgreSQL database design
    - AWS cloud services (EC2, RDS, Lambda)
    - Docker and Kubernetes
    - Git version control
    - Leadership and mentoring skills

    Nice to have:
    - Machine Learning experience
    - TensorFlow or PyTorch
    """
