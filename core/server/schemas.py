#
# Abbie Parker
# March 7, 2026
#
# This code uses pydantic and sqlmodel for schemas and validated data
#

#TODO: rename task to event

from typing import Optional, List
from enum import StrEnum
from datetime import datetime
from pydantic import Field as PydanticField
from sqlmodel import Field, Relationship, SQLModel

TBL_TASK = "task"
TBL_FEED = "feed"
TBL_CATEGORY = "category"
TBL_TASK_CAT = "task_cat"

# TODO: consider creating a model for status

class TaskStatus(StrEnum):
    NONE = "none"
    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"

# region linking table
class TaskCatLink(SQLModel, table=True):
    __tablename__: str = TBL_TASK_CAT
    task_uid: str = Field(foreign_key=f"{TBL_TASK}.uid", primary_key=True)
    cat_id: int = Field(foreign_key=f"{TBL_CATEGORY}.id", primary_key=True)
# endregion

# region ics feeds
class FeedBase(SQLModel):
    url: str = Field(index=True, unique=True)
    label: str
    synced_at: Optional[datetime] = Field(default=None)
    sync_count: Optional[int] = Field(default=None)

class Feed(FeedBase, table=True):
    __tablename__: str = TBL_FEED
    id: Optional[int] = Field(default=None, primary_key=True)

    tasks: list[Task] = Relationship(  #required for cascade delete
        back_populates="feed", cascade_delete=True)
    
class FeedResponse(FeedBase):
    id: int
    
# endregion

# region Categories
class CategoryBase(SQLModel):
    label: str = Field(index=True, unique=True)
    color: str = "#007bff"
    value: int = 0

class Category(CategoryBase, table=True):
    __tablename__: str = TBL_CATEGORY
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship: Many-to-Many with Task
    tasks: List["Task"] = Relationship(back_populates="categories", link_model=TaskCatLink)

class CategoryResponse(CategoryBase):
    id: int
# endregion 

# region tasks/events
class TaskSyncBase(SQLModel):
    """Fields synchronized from the .ics """
    uid: str = Field(index=True, unique=True)
    summary: str
    start_time: str
    description: str = ""

class Task(TaskSyncBase, table=True):
    """The full database table combining sync and local fields"""
    __tablename__: str = TBL_TASK
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
     # Local-only fields
    source_id: Optional[int] = Field(
            default=None, 
            foreign_key=f"{TBL_FEED}.id",
            ondelete="CASCADE"
        )
    status: TaskStatus = Field(default=TaskStatus.NONE)

    # Relationships
    categories: List[Category] = Relationship(back_populates="tasks", link_model=TaskCatLink)
    feed: Feed = Relationship(back_populates="tasks")
class TaskUpdate(SQLModel):
    """Specific for updating local fields"""
    status: Optional[TaskStatus] = None
    cat_ids: Optional[List[int]] = None
    
class TaskResponse(TaskSyncBase):
    id: int
    status: TaskStatus
    source_id: Optional[int]
    categories: List[CategoryResponse]
    
    uid: str = PydanticField(exclude=True)
# endregion