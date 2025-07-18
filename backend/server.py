from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
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
from models import (
    Feature, FeatureCreate, FeatureUpdate, Rating, RatingCreate, 
    RatingResponse, FeatureWithRatings, RatingStats, FeatureCategory, 
    FeatureStatus, RatingType, PointsConfig
)
from request_models import (
    FeatureRequest, FeatureRequestCreate, FeatureRequestUpdate, AdminRequestUpdate,
    RequestVote, RequestVoteCreate, RequestComment, RequestCommentCreate,
    RequestStatus, RequestPriority, RequestType, RequestPointsConfig,
    FeatureRequestResponse, RequestCommentResponse, RequestAnalytics
)
from feature_service import FeatureRatingService
from request_service import FeatureRequestService


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
feature_service = FeatureRatingService(db)
request_service = FeatureRequestService(db)

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

# Feature Management Routes
@api_router.get("/features", response_model=List[Feature])
async def get_features(
    category: Optional[FeatureCategory] = None,
    status: Optional[FeatureStatus] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: AuthUser = Depends(verify_jwt)
):
    """Get list of features"""
    try:
        features = await feature_service.get_features(
            category=category.value if category else None,
            status=status.value if status else None,
            skip=skip,
            limit=limit
        )
        return features
    except Exception as e:
        logging.error(f"Error getting features: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving features")

@api_router.get("/features/{feature_id}", response_model=FeatureWithRatings)
async def get_feature_detail(
    feature_id: str,
    current_user: AuthUser = Depends(verify_jwt)
):
    """Get detailed feature information with user's rating"""
    try:
        feature = await feature_service.get_feature_by_id(feature_id)
        if not feature:
            raise HTTPException(status_code=404, detail="Feature not found")
        
        user_rating = await feature_service.get_user_rating_for_feature(
            current_user.user_id, feature_id
        )
        
        return FeatureWithRatings(
            feature=feature,
            user_rating=user_rating,
            can_rate=user_rating is None
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting feature detail: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving feature")

@api_router.post("/features", response_model=Feature)
async def create_feature(
    feature_data: FeatureCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new feature (admin only for now)"""
    try:
        feature = await feature_service.create_feature(
            feature_data.dict(),
            current_user.id
        )
        return feature
    except Exception as e:
        logging.error(f"Error creating feature: {e}")
        raise HTTPException(status_code=500, detail="Error creating feature")

@api_router.post("/features/{feature_id}/rate")
async def rate_feature(
    feature_id: str,
    rating_data: RatingCreate,
    current_user: AuthUser = Depends(verify_jwt)
):
    """Rate a feature"""
    try:
        result = await feature_service.create_rating(
            current_user.user_id,
            feature_id,
            rating_data
        )
        
        return {
            "message": "Rating submitted successfully",
            "rating": result["rating"],
            "points_earned": result["points_earned"],
            "is_daily_first": result["is_daily_first"],
            "bonus_applied": result["is_daily_first"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error rating feature: {e}")
        raise HTTPException(status_code=500, detail="Error submitting rating")

@api_router.get("/features/{feature_id}/ratings", response_model=List[RatingResponse])
async def get_feature_ratings(
    feature_id: str,
    limit: int = 10,
    current_user: AuthUser = Depends(verify_jwt)
):
    """Get ratings for a feature"""
    try:
        ratings = await feature_service.get_feature_ratings(feature_id, limit)
        
        # Get user names for ratings
        ratings_with_names = []
        for rating in ratings:
            user = await db.users.find_one({"id": rating.user_id})
            user_name = user.get("name") if user else "Anonymous"
            ratings_with_names.append(RatingResponse(
                **rating.dict(),
                user_name=user_name
            ))
        
        return ratings_with_names
    except Exception as e:
        logging.error(f"Error getting feature ratings: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving ratings")

@api_router.get("/features/{feature_id}/stats", response_model=RatingStats)
async def get_feature_rating_stats(
    feature_id: str,
    current_user: AuthUser = Depends(verify_jwt)
):
    """Get comprehensive rating statistics for a feature"""
    try:
        stats = await feature_service.get_rating_stats(feature_id)
        return RatingStats(**stats)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting rating stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")

@api_router.get("/users/ratings", response_model=List[Rating])
async def get_user_ratings(
    skip: int = 0,
    limit: int = 20,
    current_user: AuthUser = Depends(verify_jwt)
):
    """Get current user's rating history"""
    try:
        ratings = await feature_service.get_user_ratings(
            current_user.user_id, skip, limit
        )
        return ratings
    except Exception as e:
        logging.error(f"Error getting user ratings: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving ratings")

@api_router.delete("/features/{feature_id}/rate")
async def delete_rating(
    feature_id: str,
    current_user: AuthUser = Depends(verify_jwt)
):
    """Delete user's rating for a feature"""
    try:
        success = await feature_service.delete_rating(current_user.user_id, feature_id)
        if not success:
            raise HTTPException(status_code=404, detail="Rating not found")
        
        return {"message": "Rating deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting rating: {e}")
        raise HTTPException(status_code=500, detail="Error deleting rating")

# Legacy routes (keep for backward compatibility)
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

# Points information endpoint
@api_router.get("/points/info")
async def get_points_info(current_user: AuthUser = Depends(verify_jwt)):
    """Get information about the points system"""
    return {
        "points_system": {
            "upvote_downvote": PointsConfig.UPVOTE_DOWNVOTE_POINTS,
            "star_rating": PointsConfig.STAR_RATING_POINTS,
            "feedback": PointsConfig.FEEDBACK_POINTS,
            "daily_bonus": PointsConfig.DAILY_RATING_BONUS
        },
        "description": "Earn points by rating features! Get bonus points for your first rating each day and extra points for leaving feedback."
    }

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
