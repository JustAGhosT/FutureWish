from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class GitHubIntegrationStatus(str, Enum):
    NOT_SYNCED = "not_synced"
    SYNCING = "syncing"
    SYNCED = "synced"
    SYNC_ERROR = "sync_error"

class GitHubSyncAction(str, Enum):
    CREATE_ISSUE = "create_issue"
    UPDATE_ISSUE = "update_issue"
    ADD_COMMENT = "add_comment"
    CLOSE_ISSUE = "close_issue"

class GitHubWebhookEvent(str, Enum):
    OPENED = "opened"
    CLOSED = "closed"
    REOPENED = "reopened"
    EDITED = "edited"
    LABELED = "labeled"
    UNLABELED = "unlabeled"

# GitHub Integration Models
class GitHubIntegration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None
    github_repo_owner: str = "JustAGhoST"
    github_repo_name: str = "FutureWish"
    
    # Sync status
    sync_status: GitHubIntegrationStatus = GitHubIntegrationStatus.NOT_SYNCED
    sync_error: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    
    # GitHub issue details
    github_issue_title: Optional[str] = None
    github_issue_body: Optional[str] = None
    github_issue_state: Optional[str] = None  # open, closed
    github_labels: List[str] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # admin user id
    
    # Sync configuration
    auto_sync: bool = True
    sync_comments: bool = True
    sync_status_updates: bool = True

class GitHubSyncLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    integration_id: str
    action: GitHubSyncAction
    status: str  # success, error, pending
    error_message: Optional[str] = None
    github_response: Optional[dict] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class GitHubWebhookPayload(BaseModel):
    action: str
    issue: Optional[dict] = None
    repository: Optional[dict] = None
    sender: Optional[dict] = None

class GitHubIssueCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    labels: List[str] = ["feature-request", "engagemesh"]
    assignees: List[str] = []
    milestone: Optional[int] = None

class GitHubIssueUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[str] = None  # open, closed
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    milestone: Optional[int] = None

class GitHubCommentCreate(BaseModel):
    body: str = Field(..., min_length=1)

# Response Models
class GitHubIntegrationResponse(BaseModel):
    id: str
    request_id: str
    github_issue_number: Optional[int]
    github_issue_url: Optional[str]
    github_repo_owner: str
    github_repo_name: str
    sync_status: GitHubIntegrationStatus
    sync_error: Optional[str]
    last_sync_at: Optional[datetime]
    github_issue_title: Optional[str]
    github_issue_state: Optional[str]
    github_labels: List[str]
    created_at: datetime
    updated_at: datetime
    auto_sync: bool
    
    # Request details
    request_title: Optional[str] = None
    request_status: Optional[str] = None

class GitHubSyncLogResponse(BaseModel):
    id: str
    integration_id: str
    action: GitHubSyncAction
    status: str
    error_message: Optional[str]
    created_at: datetime
    
    # Integration details
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None

class GitHubRepositoryInfo(BaseModel):
    owner: str
    name: str
    full_name: str
    description: Optional[str]
    html_url: str
    open_issues_count: int
    is_configured: bool

class GitHubSyncStats(BaseModel):
    total_integrations: int
    synced_integrations: int
    pending_integrations: int
    error_integrations: int
    
    total_issues_created: int
    total_comments_synced: int
    total_sync_actions: int
    
    last_sync_at: Optional[datetime]
    sync_success_rate: float
    
    # Repository stats
    repository_info: GitHubRepositoryInfo

# Configuration for GitHub Integration
class GitHubIntegrationConfig:
    # Default labels for EngageMesh issues
    DEFAULT_LABELS = ["feature-request", "engagemesh"]
    
    # Label mappings for request types
    TYPE_LABELS = {
        "feature": "type:feature",
        "enhancement": "type:enhancement", 
        "bug_fix": "type:bug",
        "integration": "type:integration"
    }
    
    # Label mappings for request priorities
    PRIORITY_LABELS = {
        "low": "priority:low",
        "medium": "priority:medium",
        "high": "priority:high",
        "critical": "priority:critical"
    }
    
    # Label mappings for request categories
    CATEGORY_LABELS = {
        "ui_ux": "category:ui-ux",
        "performance": "category:performance",
        "integration": "category:integration",
        "security": "category:security",
        "mobile": "category:mobile",
        "api": "category:api",
        "other": "category:other"
    }
    
    # Status mappings
    STATUS_MAPPINGS = {
        "pending": "open",
        "approved": "open",
        "implemented": "closed",
        "rejected": "closed",
        "duplicate": "closed"
    }
    
    # Reverse mappings
    GITHUB_TO_REQUEST_STATUS = {
        "open": "approved",
        "closed": "implemented"
    }
    
    @classmethod
    def get_labels_for_request(cls, request_type: str, priority: str, category: str) -> List[str]:
        """Get GitHub labels for a feature request"""
        labels = cls.DEFAULT_LABELS.copy()
        
        if request_type in cls.TYPE_LABELS:
            labels.append(cls.TYPE_LABELS[request_type])
        
        if priority in cls.PRIORITY_LABELS:
            labels.append(cls.PRIORITY_LABELS[priority])
        
        if category in cls.CATEGORY_LABELS:
            labels.append(cls.CATEGORY_LABELS[category])
        
        return labels
    
    @classmethod
    def get_github_state_for_request(cls, request_status: str) -> str:
        """Get GitHub issue state for request status"""
        return cls.STATUS_MAPPINGS.get(request_status, "open")
    
    @classmethod
    def get_request_status_for_github(cls, github_state: str) -> str:
        """Get request status for GitHub issue state"""
        return cls.GITHUB_TO_REQUEST_STATUS.get(github_state, "approved")