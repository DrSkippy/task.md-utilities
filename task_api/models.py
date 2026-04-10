"""Pydantic request/response models for the Task REST API."""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Request body for creating a new task."""

    title: str = Field(..., min_length=1, description="Task title (becomes the filename)")
    content: str = Field(..., description="Task body text")
    lane: str = Field(..., min_length=1, description="Target lane name")
    tags: List[str] = Field(default_factory=list, description="Optional list of tags")
    due_date: Optional[date] = Field(None, description="Due date (YYYY-MM-DD)")


class TaskUpdate(BaseModel):
    """Request body for updating an existing task.

    Fields that are absent from the request are left unchanged.
    Pass ``null`` for ``due_date`` to clear it.
    """

    content: Optional[str] = None
    tags: Optional[List[str]] = None
    new_title: Optional[str] = None
    due_date: Optional[date] = None


class TaskResponse(BaseModel):
    """Response schema for a single task."""

    title: str
    content: str
    lane: str
    tags: List[str]
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD or null")
    path: str


class LaneInfo(BaseModel):
    """Lane name with its task count."""

    name: str
    task_count: int


class LanesResponse(BaseModel):
    """Response schema for the lanes list endpoint."""

    lanes: List[LaneInfo]
    total_lanes: int


class StatisticsResponse(BaseModel):
    """Response schema for the statistics endpoint."""

    num_lanes: int
    tasks_per_lane: Dict[str, int]
    tag_counts: Dict[str, int]
    due_date_counts: Dict[str, int]


class MessageResponse(BaseModel):
    """Generic success message."""

    message: str


class SplitResponse(BaseModel):
    """Response schema for the split operation."""

    message: str
    tasks_split: int
    original_tasks: List[str]
    total_tasks_after: int


class ErrorResponse(BaseModel):
    """Error response body."""

    error: str
    detail: Optional[str] = None
