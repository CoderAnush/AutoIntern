"""Skill extraction service using NLP."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Cache the spaCy model after first load
_nlp_model = None


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract technical skills from resume text using NLP.

    Args:
        text: Resume text to analyze

    Returns:
        List of extracted skills
    """
    global _nlp_model

    if not text or len(text.strip()) < 20:
        logger.warning("Text too short for skill extraction")
        return []

    try:
        # Load spaCy model once
        if _nlp_model is None:
            import spacy
            try:
                _nlp_model = spacy.load("en_core_web_md")
            except OSError:
                logger.warning("spaCy model not found. Downloading...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"])
                _nlp_model = spacy.load("en_core_web_md")

        # Extract skills using pattern matching + NER
        skills = set()

        # Predefined skill patterns (case-insensitive)
        skill_patterns = {
            "Programming Languages": {
                "python", "javascript", "java", "csharp", "c#", "cpp", "c++", "go", "rust",
                "php", "ruby", "swift", "kotlin", "scala", "r", "matlab"
            },
            "Web Frameworks": {
                "react", "vue", "angular", "django", "flask", "fastapi", "spring",
                "spring boot", "nodejs", "node.js", "express", "next.js", "nextjs"
            },
            "Cloud Platforms": {
                "aws", "azure", "gcp", "google cloud", "heroku", "vercel", "netlify"
            },
            "DevOps & Infrastructure": {
                "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
                "gitlab", "github", "git", "ci/cd", "cicd"
            },
            "Databases": {
                "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
                "dynamodb", "firebase", "oracle", "sql server", "cassandra"
            },
            "Data & ML": {
                "machine learning", "ml", "deep learning", "neural network",
                "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
                "pandas", "numpy", "spark", "hadoop", "data science", "nlp"
            },
            "Tools & Platforms": {
                "git", "github", "gitlab", "jira", "slack", "confluence",
                "jupyter", "jupyter notebook", "vscode", "vim", "linux"
            }
        }

        # Convert text to lowercase for matching
        text_lower = text.lower()

        # Match skill patterns
        for category, patterns in skill_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    skills.add(pattern.title())

        # Use spaCy NER for additional extraction (organizations might contain skills)
        doc = _nlp_model(text)
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "GPE"]:
                # Additional skill detection could go here
                pass

        # Return unique skills sorted alphabetically
        return sorted(list(skills)) if skills else []

    except Exception as e:
        logger.error(f"Skill extraction error: {e}")
        return []


def get_skill_categories(skills: List[str]) -> dict:
    """
    Categorize extracted skills.

    Args:
        skills: List of skill names

    Returns:
        Dict with skill categories
    """
    categories = {
        "programming": [],
        "frameworks": [],
        "cloud": [],
        "databases": [],
        "devops": [],
        "data_ml": [],
        "other": []
    }

    skill_mapping = {
        "programming": {"python", "javascript", "java", "csharp", "c#", "cpp", "c++", "go", "rust", "php", "ruby", "swift", "kotlin", "scala", "r", "matlab"},
        "frameworks": {"react", "vue", "angular", "django", "flask", "fastapi", "spring", "Spring", "nodejs", "node.js", "express", "next.js", "nextjs"},
        "cloud": {"aws", "azure", "gcp", "google cloud", "heroku", "vercel", "netlify"},
        "databases": {"sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb", "firebase", "oracle", "sql server", "cassandra"},
        "devops": {"docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins", "gitlab", "github", "git", "ci/cd", "cicd"},
        "data_ml": {"machine learning", "ml", "deep learning", "neural network", "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "spark", "hadoop", "data science", "nlp"}
    }

    for skill in skills:
        skill_lower = skill.lower()
        found = False
        for category, skills_set in skill_mapping.items():
            if skill_lower in skills_set:
                categories[category].append(skill)
                found = True
                break
        if not found:
            categories["other"].append(skill)

    return {k: v for k, v in categories.items() if v}
