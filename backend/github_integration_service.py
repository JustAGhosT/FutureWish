from motor.motor_asyncio import AsyncIOMotorClient
from github_models import (
    GitHubIntegration, GitHubSyncLog, GitHubIntegrationStatus, 
    GitHubSyncAction, GitHubIntegrationConfig, GitHubSyncStats,
    GitHubRepositoryInfo, GitHubIntegrationResponse, GitHubSyncLogResponse
)
from github_service import github_service, GitHubIssue
from request_models import RequestStatus
from datetime import datetime
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class GitHubIntegrationService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.integrations_collection = db.github_integrations
        self.sync_logs_collection = db.github_sync_logs
        self.requests_collection = db.feature_requests
        self.github_service = github_service
    
    async def create_integration(self, request_id: str, created_by: str, 
                               auto_sync: bool = True) -> GitHubIntegration:
        """Create a new GitHub integration for a feature request"""
        try:
            # Check if integration already exists
            existing = await self.integrations_collection.find_one({"request_id": request_id})
            if existing:
                return GitHubIntegration(**existing)
            
            # Create new integration
            integration = GitHubIntegration(
                request_id=request_id,
                created_by=created_by,
                auto_sync=auto_sync
            )
            
            await self.integrations_collection.insert_one(integration.dict())
            return integration
            
        except Exception as e:
            logger.error(f"Error creating GitHub integration: {e}")
            raise
    
    async def sync_request_to_github(self, request_id: str, admin_id: str) -> Dict:
        """Sync a feature request to GitHub by creating an issue"""
        try:
            # Get the request
            request = await self.requests_collection.find_one({"id": request_id})
            if not request:
                raise ValueError("Request not found")
            
            # Check if request is approved
            if request.get("status") != RequestStatus.APPROVED:
                raise ValueError("Only approved requests can be synced to GitHub")
            
            # Get or create integration
            integration = await self.integrations_collection.find_one({"request_id": request_id})
            if not integration:
                integration_obj = await self.create_integration(request_id, admin_id)
                integration = integration_obj.dict()
            
            # Check if already synced
            if integration.get("github_issue_number"):
                return {
                    "status": "already_synced",
                    "github_issue_number": integration["github_issue_number"],
                    "github_issue_url": integration["github_issue_url"]
                }
            
            # Update integration status
            await self.integrations_collection.update_one(
                {"request_id": request_id},
                {"$set": {"sync_status": GitHubIntegrationStatus.SYNCING}}
            )
            
            # Create GitHub issue
            labels = GitHubIntegrationConfig.get_labels_for_request(
                request.get("request_type", "feature"),
                request.get("priority", "medium"),
                request.get("category", "other")
            )
            
            # Format issue body
            issue_body = self._format_issue_body(request)
            
            # Create issue via GitHub service
            github_issue = await self.github_service.create_issue(
                title=request["title"],
                body=issue_body,
                labels=labels
            )
            
            if github_issue:
                # Update integration with GitHub issue info
                update_data = {
                    "github_issue_number": github_issue.number,
                    "github_issue_url": github_issue.html_url,
                    "github_issue_title": github_issue.title,
                    "github_issue_body": github_issue.body,
                    "github_issue_state": github_issue.state,
                    "github_labels": labels,
                    "sync_status": GitHubIntegrationStatus.SYNCED,
                    "last_sync_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                await self.integrations_collection.update_one(
                    {"request_id": request_id},
                    {"$set": update_data}
                )
                
                # Log sync action
                await self._log_sync_action(
                    integration["id"],
                    GitHubSyncAction.CREATE_ISSUE,
                    "success",
                    admin_id,
                    github_response=github_issue.dict()
                )
                
                return {
                    "status": "synced",
                    "github_issue_number": github_issue.number,
                    "github_issue_url": github_issue.html_url,
                    "message": "Request successfully synced to GitHub"
                }
            else:
                # Update integration with error
                await self.integrations_collection.update_one(
                    {"request_id": request_id},
                    {"$set": {
                        "sync_status": GitHubIntegrationStatus.SYNC_ERROR,
                        "sync_error": "Failed to create GitHub issue"
                    }}
                )
                
                # Log sync error
                await self._log_sync_action(
                    integration["id"],
                    GitHubSyncAction.CREATE_ISSUE,
                    "error",
                    admin_id,
                    error_message="Failed to create GitHub issue"
                )
                
                raise ValueError("Failed to create GitHub issue")
                
        except Exception as e:
            logger.error(f"Error syncing request to GitHub: {e}")
            raise
    
    async def handle_github_webhook(self, payload: Dict, signature: str) -> Dict:
        """Handle GitHub webhook events"""
        try:
            # Verify webhook signature
            if not self.github_service.verify_webhook_signature(
                str(payload).encode(), signature
            ):
                raise ValueError("Invalid webhook signature")
            
            # Process webhook event
            action = payload.get("action")
            issue = payload.get("issue", {})
            
            if not issue:
                return {"status": "ignored", "reason": "No issue in payload"}
            
            issue_number = issue.get("number")
            if not issue_number:
                return {"status": "ignored", "reason": "No issue number"}
            
            # Find integration by GitHub issue number
            integration = await self.integrations_collection.find_one({
                "github_issue_number": issue_number
            })
            
            if not integration:
                return {"status": "ignored", "reason": "No integration found for issue"}
            
            # Update integration based on GitHub event
            if action in ["closed", "reopened"]:
                new_status = GitHubIntegrationConfig.get_request_status_for_github(
                    "closed" if action == "closed" else "open"
                )
                
                # Update request status
                await self.requests_collection.update_one(
                    {"id": integration["request_id"]},
                    {"$set": {
                        "status": RequestStatus.IMPLEMENTED if action == "closed" else RequestStatus.APPROVED,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                # Update integration
                await self.integrations_collection.update_one(
                    {"id": integration["id"]},
                    {"$set": {
                        "github_issue_state": "closed" if action == "closed" else "open",
                        "last_sync_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                # Log sync action
                await self._log_sync_action(
                    integration["id"],
                    GitHubSyncAction.UPDATE_ISSUE,
                    "success",
                    "github_webhook",
                    github_response=payload
                )
                
                return {
                    "status": "processed",
                    "action": action,
                    "request_id": integration["request_id"],
                    "new_status": new_status
                }
            
            return {"status": "ignored", "reason": f"Action {action} not handled"}
            
        except Exception as e:
            logger.error(f"Error handling GitHub webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_integration_by_request_id(self, request_id: str) -> Optional[GitHubIntegrationResponse]:
        """Get GitHub integration for a request"""
        try:
            integration = await self.integrations_collection.find_one({"request_id": request_id})
            if not integration:
                return None
            
            # Get request details
            request = await self.requests_collection.find_one({"id": request_id})
            
            response = GitHubIntegrationResponse(
                **integration,
                request_title=request.get("title") if request else None,
                request_status=request.get("status") if request else None
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting integration: {e}")
            return None
    
    async def get_integrations(self, skip: int = 0, limit: int = 20) -> List[GitHubIntegrationResponse]:
        """Get all GitHub integrations"""
        try:
            cursor = self.integrations_collection.find({}) \
                                                .sort("created_at", -1) \
                                                .skip(skip) \
                                                .limit(limit)
            
            integrations = []
            async for integration_doc in cursor:
                # Get request details
                request = await self.requests_collection.find_one({"id": integration_doc["request_id"]})
                
                response = GitHubIntegrationResponse(
                    **integration_doc,
                    request_title=request.get("title") if request else None,
                    request_status=request.get("status") if request else None
                )
                integrations.append(response)
            
            return integrations
            
        except Exception as e:
            logger.error(f"Error getting integrations: {e}")
            return []
    
    async def get_sync_logs(self, integration_id: Optional[str] = None, 
                          skip: int = 0, limit: int = 50) -> List[GitHubSyncLogResponse]:
        """Get sync logs"""
        try:
            query = {}
            if integration_id:
                query["integration_id"] = integration_id
            
            cursor = self.sync_logs_collection.find(query) \
                                            .sort("created_at", -1) \
                                            .skip(skip) \
                                            .limit(limit)
            
            logs = []
            async for log_doc in cursor:
                # Get integration details
                integration = await self.integrations_collection.find_one({"id": log_doc["integration_id"]})
                
                response = GitHubSyncLogResponse(
                    **log_doc,
                    github_issue_number=integration.get("github_issue_number") if integration else None,
                    github_issue_url=integration.get("github_issue_url") if integration else None
                )
                logs.append(response)
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting sync logs: {e}")
            return []
    
    async def get_sync_stats(self) -> GitHubSyncStats:
        """Get GitHub sync statistics"""
        try:
            # Get integration counts
            total_integrations = await self.integrations_collection.count_documents({})
            synced_integrations = await self.integrations_collection.count_documents({
                "sync_status": GitHubIntegrationStatus.SYNCED
            })
            pending_integrations = await self.integrations_collection.count_documents({
                "sync_status": GitHubIntegrationStatus.NOT_SYNCED
            })
            error_integrations = await self.integrations_collection.count_documents({
                "sync_status": GitHubIntegrationStatus.SYNC_ERROR
            })
            
            # Get sync action counts
            total_issues_created = await self.sync_logs_collection.count_documents({
                "action": GitHubSyncAction.CREATE_ISSUE,
                "status": "success"
            })
            total_comments_synced = await self.sync_logs_collection.count_documents({
                "action": GitHubSyncAction.ADD_COMMENT,
                "status": "success"
            })
            total_sync_actions = await self.sync_logs_collection.count_documents({})
            
            # Get last sync
            last_sync_doc = await self.sync_logs_collection.find_one(
                {"status": "success"},
                sort=[("created_at", -1)]
            )
            last_sync_at = last_sync_doc.get("created_at") if last_sync_doc else None
            
            # Calculate success rate
            successful_actions = await self.sync_logs_collection.count_documents({"status": "success"})
            sync_success_rate = (successful_actions / total_sync_actions) if total_sync_actions > 0 else 0
            
            # Repository info
            repository_info = GitHubRepositoryInfo(
                owner=self.github_service.repo_owner,
                name=self.github_service.repo_name,
                full_name=f"{self.github_service.repo_owner}/{self.github_service.repo_name}",
                description="EngageMesh Feature Requests",
                html_url=self.github_service.get_repository_url(),
                open_issues_count=0,  # Could be fetched from GitHub API
                is_configured=self.github_service.is_configured()
            )
            
            return GitHubSyncStats(
                total_integrations=total_integrations,
                synced_integrations=synced_integrations,
                pending_integrations=pending_integrations,
                error_integrations=error_integrations,
                total_issues_created=total_issues_created,
                total_comments_synced=total_comments_synced,
                total_sync_actions=total_sync_actions,
                last_sync_at=last_sync_at,
                sync_success_rate=sync_success_rate,
                repository_info=repository_info
            )
            
        except Exception as e:
            logger.error(f"Error getting sync stats: {e}")
            # Return empty stats on error
            return GitHubSyncStats(
                total_integrations=0,
                synced_integrations=0,
                pending_integrations=0,
                error_integrations=0,
                total_issues_created=0,
                total_comments_synced=0,
                total_sync_actions=0,
                last_sync_at=None,
                sync_success_rate=0,
                repository_info=GitHubRepositoryInfo(
                    owner=self.github_service.repo_owner,
                    name=self.github_service.repo_name,
                    full_name=f"{self.github_service.repo_owner}/{self.github_service.repo_name}",
                    description="EngageMesh Feature Requests",
                    html_url=self.github_service.get_repository_url(),
                    open_issues_count=0,
                    is_configured=self.github_service.is_configured()
                )
            )
    
    async def _format_issue_body(self, request: Dict) -> str:
        """Format the GitHub issue body from a feature request"""
        body = f"""## Feature Request from EngageMesh

**Description:**
{request.get('description', '')}

**Request Type:** {request.get('request_type', '').replace('_', ' ').title()}
**Priority:** {request.get('priority', '').title()}
**Category:** {request.get('category', '').replace('_', ' ').title()}

"""
        
        if request.get('use_case'):
            body += f"""**Use Case:**
{request['use_case']}

"""
        
        if request.get('expected_behavior'):
            body += f"""**Expected Behavior:**
{request['expected_behavior']}

"""
        
        if request.get('current_workaround'):
            body += f"""**Current Workaround:**
{request['current_workaround']}

"""
        
        body += f"""**Request Details:**
- Points Spent: {request.get('points_spent', 0)}
- Votes: {request.get('votes', 0)}
- Submitted: {request.get('submitted_at', '')}

---
*This issue was automatically created from EngageMesh (Feature Management Platform)*
*Request ID: {request.get('id', '')}*"""
        
        return body
    
    async def _log_sync_action(self, integration_id: str, action: GitHubSyncAction, 
                             status: str, created_by: str, 
                             error_message: Optional[str] = None,
                             github_response: Optional[Dict] = None):
        """Log a sync action"""
        try:
            log = GitHubSyncLog(
                integration_id=integration_id,
                action=action,
                status=status,
                error_message=error_message,
                github_response=github_response,
                created_by=created_by
            )
            
            await self.sync_logs_collection.insert_one(log.dict())
            
        except Exception as e:
            logger.error(f"Error logging sync action: {e}")
    
    async def delete_integration(self, integration_id: str) -> bool:
        """Delete a GitHub integration"""
        try:
            result = await self.integrations_collection.delete_one({"id": integration_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting integration: {e}")
            return False