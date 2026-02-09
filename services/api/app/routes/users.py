from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(payload: UserCreate):
    # Placeholder: create user, hash password
    return {"msg": "user created (stub)", "email": payload.email}
