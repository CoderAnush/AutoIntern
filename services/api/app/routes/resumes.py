"""Resume upload and management endpoints."""

from fastapi import APIRouter, UploadFile, File, status, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.schemas.resume import ResumeOut
from app.db.session import get_db
from app.models.models import Resume as ResumeModel
from app.core.config import settings
from app.core.security import get_current_user
from app.services.text_extractor import extract_text_from_file
from app.services.skill_extractor import extract_skills_from_text
from app.services.file_storage import MinIOStorage
from app.services.embeddings_service import EmbeddingsManager
import uuid
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize MinIO client
minio_client = MinIOStorage(
    endpoint=settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    bucket_name=settings.minio_bucket_name
)


@router.post("/resumes/upload", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a resume file (PDF, DOCX, or TXT).

    - Extracts text from file
    - Extracts skills using NLP
    - Stores file in MinIO
    - Saves resume metadata to PostgreSQL

    Protected endpoint requiring valid Authentication header.

    Returns:
        201 Created with resume metadata and extracted skills
    """
    try:
        # Extract user_id from authenticated user
        user_id = current_user.get("user_id")
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        allowed_types = {'pdf', 'docx', 'doc', 'txt'}

        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Supported: pdf, docx, txt"
            )

        # Read file content
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        if file_size_mb > settings.max_resume_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: {settings.max_resume_size_mb}MB"
            )

        # Extract text from file
        try:
            extracted_text = extract_text_from_file(file_content, file_extension)
        except ValueError as e:
            logger.error(f"Text extraction error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text: {str(e)}"
            )

        # Extract skills from text
        skills = extract_skills_from_text(extracted_text)

        # Upload file to MinIO
        try:
            storage_url = minio_client.upload_file(user_id, file_content, file.filename)
        except Exception as e:
            logger.error(f"MinIO upload error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )

        # Create Resume record in database
        resume_id = str(uuid.uuid4())
        resume = ResumeModel(
            id=resume_id,
            user_id=user_id,
            file_name=file.filename,
            parsed_text=extracted_text,
            skills=json.dumps(skills),  # Store as JSON
            storage_url=storage_url
        )

        db.add(resume)
        try:
            await db.commit()
            await db.refresh(resume)
        except Exception as e:
            logger.error(f"Database error: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save resume metadata"
            )

        # Auto-generate embedding for recommendation engine (non-blocking)
        try:
            embeddings_mgr = EmbeddingsManager()
            await embeddings_mgr.add_resume_embedding(resume_id, extracted_text, db)
            logger.info(f"Resume embedding generated successfully: {resume_id}")
        except Exception as e:
            # Log but don't fail - embedding can be generated later
            logger.warning(f"Failed to generate resume embedding: {e}. Resume will still be usable for manual queries.")

        logger.info(f"Resume uploaded successfully: {resume_id} for user {user_id}")

        # Queue resume upload confirmation email (Phase 7)
        try:
            from app.services.email_queue import EmailQueue
            from app.models.models import User
            from sqlalchemy import select

            # Get user email
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one()

            email_queue = EmailQueue(settings.redis_url)
            await email_queue.connect()

            await email_queue.enqueue_resume_upload_email(
                user_id=str(user_id),
                user_email=user.email,
                resume_name=file.filename,
                skills=skills
            )

            await email_queue.disconnect()
            logger.info(f"Resume upload confirmation email queued for: {user.email}")
        except Exception as e:
            logger.error(f"Failed to queue resume upload email for user {user_id}: {e}")
            # Don't fail resume upload if email queueing fails

        # Return response with parsed skills
        return ResumeOut(
            id=resume.id,
            user_id=resume.user_id,
            file_name=resume.file_name,
            parsed_text=None,  # Don't return full text to save bandwidth
            skills=skills,
            storage_url=resume.storage_url,
            created_at=resume.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in resume upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/resumes/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single resume by ID."""
    try:
        result = await db.execute(
            select(ResumeModel).where(ResumeModel.id == resume_id)
        )
        resume = result.scalars().first()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}"
            )

        # Parse skills from JSON
        skills = json.loads(resume.skills) if resume.skills else []

        return ResumeOut(
            id=resume.id,
            user_id=resume.user_id,
            file_name=resume.file_name,
            parsed_text=None,
            skills=skills,
            storage_url=resume.storage_url,
            created_at=resume.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume"
        )


@router.get("/resumes", response_model=list[ResumeOut])
async def list_resumes(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List resumes for the currently authenticated user with pagination."""
    try:
        user_id = current_user.get("user_id")
        result = await db.execute(
            select(ResumeModel)
            .where(ResumeModel.user_id == user_id)
            .limit(limit)
            .offset(offset)
        )
        resumes = result.scalars().all()

        response = []
        for resume in resumes:
            skills = json.loads(resume.skills) if resume.skills else []
            response.append(ResumeOut(
                id=resume.id,
                user_id=resume.user_id,
                file_name=resume.file_name,
                parsed_text=None,
                skills=skills,
                storage_url=resume.storage_url,
                created_at=resume.created_at
            ))

        return response

    except Exception as e:
        logger.error(f"Error listing resumes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list resumes"
        )


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a resume by ID."""
    try:
        result = await db.execute(
            select(ResumeModel).where(ResumeModel.id == resume_id)
        )
        resume = result.scalars().first()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}"
            )

        # Delete file from MinIO if storage_url exists
        if resume.storage_url:
            try:
                # Extract object name from URL
                # URL format: http://minio:9000/resumes/user/file.ext
                object_name = resume.storage_url.split('/', 3)[-1]
                minio_client.delete_file(object_name)
            except Exception as e:
                logger.warning(f"Failed to delete file from MinIO: {e}")

        # Delete from database
        await db.execute(
            delete(ResumeModel).where(ResumeModel.id == resume_id)
        )
        await db.commit()

        logger.info(f"Resume deleted: {resume_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume"
        )
