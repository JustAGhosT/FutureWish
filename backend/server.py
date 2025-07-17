from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from auth import verify_jwt, get_current_user, AuthUser, User


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="EngageMesh API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class UserProfile(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    points: int
    created_at: datetime
    last_login: datetime

class UserUpdate(BaseModel):
    name: Optional[str] = None

# Public routes
@api_router.get("/")
async def root():
    return {"message": "EngageMesh API - Feature Management Platform"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication routes
@api_router.get("/auth/me", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        points=current_user.points,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@api_router.put("/auth/me", response_model=UserProfile)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    update_data = {}
    if user_update.name is not None:
        update_data["name"] = user_update.name
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await db.users.find_one({"id": current_user.id})
        return UserProfile(**updated_user)
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        points=current_user.points,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

# Protected routes (examples)
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(
    input: StatusCheckCreate,
    current_user: AuthUser = Depends(verify_jwt)
):
    """Create a status check (protected route)"""
    status_dict = input.dict()
    status_dict["user_id"] = current_user.user_id
    status_obj = StatusCheck(**status_dict)
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks(current_user: AuthUser = Depends(verify_jwt)):
    """Get status checks for current user"""
    status_checks = await db.status_checks.find({"user_id": current_user.user_id}).to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.get("/users/leaderboard")
async def get_users_leaderboard(current_user: AuthUser = Depends(verify_jwt)):
    """Get users sorted by points (leaderboard)"""
    users = await db.users.find(
        {},
        {"id": 1, "name": 1, "email": 1, "points": 1, "avatar_url": 1}
    ).sort("points", -1).limit(10).to_list(10)
    
    return {"leaderboard": users}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
