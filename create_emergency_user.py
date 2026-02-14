import asyncio
import sys
import logging
from uuid import uuid4

# Add services/api to path
sys.path.insert(0, "services/api")

from app.db.session import AsyncSessionLocal
from app.services.auth_service import AuthService
from app.models.models import User
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_emergency_user():
    print("🚀 Creating Emergency User...")
    
    async with AsyncSessionLocal() as db:
        try:
            email = "emergency@autointern.com"
            password = "EmergencyPass123!"
            
            # Check if exists
            result = await db.execute(select(User).where(User.email == email))
            existing = result.scalars().first()
            if existing:
                print(f"⚠️ User {email} already exists. Updating password...")
                existing.password_hash = AuthService.hash_password(password)
                existing.failed_login_attempts = 0 # Unlock if locked
                await db.commit()
                print(f"✅ Password updated and account unlocked for {email}")
                return True

            # Create new
            password_hash = AuthService.hash_password(password)
            user = User(
                id=str(uuid4()),
                email=email,
                password_hash=password_hash,
                is_active=True,
                failed_login_attempts=0
            )
            
            db.add(user)
            await db.commit()
            print(f"✅ Created user: {email}")
            print(f"🔑 Password: {password}")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    asyncio.run(create_emergency_user())
