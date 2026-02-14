from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
import uuid

from app.db.session import get_db
from app.models.models import Application as ApplicationModel
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationUpdate
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    application: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job application record."""
    try:
        user_id = current_user.get("user_id")
        
        # Handle UUID conversion for both string and UUID types
        if isinstance(user_id, str):
            user_uuid = user_id
        else:
            user_uuid = str(user_id)
        
        new_application = ApplicationModel(
            id=str(uuid.uuid4()),
            user_id=user_uuid,
            **application.dict()
        )
        
        db.add(new_application)
        await db.commit()
        await db.refresh(new_application)
        return new_application
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to create application: {str(e)}"
        )

@router.get("/", response_model=List[ApplicationOut])
async def list_applications(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all applications for the current user."""
    user_id = current_user.get("user_id")
    
    result = await db.execute(
        select(ApplicationModel)
        .where(ApplicationModel.user_id == user_id)
        .order_by(desc(ApplicationModel.applied_at))
    )
    return result.scalars().all()

@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    update_data: ApplicationUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an application status or notes."""
    user_id = current_user.get("user_id")
    
    result = await db.execute(
        select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == user_id
        )
    )
    application = result.scalars().first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if update_data.status:
        application.status = update_data.status
    if update_data.notes:
        application.notes = update_data.notes
        
    await db.commit()
    await db.refresh(application)
    return application

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an application record."""
    user_id = current_user.get("user_id")
    
    result = await db.execute(
        select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == user_id
        )
    )
    application = result.scalars().first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
        
    await db.delete(application)
    await db.commit()
    return None
