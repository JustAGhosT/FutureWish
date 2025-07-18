import os
import hmac
import hashlib
import httpx
import logging
from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str
    state: str
    html_url: str
    created_at: datetime
    updated_at: datetime

class GitHubService:
    def __init__(self):
        self.token = os.getenv("GITHUB_ACCESS_TOKEN")
        self.repo_owner = "JustAGhoST"
        self.repo_name = "FutureWish"
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "wh_secret_engagemesh_2024_9a8b7c6d5e4f3g2h1i0j")
        self.base_url = "https://api.github.com"
        
        if not self.token:
            logger.warning("GitHub token not found. GitHub integration will be disabled.")
    
    def is_configured(self) -> bool:
        """Check if GitHub integration is properly configured"""
        return bool(self.token)
    
    async def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Optional[GitHubIssue]:
        """Create a GitHub issue from a feature request"""
        if not self.is_configured():
            logger.error("GitHub integration not configured")
            return None
        
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            # Format the issue body with EngageMesh branding
            formatted_body = f"""
## Feature Request from EngageMesh

{body}

---
*This issue was automatically created from a feature request submitted via EngageMesh.*
*Platform: https://engagemesh.com*
"""
            
            payload = {
                "title": title,
                "body": formatted_body,
                "labels": labels or ["feature-request", "engagemesh"]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 201:
                    issue_data = response.json()
                    return GitHubIssue(
                        number=issue_data["number"],
                        title=issue_data["title"],
                        body=issue_data["body"],
                        state=issue_data["state"],
                        html_url=issue_data["html_url"],
                        created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                    )
                else:
                    logger.error(f"Failed to create GitHub issue: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return None
    
    async def get_issue(self, issue_number: int) -> Optional[GitHubIssue]:
        """Get a GitHub issue by number"""
        if not self.is_configured():
            return None
        
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    issue_data = response.json()
                    return GitHubIssue(
                        number=issue_data["number"],
                        title=issue_data["title"],
                        body=issue_data["body"],
                        state=issue_data["state"],
                        html_url=issue_data["html_url"],
                        created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                    )
                else:
                    logger.error(f"Failed to get GitHub issue: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting GitHub issue: {e}")
            return None
    
    async def update_issue(self, issue_number: int, title: Optional[str] = None, 
                          body: Optional[str] = None, state: Optional[str] = None) -> Optional[GitHubIssue]:
        """Update a GitHub issue"""
        if not self.is_configured():
            return None
        
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            payload = {}
            if title:
                payload["title"] = title
            if body:
                payload["body"] = body
            if state:
                payload["state"] = state
                
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    issue_data = response.json()
                    return GitHubIssue(
                        number=issue_data["number"],
                        title=issue_data["title"],
                        body=issue_data["body"],
                        state=issue_data["state"],
                        html_url=issue_data["html_url"],
                        created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                    )
                else:
                    logger.error(f"Failed to update GitHub issue: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error updating GitHub issue: {e}")
            return None
    
    async def add_comment(self, issue_number: int, comment_body: str) -> bool:
        """Add a comment to a GitHub issue"""
        if not self.is_configured():
            return False
        
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            payload = {
                "body": comment_body
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/comments",
                    headers=headers,
                    json=payload
                )
                
                return response.status_code == 201
                
        except Exception as e:
            logger.error(f"Error adding comment to GitHub issue: {e}")
            return False
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        if not signature:
            return False
        
        # Remove 'sha256=' prefix
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        # Compute HMAC
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def get_repository_url(self) -> str:
        """Get the full repository URL"""
        return f"https://github.com/{self.repo_owner}/{self.repo_name}"
    
    def get_issue_url(self, issue_number: int) -> str:
        """Get the URL for a specific issue"""
        return f"https://github.com/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"
    
    async def list_repository_issues(self, state: str = "all", labels: Optional[str] = None) -> List[GitHubIssue]:
        """List issues in the repository"""
        if not self.is_configured():
            return []
        
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            params = {"state": state}
            if labels:
                params["labels"] = labels
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    issues_data = response.json()
                    return [
                        GitHubIssue(
                            number=issue["number"],
                            title=issue["title"],
                            body=issue["body"],
                            state=issue["state"],
                            html_url=issue["html_url"],
                            created_at=datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")),
                            updated_at=datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
                        )
                        for issue in issues_data
                    ]
                else:
                    logger.error(f"Failed to list repository issues: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing repository issues: {e}")
            return []

# Global instance
github_service = GitHubService()