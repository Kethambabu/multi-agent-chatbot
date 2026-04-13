"""
State management for the multi-modal AI agent workflow.

Defines the state schema for LangGraph using both TypedDict and Pydantic approaches.
- TypedDict: Lightweight, good for simple state management
- Pydantic: Full validation, serialization, better error messages
"""

from typing import Optional, List, Any, Literal, TypedDict
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


# ============================================================================
# Task Type Enum
# ============================================================================

class TaskType(str, Enum):
    """Supported task types for the multi-modal agent."""
    
    SUMMARIZATION = "summary"
    STANCE_DETECTION = "stance"
    IMAGE_GENERATION = "image_gen"
    IMAGE_ANALYSIS = "image_analysis"


# ============================================================================
# TypedDict Approach (Lightweight, Simple)
# ============================================================================

class AgentStateDict(TypedDict, total=False):
    """TypedDict state for LangGraph workflow.
    
    Advantages:
    - Lightweight and simple
    - Good for straightforward state management
    - No runtime validation overhead
    - Compatible with all type checkers
    
    Note: total=False means all fields are optional
    """
    
    # Core input fields
    user_input: str
    image: Optional[bytes]
    
    # Task management
    task_type: Literal["summary", "stance", "image_gen", "image_analysis"]
    
    # Results and status
    result: Optional[Any]
    error: Optional[str]
    
    # Metadata
    messages: List[str]
    created_at: str
    updated_at: str


# ============================================================================
# Pydantic Approach (With Validation)
# ============================================================================

class AgentStatePydantic(BaseModel):
    """Pydantic-based state for LangGraph workflow.
    
    Advantages:
    - Full runtime validation
    - Better error messages
    - Built-in serialization (JSON, dict)
    - Type coercion
    - Extensible with custom validators
    
    Fields:
        user_input: Text input from user
        image: Optional binary image data
        task_type: Type of task to perform
        result: Task result (format varies by task)
        error: Error message if task failed
        messages: Conversation history
        created_at: ISO format timestamp when created
        updated_at: ISO format timestamp when last updated
    """
    
    # Core input fields
    user_input: str = Field(
        ...,
        description="User input text (prompt, text to summarize, etc.)"
    )
    image: Optional[bytes] = Field(
        default=None,
        description="Optional image bytes for image analysis or generation"
    )
    
    # Task management
    task_type: TaskType = Field(
        default=TaskType.SUMMARIZATION,
        description="Type of task: summary, stance, image_gen, or image_analysis"
    )
    
    # Results and error handling
    result: Optional[Any] = Field(
        default=None,
        description="Task result (format depends on task_type)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if task execution failed"
    )
    
    # Metadata
    messages: List[str] = Field(
        default_factory=list,
        description="Conversation message history"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp of state creation"
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp of last update"
    )
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True  # Serialize enums to their values
        json_schema_extra = {
            "example": {
                "user_input": "Summarize this text",
                "task_type": "summary",
                "messages": ["User: Summarize..."],
                "created_at": "2026-04-11T10:30:00",
                "updated_at": "2026-04-11T10:30:00"
            }
        }
    
    @validator("user_input")
    def validate_user_input(cls, v):
        """Validate that user_input is not empty."""
        if not v or not v.strip():
            raise ValueError("user_input cannot be empty")
        return v.strip()
    
    @validator("image")
    def validate_image(cls, v):
        """Validate image data if provided."""
        if v is not None and len(v) == 0:
            raise ValueError("image bytes cannot be empty")
        return v
    
    def add_message(self, message: str):
        """Add a message to the conversation history.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.updated_at = datetime.utcnow().isoformat()
    
    def set_result(self, result: Any, error: Optional[str] = None):
        """Set the result and optionally error.
        
        Args:
            result: Task result
            error: Optional error message
        """
        self.result = result
        self.error = error
        self.updated_at = datetime.utcnow().isoformat()
    
    def set_error(self, error: str):
        """Set error state.
        
        Args:
            error: Error message
        """
        self.error = error
        self.result = None
        self.updated_at = datetime.utcnow().isoformat()
    
    def is_error(self) -> bool:
        """Check if state is in error condition.
        
        Returns:
            True if error is set, False otherwise
        """
        return self.error is not None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for LangGraph compatibility.
        
        Returns:
            Dictionary representation of state
        """
        return self.dict()


# ============================================================================
# Legacy Dataclass Approach (For Backward Compatibility)
# ============================================================================

class WorkflowState:
    """Legacy workflow state class for backward compatibility.
    
    Provides a simple dataclass-like interface with helpful methods.
    Consider migrating to AgentStatePydantic for new projects.
    """
    
    def __init__(
        self,
        user_input: str,
        image: Optional[bytes] = None,
        task_type: str = "summary",
        result: Optional[Any] = None,
        error: Optional[str] = None,
        messages: Optional[List[str]] = None
    ):
        """Initialize workflow state.
        
        Args:
            user_input: Text input from user
            image: Optional image bytes
            task_type: Type of task to perform
            result: Task result
            error: Error message if applicable
            messages: Conversation history
        """
        self.user_input = user_input
        self.image = image
        self.task_type = task_type
        self.result = result
        self.error = error
        self.messages = messages or []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
    
    def add_message(self, message: str):
        """Add a message to history."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow().isoformat()
    
    def set_result(self, result: Any, error: Optional[str] = None):
        """Set result and optional error."""
        self.result = result
        self.error = error
        self.updated_at = datetime.utcnow().isoformat()
    
    def set_error(self, error: str):
        """Set error state."""
        self.error = error
        self.result = None
        self.updated_at = datetime.utcnow().isoformat()
    
    def is_error(self) -> bool:
        """Check if in error state."""
        return self.error is not None
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"WorkflowState(task={self.task_type}, "
            f"error={bool(self.error)}, "
            f"result={'set' if self.result else 'None'})"
        )
