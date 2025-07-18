from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
import uuid

class FeatureStatus(str, Enum):
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    IMPLEMENTED = "implemented"
    ARCHIVED = "archived"

class FeatureCategory(str, Enum):
    UI_UX = "ui_ux"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    SECURITY = "security"
    MOBILE = "mobile"
    API = "api"
    OTHER = "other"

class RatingType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    STAR = "star"
    FEEDBACK = "feedback"

# Feature Models
class Feature(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: FeatureCategory
    status: FeatureStatus = FeatureStatus.ACTIVE
    created_by: str  # admin user id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Rating stats
    upvotes: int = 0
    downvotes: int = 0
    average_star_rating: float = 0.0
    total_ratings: int = 0
    feedback_count: int = 0

class FeatureCreate(BaseModel):
    title: str
    description: str
    category: FeatureCategory
    status: FeatureStatus = FeatureStatus.ACTIVE

class FeatureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[FeatureCategory] = None
    status: Optional[FeatureStatus] = None

# Rating Models
class Rating(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    feature_id: str
    rating_type: RatingType
    rating_value: Optional[int] = None  # 1-5 for stars, 1 for upvote, -1 for downvote
    feedback: Optional[str] = None
    points_earned: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RatingCreate(BaseModel):
    rating_type: RatingType
    rating_value: Optional[int] = None
    feedback: Optional[str] = None

class RatingResponse(BaseModel):
    id: str
    user_id: str
    feature_id: str
    rating_type: RatingType
    rating_value: Optional[int] = None
    feedback: Optional[str] = None
    points_earned: int
    created_at: datetime
    user_name: Optional[str] = None

# Response Models
class FeatureWithRatings(BaseModel):
    feature: Feature
    user_rating: Optional[Rating] = None
    can_rate: bool = True

class RatingStats(BaseModel):
    total_ratings: int
    upvotes: int
    downvotes: int
    average_star_rating: float
    feedback_count: int
    recent_feedback: List[RatingResponse]

# Points Configuration
class PointsConfig:
    UPVOTE_DOWNVOTE_POINTS = 5
    STAR_RATING_POINTS = 10
    FEEDBACK_POINTS = 15
    DAILY_RATING_BONUS = 5  # Extra points for first rating of the day
    
    @classmethod
    def calculate_points(cls, rating_type: RatingType, has_feedback: bool = False, is_daily_first: bool = False) -> int:
        base_points = 0
        
        if rating_type == RatingType.UPVOTE or rating_type == RatingType.DOWNVOTE:
            base_points = cls.UPVOTE_DOWNVOTE_POINTS
        elif rating_type == RatingType.STAR:
            base_points = cls.STAR_RATING_POINTS
        elif rating_type == RatingType.FEEDBACK:
            base_points = cls.FEEDBACK_POINTS
        
        if has_feedback and rating_type != RatingType.FEEDBACK:
            base_points += cls.FEEDBACK_POINTS
        
        if is_daily_first:
            base_points += cls.DAILY_RATING_BONUS
            
        return base_points