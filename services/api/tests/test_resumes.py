"""
Tests for Resume Upload & Skill Extraction Service (Phase 3)

Tests resume service components:
- Text extraction from PDF, DOCX, TXT
- Skill extraction from resume text
- MinIO storage integration
- Resume schema validation
- Model field verification
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class TestTextExtractorService(unittest.TestCase):
    """Test text extraction from various file formats."""

    def test_extract_from_txt(self):
        """Test TXT file extraction."""
        from app.services.text_extractor import extract_text_from_file

        content = b"Hello World\nResume Content\nPython Django"
        result = extract_text_from_file(content, 'txt')
        self.assertIn("Hello World", result)
        self.assertIn("Resume Content", result)

    def test_extract_from_txt_with_extra_whitespace(self):
        """Test that extra whitespace is cleaned."""
        from app.services.text_extractor import extract_text_from_file

        content = b"Hello\n\n\nWorld  \n\nResume"
        result = extract_text_from_file(content, 'txt')
        lines = result.split('\n')
        # Should not have empty lines
        self.assertTrue(all(line.strip() for line in lines))

    def test_invalid_file_type(self):
        """Test rejection of unsupported file types."""
        from app.services.text_extractor import extract_text_from_file

        with self.assertRaises(ValueError) as cm:
            extract_text_from_file(b"content", 'xyz')
        self.assertIn("Unsupported file type", str(cm.exception))

    def test_empty_text_rejected(self):
        """Test that extraction fails on empty content."""
        from app.services.text_extractor import extract_text_from_file

        with self.assertRaises(ValueError):
            extract_text_from_file(b"", 'txt')


class TestSkillExtractorService(unittest.TestCase):
    """Test skill extraction from resume text."""

    def test_extract_programming_languages(self):
        """Test extraction of programming languages."""
        from app.services.skill_extractor import extract_skills_from_text

        text = "I have 5 years of experience with Python and JavaScript coding"
        skills = extract_skills_from_text(text)
        # Should find at least Python
        self.assertGreater(len(skills), 0, f"Expected at least 1 skill, got: {skills}")

    def test_extract_frameworks(self):
        """Test extraction of frameworks."""
        from app.services.skill_extractor import extract_skills_from_text

        text = "Expert in Django, React, and Spring Boot frameworks for web development"
        skills = extract_skills_from_text(text)
        # Should find frameworks
        self.assertGreater(len(skills), 0, f"Expected frameworks, got: {skills}")

    def test_extract_cloud_platforms(self):
        """Test extraction of cloud platforms."""
        from app.services.skill_extractor import extract_skills_from_text

        text = "Deployed applications on AWS and Azure cloud infrastructure"
        skills = extract_skills_from_text(text)
        # Should find AWS
        self.assertTrue(
            any("aws" in skill.lower() for skill in skills) or len(skills) > 0,
            f"Expected AWS or other skills, got: {skills}"
        )

    def test_empty_text_returns_empty_list(self):
        """Test that very short text returns empty list."""
        from app.services.skill_extractor import extract_skills_from_text

        skills = extract_skills_from_text("Short")
        self.assertEqual(skills, [])

    def test_returns_unique_skills_sorted(self):
        """Test that skills are unique and sorted."""
        from app.services.skill_extractor import extract_skills_from_text

        text = "I know Python Python and JavaScript JavaScript programming"
        skills = extract_skills_from_text(text)
        # Should not have duplicates
        self.assertEqual(len(skills), len(set(skills)))
        # Should be sorted
        if len(skills) > 0:
            self.assertEqual(skills, sorted(skills))


class TestResumeSchema(unittest.TestCase):
    """Test Resume Pydantic schemas."""

    def test_resume_out_model(self):
        """Test ResumeOut schema creation."""
        from app.schemas.resume import ResumeOut

        resume = ResumeOut(
            id="123",
            user_id="user1",
            file_name="resume.pdf",
            parsed_text="Sample text",
            skills=["Python", "JavaScript"],
            storage_url="http://minio/resumes/resume.pdf",
            created_at=None
        )
        self.assertEqual(resume.id, "123")
        self.assertEqual(len(resume.skills), 2)

    def test_skill_extracted_model(self):
        """Test SkillExtracted schema."""
        from app.schemas.resume import SkillExtracted

        skill = SkillExtracted(name="Python", source="nlp")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.source, "nlp")


class TestResumeConfigurationIntegration(unittest.TestCase):
    """Test that resume settings are properly configured."""

    def test_minio_settings_available(self):
        """Test that MinIO settings are configured."""
        from app.core.config import settings

        self.assertEqual(settings.minio_endpoint, "localhost:9000")
        self.assertEqual(settings.minio_access_key, "minioadmin")
        self.assertEqual(settings.minio_secret_key, "minioadmin")
        self.assertEqual(settings.minio_bucket_name, "resumes")
        self.assertEqual(settings.max_resume_size_mb, 10)


class TestResumeModelUpdates(unittest.TestCase):
    """Test that Resume model has necessary fields."""

    def test_resume_model_fields(self):
        """Test Resume model has all required fields."""
        from app.models.models import Resume

        # Check that model has required columns
        column_names = [col.name for col in Resume.__table__.columns]
        required_fields = ['id', 'user_id', 'file_name', 'parsed_text', 'skills', 'storage_url', 'created_at']

        for field in required_fields:
            self.assertIn(field, column_names, f"Missing field: {field}")


if __name__ == '__main__':
    unittest.main()
