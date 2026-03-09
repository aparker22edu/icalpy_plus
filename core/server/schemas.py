#
# Abbie Parker
# March 7, 2026
#
# This code uses pydantic and sqlmodel for schemas and validated data
#

from typing import Optional, List
from enum import Enum
from pydantic import Field as PydanticField
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.orm import selectinload

TABLE_TASKS = "tasks"
TABLE_FEEDS = "feeds"
TABLE_TAGS = "tags"
TABLE_TASK_TAGS = "task_tag"


class TaskStatus(str, Enum):
    NONE = "none"
    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"

# linking table
class TaskTagLink(SQLModel, table=True):
    __tablename__: str = TABLE_TASK_TAGS
    task_id: int = Field(foreign_key=f"{TABLE_TASKS}.id", primary_key=True)
    tag_id: int = Field(foreign_key=f"{TABLE_TAGS}.id", primary_key=True)

# ics feeds
class FeedBase(SQLModel):
    url: str = Field(index=True, unique=True)
    label: str

class Feed(FeedBase, table=True):
    __tablename__: str = TABLE_FEEDS
    id: Optional[int] = Field(default=None, primary_key=True)

class FeedResponse(FeedBase):
    id: int

# tags
class TagBase(SQLModel):
    label: str = Field(index=True, unique=True)
    color: str = "#007bff"
    value: int = 0

class Tag(TagBase, table=True):
    __tablename__: str = TABLE_TAGS
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship: Many-to-Many with Task
    tasks: List["Task"] = Relationship(back_populates=TABLE_TAGS, link_model=TaskTagLink)

class TagResponse(TagBase):
    id: int

# tasks/events
class TaskSyncBase(SQLModel):
    """Fields synchronized from the .ics """
    uid: str = Field(index=True, unique=True)
    summary: str
    start_time: str
    description: str = ""

class Task(TaskSyncBase, table=True):
    """The full database table combining sync and local fields"""
    __tablename__: str = TABLE_TASKS
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
     # Local-only fields
    source_id: Optional[int] = Field(
            default=None, 
            foreign_key=f"{TABLE_FEEDS}.id",
            ondelete="CASCADE"
        )
    status: TaskStatus = Field(default=TaskStatus.NONE)

    # Relationships
    tags: List[Tag] = Relationship(back_populates=TABLE_TASKS, link_model=TaskTagLink)

class TaskUpdate(SQLModel):
    """Specific for updating local fields"""
    status: Optional[TaskStatus] = None
    tag_ids: Optional[List[int]] = None
    
class TaskResponse(TaskSyncBase):
    id: int
    status: TaskStatus
    source_id: Optional[int]
    tags: List[TagResponse]
    
    uid: str = PydanticField(exclude=True)
