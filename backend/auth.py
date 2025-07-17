from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# JWT Authentication
bearer_scheme = HTTPBearer(auto_error=False)

class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    last_login: datetime = datetime.utcnow()
    points: int = 0

class AuthUser(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

async def get_database():
    """Get database connection"""
    from server import db
    return db

async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncIOMotorClient = Depends(get_database)
) -> AuthUser:
    """Verify JWT token and return user information"""
    if not credentials or credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("SUPABASE_JWT_SECRET"),
            algorithms=["HS256"],
            audience="authenticated",
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user metadata from token
        user_metadata = payload.get("user_metadata", {})
        app_metadata = payload.get("app_metadata", {})
        
        # Sync user to MongoDB
        user_data = {
            "id": user_id,
            "email": email,
            "name": user_metadata.get("name") or user_metadata.get("full_name"),
            "avatar_url": user_metadata.get("avatar_url"),
            "provider": app_metadata.get("provider"),
            "last_login": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Update or create user in MongoDB
        result = await db.users.find_one({"id": user_id})
        if result:
            # Update existing user
            await db.users.update_one(
                {"id": user_id},
                {"$set": user_data}
            )
        else:
            # Create new user with default points
            user_data["points"] = 100  # Starting points
            user_data["created_at"] = datetime.utcnow()
            await db.users.insert_one(user_data)
        
        return AuthUser(
            user_id=user_id,
            email=email,
            name=user_data.get("name"),
            avatar_url=user_data.get("avatar_url")
        )
        
    except JWTError as e:
        logger.error(f"JWT verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

async def get_current_user(
    current_user: AuthUser = Depends(verify_jwt),
    db: AsyncIOMotorClient = Depends(get_database)
) -> User:
    """Get full user data from database"""
    try:
        user_data = await db.users.find_one({"id": current_user.user_id})
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return User(**user_data)
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user data"
        )

# Optional: middleware for user points and gamification
async def get_user_with_points(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get user with points validation"""
    return current_user