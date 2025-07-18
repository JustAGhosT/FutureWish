from motor.motor_asyncio import AsyncIOMotorClient
from request_models import (
    FeatureRequest, FeatureRequestCreate, FeatureRequestUpdate, AdminRequestUpdate,
    RequestVote, RequestVoteCreate, RequestComment, RequestCommentCreate,
    RequestStatus, RequestPriority, RequestType, RequestPointsConfig,
    FeatureRequestResponse, RequestCommentResponse, RequestAnalytics
)
from models import FeatureCategory
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class FeatureRequestService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.requests_collection = db.feature_requests
        self.votes_collection = db.request_votes
        self.comments_collection = db.request_comments
        self.users_collection = db.users
        self.features_collection = db.features
    
    async def create_request(self, request_data: FeatureRequestCreate, user_id: str) -> Dict:
        """Create a new feature request"""
        try:
            # Check if user has enough points
            user = await self.users_collection.find_one({"id": user_id})
            if not user:
                raise ValueError("User not found")
            
            # Calculate request cost
            request_cost = RequestPointsConfig.get_request_cost(request_data.request_type)
            
            if user.get("points", 0) < request_cost:
                raise ValueError(f"Insufficient points. Required: {request_cost}, Available: {user.get('points', 0)}")
            
            # Check for duplicate requests (similar title from same user)
            existing_request = await self.requests_collection.find_one({
                "submitted_by": user_id,
                "title": {"$regex": f"^{request_data.title.strip()}$", "$options": "i"},
                "status": {"$ne": RequestStatus.REJECTED}
            })
            
            if existing_request:
                raise ValueError("You have already submitted a similar request")
            
            # Create the request
            request = FeatureRequest(
                **request_data.dict(),
                submitted_by=user_id,
                points_spent=request_cost
            )
            
            # Insert request
            await self.requests_collection.insert_one(request.dict())
            
            # Deduct points from user
            await self.users_collection.update_one(
                {"id": user_id},
                {"$inc": {"points": -request_cost}}
            )
            
            return {
                "request": request,
                "points_spent": request_cost,
                "remaining_points": user.get("points", 0) - request_cost
            }
            
        except Exception as e:
            logger.error(f"Error creating request: {e}")
            raise
    
    async def get_requests(self, status: Optional[RequestStatus] = None, 
                          category: Optional[str] = None, 
                          request_type: Optional[RequestType] = None,
                          priority: Optional[RequestPriority] = None,
                          user_id: Optional[str] = None,
                          skip: int = 0, limit: int = 20) -> List[FeatureRequestResponse]:
        """Get feature requests with filtering"""
        try:
            query = {}
            
            if status:
                query["status"] = status
            if category:
                query["category"] = category
            if request_type:
                query["request_type"] = request_type
            if priority:
                query["priority"] = priority
            if user_id:
                query["submitted_by"] = user_id
            
            # Get requests with pagination
            cursor = self.requests_collection.find(query) \
                                            .sort("submitted_at", -1) \
                                            .skip(skip) \
                                            .limit(limit)
            
            requests = []
            async for request_doc in cursor:
                # Get user information
                user = await self.users_collection.find_one({"id": request_doc["submitted_by"]})
                
                request_response = FeatureRequestResponse(
                    **request_doc,
                    user_name=user.get("name") if user else "Unknown",
                    user_email=user.get("email") if user else None
                )
                requests.append(request_response)
            
            return requests
            
        except Exception as e:
            logger.error(f"Error getting requests: {e}")
            raise
    
    async def get_request_by_id(self, request_id: str) -> Optional[FeatureRequestResponse]:
        """Get a single request by ID"""
        try:
            request_doc = await self.requests_collection.find_one({"id": request_id})
            if not request_doc:
                return None
            
            # Get user information
            user = await self.users_collection.find_one({"id": request_doc["submitted_by"]})
            
            return FeatureRequestResponse(
                **request_doc,
                user_name=user.get("name") if user else "Unknown",
                user_email=user.get("email") if user else None
            )
            
        except Exception as e:
            logger.error(f"Error getting request by ID: {e}")
            raise
    
    async def update_request(self, request_id: str, user_id: str, 
                           update_data: FeatureRequestUpdate) -> Optional[FeatureRequestResponse]:
        """Update user's own request (only if pending)"""
        try:
            # Check if request exists and belongs to user
            request = await self.requests_collection.find_one({
                "id": request_id,
                "submitted_by": user_id,
                "status": RequestStatus.PENDING
            })
            
            if not request:
                raise ValueError("Request not found or cannot be updated")
            
            # Update request
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()
            
            await self.requests_collection.update_one(
                {"id": request_id},
                {"$set": update_dict}
            )
            
            return await self.get_request_by_id(request_id)
            
        except Exception as e:
            logger.error(f"Error updating request: {e}")
            raise
    
    async def admin_update_request(self, request_id: str, admin_id: str, 
                                 update_data: AdminRequestUpdate) -> Optional[FeatureRequestResponse]:
        """Admin update request status"""
        try:
            request = await self.requests_collection.find_one({"id": request_id})
            if not request:
                raise ValueError("Request not found")
            
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            update_dict["reviewed_by"] = admin_id
            update_dict["reviewed_at"] = datetime.utcnow()
            update_dict["updated_at"] = datetime.utcnow()
            
            # Handle point refund for rejected requests
            if update_data.status == RequestStatus.REJECTED:
                refund_amount = RequestPointsConfig.calculate_refund(request["points_spent"])
                await self.users_collection.update_one(
                    {"id": request["submitted_by"]},
                    {"$inc": {"points": refund_amount}}
                )
            
            await self.requests_collection.update_one(
                {"id": request_id},
                {"$set": update_dict}
            )
            
            return await self.get_request_by_id(request_id)
            
        except Exception as e:
            logger.error(f"Error admin updating request: {e}")
            raise
    
    async def vote_on_request(self, request_id: str, user_id: str, 
                            vote_data: RequestVoteCreate) -> Dict:
        """Vote on a feature request"""
        try:
            # Check if request exists and is approved
            request = await self.requests_collection.find_one({
                "id": request_id,
                "status": RequestStatus.APPROVED
            })
            
            if not request:
                raise ValueError("Request not found or not available for voting")
            
            # Check if user has already voted
            existing_vote = await self.votes_collection.find_one({
                "user_id": user_id,
                "request_id": request_id
            })
            
            if existing_vote:
                raise ValueError("You have already voted on this request")
            
            # Check if user has enough points
            user = await self.users_collection.find_one({"id": user_id})
            if not user or user.get("points", 0) < vote_data.points_spent:
                raise ValueError("Insufficient points for voting")
            
            # Create vote
            vote = RequestVote(
                user_id=user_id,
                request_id=request_id,
                points_spent=vote_data.points_spent
            )
            
            await self.votes_collection.insert_one(vote.dict())
            
            # Deduct points from user
            await self.users_collection.update_one(
                {"id": user_id},
                {"$inc": {"points": -vote_data.points_spent}}
            )
            
            # Update request vote count
            await self.requests_collection.update_one(
                {"id": request_id},
                {"$inc": {"votes": vote_data.points_spent}}
            )
            
            return {
                "vote": vote,
                "points_spent": vote_data.points_spent,
                "remaining_points": user.get("points", 0) - vote_data.points_spent
            }
            
        except Exception as e:
            logger.error(f"Error voting on request: {e}")
            raise
    
    async def add_comment(self, request_id: str, user_id: str, 
                        comment_data: RequestCommentCreate) -> RequestCommentResponse:
        """Add comment to a request"""
        try:
            # Check if request exists
            request = await self.requests_collection.find_one({"id": request_id})
            if not request:
                raise ValueError("Request not found")
            
            # Create comment
            comment = RequestComment(
                user_id=user_id,
                request_id=request_id,
                comment=comment_data.comment
            )
            
            await self.comments_collection.insert_one(comment.dict())
            
            # Update request comments count
            await self.requests_collection.update_one(
                {"id": request_id},
                {"$inc": {"comments_count": 1}}
            )
            
            # Get user information
            user = await self.users_collection.find_one({"id": user_id})
            
            return RequestCommentResponse(
                **comment.dict(),
                user_name=user.get("name") if user else "Unknown"
            )
            
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            raise
    
    async def get_request_comments(self, request_id: str, skip: int = 0, 
                                 limit: int = 20) -> List[RequestCommentResponse]:
        """Get comments for a request"""
        try:
            cursor = self.comments_collection.find({"request_id": request_id}) \
                                            .sort("created_at", -1) \
                                            .skip(skip) \
                                            .limit(limit)
            
            comments = []
            async for comment_doc in cursor:
                # Get user information
                user = await self.users_collection.find_one({"id": comment_doc["user_id"]})
                
                comment_response = RequestCommentResponse(
                    **comment_doc,
                    user_name=user.get("name") if user else "Unknown"
                )
                comments.append(comment_response)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            raise
    
    async def convert_request_to_feature(self, request_id: str, admin_id: str) -> Dict:
        """Convert approved request to ratable feature"""
        try:
            request = await self.requests_collection.find_one({
                "id": request_id,
                "status": RequestStatus.APPROVED
            })
            
            if not request:
                raise ValueError("Request not found or not approved")
            
            # Import Feature model
            from models import Feature, FeatureStatus
            
            # Create feature from request
            feature = Feature(
                title=request["title"],
                description=request["description"],
                category=request["category"],
                status=FeatureStatus.ACTIVE,
                created_by=admin_id
            )
            
            # Insert feature
            await self.features_collection.insert_one(feature.dict())
            
            # Update request status
            await self.requests_collection.update_one(
                {"id": request_id},
                {
                    "$set": {
                        "status": RequestStatus.IMPLEMENTED,
                        "implemented_in_feature_id": feature.id,
                        "implementation_date": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "feature": feature,
                "request_id": request_id,
                "message": "Request successfully converted to feature"
            }
            
        except Exception as e:
            logger.error(f"Error converting request to feature: {e}")
            raise
    
    async def get_analytics(self) -> RequestAnalytics:
        """Get request analytics"""
        try:
            # Get total counts
            total_requests = await self.requests_collection.count_documents({})
            pending_requests = await self.requests_collection.count_documents({"status": RequestStatus.PENDING})
            approved_requests = await self.requests_collection.count_documents({"status": RequestStatus.APPROVED})
            rejected_requests = await self.requests_collection.count_documents({"status": RequestStatus.REJECTED})
            implemented_requests = await self.requests_collection.count_documents({"status": RequestStatus.IMPLEMENTED})
            
            # Get requests by category
            category_pipeline = [
                {"$group": {"_id": "$category", "count": {"$sum": 1}}}
            ]
            category_cursor = self.requests_collection.aggregate(category_pipeline)
            requests_by_category = {doc["_id"]: doc["count"] async for doc in category_cursor}
            
            # Get requests by priority
            priority_pipeline = [
                {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
            ]
            priority_cursor = self.requests_collection.aggregate(priority_pipeline)
            requests_by_priority = {doc["_id"]: doc["count"] async for doc in priority_cursor}
            
            # Get requests by type
            type_pipeline = [
                {"$group": {"_id": "$request_type", "count": {"$sum": 1}}}
            ]
            type_cursor = self.requests_collection.aggregate(type_pipeline)
            requests_by_type = {doc["_id"]: doc["count"] async for doc in type_cursor}
            
            # Get top contributors
            contributors_pipeline = [
                {"$group": {"_id": "$submitted_by", "count": {"$sum": 1}, "total_points": {"$sum": "$points_spent"}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            contributors_cursor = self.requests_collection.aggregate(contributors_pipeline)
            top_contributors = []
            async for doc in contributors_cursor:
                user = await self.users_collection.find_one({"id": doc["_id"]})
                top_contributors.append({
                    "user_id": doc["_id"],
                    "user_name": user.get("name") if user else "Unknown",
                    "request_count": doc["count"],
                    "total_points_spent": doc["total_points"]
                })
            
            # Get recent activity
            recent_cursor = self.requests_collection.find({}) \
                                                  .sort("submitted_at", -1) \
                                                  .limit(10)
            recent_activity = []
            async for doc in recent_cursor:
                user = await self.users_collection.find_one({"id": doc["submitted_by"]})
                recent_activity.append({
                    "request_id": doc["id"],
                    "title": doc["title"],
                    "user_name": user.get("name") if user else "Unknown",
                    "status": doc["status"],
                    "submitted_at": doc["submitted_at"]
                })
            
            return RequestAnalytics(
                total_requests=total_requests,
                pending_requests=pending_requests,
                approved_requests=approved_requests,
                rejected_requests=rejected_requests,
                implemented_requests=implemented_requests,
                requests_by_category=requests_by_category,
                requests_by_priority=requests_by_priority,
                requests_by_type=requests_by_type,
                top_contributors=top_contributors,
                recent_activity=recent_activity
            )
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            raise
    
    async def delete_request(self, request_id: str, user_id: str) -> bool:
        """Delete user's own request (only if pending)"""
        try:
            request = await self.requests_collection.find_one({
                "id": request_id,
                "submitted_by": user_id,
                "status": RequestStatus.PENDING
            })
            
            if not request:
                return False
            
            # Refund points
            refund_amount = request["points_spent"]
            await self.users_collection.update_one(
                {"id": user_id},
                {"$inc": {"points": refund_amount}}
            )
            
            # Delete request
            await self.requests_collection.delete_one({"id": request_id})
            
            # Delete associated votes and comments
            await self.votes_collection.delete_many({"request_id": request_id})
            await self.comments_collection.delete_many({"request_id": request_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting request: {e}")
            return False