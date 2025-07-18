from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    DUPLICATE = "duplicate"

class RequestPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RequestType(str, Enum):
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    BUG_FIX = "bug_fix"
    INTEGRATION = "integration"

# Feature Request Models
class FeatureRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: str  # Using FeatureCategory from existing models
    request_type: RequestType = RequestType.FEATURE
    priority: RequestPriority = RequestPriority.MEDIUM
    status: RequestStatus = RequestStatus.PENDING
    
    # User information
    submitted_by: str  # user_id
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    points_spent: int = 0
    
    # Request details
    use_case: Optional[str] = None
    expected_behavior: Optional[str] = None
    current_workaround: Optional[str] = None
    
    # Voting and engagement
    votes: int = 0
    comments_count: int = 0
    
    # Admin fields
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Implementation tracking
    implemented_in_feature_id: Optional[str] = None
    implementation_date: Optional[datetime] = None
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FeatureRequestCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    category: str
    request_type: RequestType = RequestType.FEATURE
    priority: RequestPriority = RequestPriority.MEDIUM
    use_case: Optional[str] = Field(None, max_length=1000)
    expected_behavior: Optional[str] = Field(None, max_length=1000)
    current_workaround: Optional[str] = Field(None, max_length=1000)

class FeatureRequestUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=2000)
    category: Optional[str] = None
    request_type: Optional[RequestType] = None
    priority: Optional[RequestPriority] = None
    use_case: Optional[str] = Field(None, max_length=1000)
    expected_behavior: Optional[str] = Field(None, max_length=1000)
    current_workaround: Optional[str] = Field(None, max_length=1000)

class AdminRequestUpdate(BaseModel):
    status: Optional[RequestStatus] = None
    priority: Optional[RequestPriority] = None
    admin_notes: Optional[str] = Field(None, max_length=1000)
    rejection_reason: Optional[str] = Field(None, max_length=500)

class FeatureRequestResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    request_type: RequestType
    priority: RequestPriority
    status: RequestStatus
    submitted_by: str
    submitted_at: datetime
    points_spent: int
    use_case: Optional[str]
    expected_behavior: Optional[str]
    current_workaround: Optional[str]
    votes: int
    comments_count: int
    
    # Admin fields (only visible to admins)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # User information
    user_name: Optional[str] = None
    user_email: Optional[str] = None

class RequestVote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    request_id: str
    points_spent: int
    vote_weight: int = 1  # Can be increased for premium users
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RequestVoteCreate(BaseModel):
    points_spent: int = Field(..., ge=1, le=50)

class RequestComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    request_id: str
    comment: str = Field(..., min_length=1, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RequestCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)

class RequestCommentResponse(BaseModel):
    id: str
    user_id: str
    request_id: str
    comment: str
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None

# Request Analytics
class RequestAnalytics(BaseModel):
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    implemented_requests: int
    
    requests_by_category: dict
    requests_by_priority: dict
    requests_by_type: dict
    
    top_contributors: List[dict]
    recent_activity: List[dict]

# Points Configuration for Requests
class RequestPointsConfig:
    # Points required to submit different types of requests
    FEATURE_REQUEST_COST = 25
    ENHANCEMENT_REQUEST_COST = 15
    BUG_FIX_REQUEST_COST = 10
    INTEGRATION_REQUEST_COST = 35
    
    # Points required to vote on requests
    VOTE_COST_MIN = 1
    VOTE_COST_MAX = 10
    
    # Points refunded when request is rejected
    REFUND_PERCENTAGE = 0.8  # 80% refund on rejection
    
    # Premium multipliers
    PREMIUM_COST_MULTIPLIER = 0.5  # Premium users pay 50% less
    
    @classmethod
    def get_request_cost(cls, request_type: RequestType, is_premium: bool = False) -> int:
        costs = {
            RequestType.FEATURE: cls.FEATURE_REQUEST_COST,
            RequestType.ENHANCEMENT: cls.ENHANCEMENT_REQUEST_COST,
            RequestType.BUG_FIX: cls.BUG_FIX_REQUEST_COST,
            RequestType.INTEGRATION: cls.INTEGRATION_REQUEST_COST
        }
        base_cost = costs.get(request_type, cls.FEATURE_REQUEST_COST)
        
        if is_premium:
            base_cost = int(base_cost * cls.PREMIUM_COST_MULTIPLIER)
        
        return base_cost
    
    @classmethod
    def calculate_refund(cls, points_spent: int) -> int:
        return int(points_spent * cls.REFUND_PERCENTAGE)