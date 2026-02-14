"""Job recommendation engine with skill matching and quality scoring."""

import logging
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.skill_extractor import extract_skills_from_text

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Provides recommendation and quality scoring logic."""

    EXPECTED_SKILL_COUNT = 8  # For normalization
    MIN_RESUME_LENGTH = 500  # Characters
    SOFT_SKILLS_KEYWORDS = {
        "communication", "teamwork", "leadership", "management",
        "problem solving", "analytical", "critical thinking",
        "collaboration", "time management", "adaptability"
    }

    @staticmethod
    def calculate_skill_match(resume_skills: List[str], job_description: str) -> Tuple[List[str], List[str]]:
        """
        Calculate matched skills and skill gaps between resume and job.

        Args:
            resume_skills: List of skills extracted from resume
            job_description: Job description text

        Returns:
            Tuple of (matched_skills, skill_gaps)
        """
        try:
            # Extract skills from job description
            job_skills = extract_skills_from_text(job_description)

            # Normalize to lowercase for comparison
            resume_skills_lower = {s.lower() for s in resume_skills}
            job_skills_lower = {s.lower() for s in job_skills}

            # Calculate matches and gaps
            matched = [s for s in job_skills if s.lower() in resume_skills_lower]
            gaps = [s for s in job_skills if s.lower() not in resume_skills_lower]

            logger.debug(f"Skill match: {len(matched)} matched, {len(gaps)} gaps")
            return matched, gaps

        except Exception as e:
            logger.error(f"Skill matching error: {e}")
            return [], []

    @staticmethod
    def score_recommendation(
        similarity_score: float,
        matched_skills_count: int = 0,
        total_job_skills: int = 1
    ) -> float:
        """
        Calculate composite recommendation score.

        Weighted: 70% vector similarity + 30% skill match ratio

        Args:
            similarity_score: 0.0-1.0 from FAISS cosine similarity
            matched_skills_count: Number of matched skills
            total_job_skills: Total skills in job description

        Returns:
            Final composite score 0.0-1.0
        """
        try:
            # Ensure total_job_skills > 0 to avoid division by zero
            if total_job_skills == 0:
                total_job_skills = 1

            # Calculate skill match ratio
            skill_match_ratio = min(matched_skills_count / total_job_skills, 1.0)

            # Weighted combination: 70% vector + 30% skills
            composite_score = (0.7 * similarity_score) + (0.3 * skill_match_ratio)

            return min(composite_score, 1.0)

        except Exception as e:
            logger.error(f"Score calculation error: {e}")
            return 0.0

    @staticmethod
    def calculate_resume_quality(resume_text: str, resume_skills: List[str]) -> dict:
        """
        Calculate quality metrics for a resume.

        Returns breakdown of:
        - Text length score (0-100): longer is better up to a point
        - Skill count score (0-100): normalized against expected count
        - Completeness score (0-100): presence of technical and soft skills
        - Overall quality score (0-100): average of three

        Args:
            resume_text: Full resume parsed text
            resume_skills: List of extracted skills

        Returns:
            Dict with all quality scores
        """
        try:
            # Text length score (0-100)
            text_length = len(resume_text.strip())
            if text_length < RecommendationEngine.MIN_RESUME_LENGTH:
                text_length_score = (text_length / RecommendationEngine.MIN_RESUME_LENGTH) * 100
            else:
                # Bonus for longer resumes, capped at 100
                text_length_score = min(100, 100 + ((text_length - RecommendationEngine.MIN_RESUME_LENGTH) / 1000))
            text_length_score = min(text_length_score, 100)

            # Skill count score (0-100)
            skill_count = len(resume_skills)
            skill_count_score = min((skill_count / RecommendationEngine.EXPECTED_SKILL_COUNT) * 100, 100)

            # Completeness score (0-100): checks for both tech and soft skills
            resume_text_lower = resume_text.lower()
            has_tech_skills = len(resume_skills) > 0
            has_soft_skills = any(skill in resume_text_lower for skill in RecommendationEngine.SOFT_SKILLS_KEYWORDS)

            if has_tech_skills and has_soft_skills:
                completeness_score = 100.0
            elif has_tech_skills or has_soft_skills:
                completeness_score = 50.0
            else:
                completeness_score = 0.0

            # Overall quality: average of three
            overall_quality_score = (text_length_score + skill_count_score + completeness_score) / 3

            result = {
                "text_length_score": float(text_length_score),
                "skill_count_score": float(skill_count_score),
                "completeness_score": float(completeness_score),
                "overall_quality_score": float(overall_quality_score)
            }

            logger.debug(f"Resume quality: {result}")
            return result

        except Exception as e:
            logger.error(f"Resume quality calculation error: {e}")
            return {
                "text_length_score": 0.0,
                "skill_count_score": 0.0,
                "completeness_score": 0.0,
                "overall_quality_score": 0.0
            }

    @staticmethod
    async def recommend_jobs_for_resume(
        resume_id: str,
        resume_embedding,
        resume_skills: List[str],
        embeddings_manager,
        db: AsyncSession,
        min_similarity: float = 0.5,
        top_k: int = 20
    ) -> List[dict]:
        """
        Get top_k job recommendations for a resume.

        Algorithm:
        1. Use FAISS to find similar jobs (vector search)
        2. For each job, calculate skill match
        3. Combine vector similarity (70%) + skill match (30%)
        4. Filter by min_similarity threshold
        5. Return sorted by composite score

        Args:
            resume_id: UUID of the resume
            resume_embedding: 384-dimensional numpy array
            resume_skills: List of skills from resume
            embeddings_manager: EmbeddingsManager instance
            db: AsyncSession for database operations
            min_similarity: Filter threshold (0.0-1.0)
            top_k: Maximum results to return

        Returns:
            List of recommendation dicts with job details and scores
        """
        try:
            from app.models.models import Job as JobModel

            # Search for similar jobs
            similar_jobs = embeddings_manager.search_similar_jobs(resume_embedding, top_k=top_k * 2)

            if not similar_jobs:
                logger.warning(f"No similar jobs found for resume {resume_id}")
                return []

            recommendations = []

            for job_id, vector_similarity_score in similar_jobs:
                # Fetch job details
                job = await db.get(JobModel, job_id)
                if not job:
                    continue

                # Calculate skill match
                matched_skills, skill_gaps = RecommendationEngine.calculate_skill_match(
                    resume_skills, job.description
                )

                # Calculate composite score
                composite_score = RecommendationEngine.score_recommendation(
                    vector_similarity_score,
                    len(matched_skills),
                    len(matched_skills) + len(skill_gaps) if (len(matched_skills) + len(skill_gaps)) > 0 else 1
                )

                # Filter by threshold
                if composite_score < min_similarity:
                    continue

                recommendation = {
                    "job_id": job_id,
                    "job_title": job.title,
                    "job_description": job.description[:500],  # Truncate for response
                    "job_location": job.location,
                    "company_name": job.company_name,
                    "apply_url": job.apply_url,
                    "job_source": job.source,
                    "resume_id": resume_id,
                    "similarity_score": float(composite_score),
                    "vector_similarity": float(vector_similarity_score),
                    "matched_skills": matched_skills,
                    "skill_gaps": skill_gaps
                }
                recommendations.append(recommendation)

            # Sort by composite score descending
            recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Return top_k
            result = recommendations[:top_k]
            logger.info(f"Generated {len(result)} recommendations for resume {resume_id}")
            return result

        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return []

    @staticmethod
    async def recommend_resumes_for_job(
        job_id: str,
        job_embedding,
        job_skills: List[str],
        embeddings_manager,
        db: AsyncSession,
        min_similarity: float = 0.5,
        top_k: int = 20
    ) -> List[dict]:
        """
        Get top_k resume recommendations for a job.

        Args:
            job_id: UUID of the job
            job_embedding: 384-dimensional numpy array
            job_skills: List of skills required for the job
            embeddings_manager: EmbeddingsManager instance
            db: AsyncSession for database operations
            min_similarity: Filter threshold (0.0-1.0)
            top_k: Maximum results to return

        Returns:
            List of recommendation dicts with resume details and scores
        """
        try:
            from app.models.models import Resume as ResumeModel

            # Search for similar resumes
            similar_resumes = embeddings_manager.search_similar_resumes(job_embedding, top_k=top_k * 2)

            if not similar_resumes:
                logger.warning(f"No similar resumes found for job {job_id}")
                return []

            recommendations = []

            for resume_id, vector_similarity_score in similar_resumes:
                # Fetch resume details
                resume = await db.get(ResumeModel, resume_id)
                if not resume:
                    continue

                # Calculate resume quality
                quality = RecommendationEngine.calculate_resume_quality(
                    resume.parsed_text,
                    resume.skills if isinstance(resume.skills, list) else []
                )

                # Calculate skill match
                matched_skills, skill_gaps = RecommendationEngine.calculate_skill_match(
                    resume.skills if isinstance(resume.skills, list) else [],
                    ""  # We already have job_skills, no need to extract
                )

                # Calculate composite score
                composite_score = RecommendationEngine.score_recommendation(
                    vector_similarity_score,
                    len(matched_skills),
                    len(job_skills) if len(job_skills) > 0 else 1
                )

                # Filter by threshold
                if composite_score < min_similarity:
                    continue

                recommendation = {
                    "resume_id": resume_id,
                    "job_id": job_id,
                    "similarity_score": float(composite_score),
                    "vector_similarity": float(vector_similarity_score),
                    "resume_quality_score": quality["overall_quality_score"],
                    "matched_skills": matched_skills,
                    "skill_gaps": skill_gaps
                }
                recommendations.append(recommendation)

            # Sort by composite score descending
            recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Return top_k
            result = recommendations[:top_k]
            logger.info(f"Generated {len(result)} resume recommendations for job {job_id}")
            return result

        except Exception as e:
            logger.error(f"Resume recommendation error: {e}")
            return []
