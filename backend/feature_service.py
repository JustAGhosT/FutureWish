from motor.motor_asyncio import AsyncIOMotorClient
from models import Feature, Rating, RatingCreate, RatingType, PointsConfig
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class FeatureRatingService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.features_collection = db.features
        self.ratings_collection = db.ratings
        self.users_collection = db.users
    
    async def create_feature(self, feature_data: dict, created_by: str) -> Feature:
        """Create a new feature (admin only)"""
        feature_data["created_by"] = created_by
        feature = Feature(**feature_data)
        await self.features_collection.insert_one(feature.dict())
        return feature
    
    async def get_features(self, category: Optional[str] = None, status: Optional[str] = None, 
                          skip: int = 0, limit: int = 20) -> List[Feature]:
        """Get list of features with optional filtering"""
        query = {}
        if category:
            query["category"] = category
        if status:
            query["status"] = status
        
        cursor = self.features_collection.find(query).skip(skip).limit(limit)
        features = []
        async for feature_doc in cursor:
            features.append(Feature(**feature_doc))
        return features
    
    async def get_feature_by_id(self, feature_id: str) -> Optional[Feature]:
        """Get a single feature by ID"""
        feature_doc = await self.features_collection.find_one({"id": feature_id})
        if feature_doc:
            return Feature(**feature_doc)
        return None
    
    async def get_user_rating_for_feature(self, user_id: str, feature_id: str) -> Optional[Rating]:
        """Get user's existing rating for a feature"""
        rating_doc = await self.ratings_collection.find_one({
            "user_id": user_id,
            "feature_id": feature_id
        })
        if rating_doc:
            return Rating(**rating_doc)
        return None
    
    async def check_daily_first_rating(self, user_id: str) -> bool:
        """Check if this is user's first rating today"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_rating = await self.ratings_collection.find_one({
            "user_id": user_id,
            "created_at": {"$gte": today_start}
        })
        return today_rating is None
    
    async def create_rating(self, user_id: str, feature_id: str, rating_data: RatingCreate) -> Dict:
        """Create a new rating for a feature"""
        # Check if feature exists
        feature = await self.get_feature_by_id(feature_id)
        if not feature:
            raise ValueError("Feature not found")
        
        # Check if user already rated this feature
        existing_rating = await self.get_user_rating_for_feature(user_id, feature_id)
        if existing_rating:
            raise ValueError("User has already rated this feature")
        
        # Check if this is user's first rating today
        is_daily_first = await self.check_daily_first_rating(user_id)
        
        # Calculate points
        has_feedback = bool(rating_data.feedback and rating_data.feedback.strip())
        points = PointsConfig.calculate_points(
            rating_data.rating_type, 
            has_feedback, 
            is_daily_first
        )
        
        # Create rating
        rating = Rating(
            user_id=user_id,
            feature_id=feature_id,
            rating_type=rating_data.rating_type,
            rating_value=rating_data.rating_value,
            feedback=rating_data.feedback,
            points_earned=points
        )
        
        # Save rating
        await self.ratings_collection.insert_one(rating.dict())
        
        # Update user points
        await self.users_collection.update_one(
            {"id": user_id},
            {"$inc": {"points": points}}
        )
        
        # Update feature statistics
        await self.update_feature_stats(feature_id)
        
        return {
            "rating": rating,
            "points_earned": points,
            "is_daily_first": is_daily_first
        }
    
    async def update_feature_stats(self, feature_id: str):
        """Update feature rating statistics"""
        # Get all ratings for this feature
        ratings_cursor = self.ratings_collection.find({"feature_id": feature_id})
        ratings = []
        async for rating_doc in ratings_cursor:
            ratings.append(Rating(**rating_doc))
        
        # Calculate stats
        upvotes = sum(1 for r in ratings if r.rating_type == RatingType.UPVOTE)
        downvotes = sum(1 for r in ratings if r.rating_type == RatingType.DOWNVOTE)
        
        star_ratings = [r.rating_value for r in ratings 
                       if r.rating_type == RatingType.STAR and r.rating_value is not None]
        average_star_rating = sum(star_ratings) / len(star_ratings) if star_ratings else 0.0
        
        feedback_count = sum(1 for r in ratings if r.feedback and r.feedback.strip())
        
        # Update feature
        await self.features_collection.update_one(
            {"id": feature_id},
            {
                "$set": {
                    "upvotes": upvotes,
                    "downvotes": downvotes,
                    "average_star_rating": average_star_rating,
                    "total_ratings": len(ratings),
                    "feedback_count": feedback_count,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def get_feature_ratings(self, feature_id: str, limit: int = 10) -> List[Rating]:
        """Get recent ratings for a feature"""
        cursor = self.ratings_collection.find({"feature_id": feature_id}) \
                                      .sort("created_at", -1) \
                                      .limit(limit)
        ratings = []
        async for rating_doc in cursor:
            ratings.append(Rating(**rating_doc))
        return ratings
    
    async def get_user_ratings(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Rating]:
        """Get user's rating history"""
        cursor = self.ratings_collection.find({"user_id": user_id}) \
                                      .sort("created_at", -1) \
                                      .skip(skip) \
                                      .limit(limit)
        ratings = []
        async for rating_doc in cursor:
            ratings.append(Rating(**rating_doc))
        return ratings
    
    async def get_rating_stats(self, feature_id: str) -> Dict:
        """Get comprehensive rating statistics for a feature"""
        feature = await self.get_feature_by_id(feature_id)
        if not feature:
            raise ValueError("Feature not found")
        
        recent_ratings = await self.get_feature_ratings(feature_id, limit=5)
        
        # Get user names for recent ratings
        recent_with_names = []
        for rating in recent_ratings:
            user = await self.users_collection.find_one({"id": rating.user_id})
            user_name = user.get("name") if user else "Anonymous"
            recent_with_names.append({
                **rating.dict(),
                "user_name": user_name
            })
        
        return {
            "total_ratings": feature.total_ratings,
            "upvotes": feature.upvotes,
            "downvotes": feature.downvotes,
            "average_star_rating": feature.average_star_rating,
            "feedback_count": feature.feedback_count,
            "recent_feedback": recent_with_names
        }
    
    async def delete_rating(self, user_id: str, feature_id: str) -> bool:
        """Delete a user's rating (admin only or user's own rating)"""
        rating = await self.get_user_rating_for_feature(user_id, feature_id)
        if not rating:
            return False
        
        # Remove points from user
        await self.users_collection.update_one(
            {"id": user_id},
            {"$inc": {"points": -rating.points_earned}}
        )
        
        # Delete rating
        await self.ratings_collection.delete_one({
            "user_id": user_id,
            "feature_id": feature_id
        })
        
        # Update feature stats
        await self.update_feature_stats(feature_id)
        
        return True