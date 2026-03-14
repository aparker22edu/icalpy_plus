#
# Abbie Parker
# March 8, 2026
#
# This is a file for the api endpoint definitions
#

#TODO: consider moving to separate endpoint files under routers folder

import uuid
from datetime import datetime, timedelta
from uuidbase62 import base62 # will use for fake UID on local tasks
from server.ics_service import get_session, SyncService
from typing import List, Annotated
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
import server.schemas as m 

SessionDep = Annotated[Session, Depends(get_session)]


router = APIRouter(prefix="/api")

# region **** FEED ****
@router.get("/feeds", response_model=List[m.FeedResponse])
def get_feeds(session: SessionDep):
    return session.exec(select(m.Feed)).all()

@router.post("/feeds", response_model=m.FeedResponse)
def add_feed(feed_data: m.FeedBase, session: SessionDep, background_tasks: BackgroundTasks):
    db_feed = m.Feed.model_validate(feed_data)
    session.add(db_feed)
    session.commit()
    session.refresh(db_feed)
    # adding this line to auto-sync after we get an id
    background_tasks.add_task(SyncService.perform_sync, db_feed.id)
    return db_feed

@router.delete("/feeds/{feed_id}")
def remove_feed(feed_id: int, session: SessionDep):
    feed = session.get(m.Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    session.delete(feed)
    session.commit()
    return {"ok": True}

@router.put("/feeds/{feed_id}", response_model=m.FeedResponse)
def update_feed(feed_id: int, feed_data: m.FeedBase, session: SessionDep, background_tasks: BackgroundTasks):
    db_feed = session.get(m.Feed, feed_id)
    if not db_feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    db_feed.sqlmodel_update(feed_data.model_dump())
    session.add(db_feed)
    session.commit()
    session.refresh(db_feed)
    # adding this line to auto-sync after we update
    # could maybe limit it to only update if the url is updated
    background_tasks.add_task(SyncService.perform_sync, db_feed.id)
    return db_feed

@router.post("/feeds/{feed_id}/sync")
def sync_feed(feed_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(SyncService.perform_sync, feed_id)
    return {"ok": True}
# endregion

# region  **** TASK ****
# TODO: Implementation for filtering and sorting
#     Handle query parametersfor example:
#     GET /api/tasks?status=in_progress&since=2023-01-01
# https://oneuptime.com/blog/post/2026-02-03-fastapi-query-parameters/view
# TODO: handle locally added events/tasks?
# TODO: handle multiselect updates on status and categories

@router.get("/tasks", response_model=List[m.TaskResponse])
def get_tasks(session: SessionDep, 
        days_back: int = Query(
        default=5, 
        title="Days in the Past",
        description="Positive integer number of days ago to include",
        ge=0, # Validation
        le=365
    ),
    days_ahead: int = Query(
        default=7, 
        title="Days in the Future",
        description="Positive integer number of days ahead to include",
        le=365, # Validation
        ge=0
    )):
    now = datetime.now()
    start_date = now - timedelta(days=days_back)
    end_date = now + timedelta(days=days_ahead)
    
    # SQLModel filter: find tasks within a 14 day window
    statement = (
        select(m.Task)
        .where(
            m.Task.start_time >= start_date,
            m.Task.start_time <= end_date
        )
        .options(selectinload(m.Task.categories))
        .order_by(m.Task.start_time.desc())
        )
    # Use selectinload to ensure categories are included in the response

    return session.exec(statement).all()

# TODO: this may need to be put in dev mode since we don't have 
# whole task updating and might disable deletes
@router.post("/tasks", response_model=m.TaskResponse, include_in_schema=False)
def add_task(task_data: m.TaskSyncBase, session: SessionDep):
    # Generate a unique UID if not provided for local tasks
    if task_data.uid is None:
        task_data.uid = "icalpy_plus." + base62.encode(uuid.uuid4())
        task_data.source_id = 0
    db_task = m.Task.model_validate(task_data)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.put("/tasks/{task_id}", response_model=m.TaskResponse)
def update_task(task_id: int, task_data: m.TaskUpdate, session: SessionDep):
    db_task = session.get(m.Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Handle Many-to-Many CAtegories Linker Table
    if task_data.cat_ids is not None:
        if task_data.cat_ids:
            # Resolve cat_ids to actual Cetegory objects to update the linker table
            cat_statement = select(m.Category).where(m.Category.id.in_(task_data.cat_ids))
            db_task.categories = session.exec(cat_statement).all()
        else:
            # Clear all categories for this task
            db_task.categories = []
    db_task.sqlmodel_update(task_data.model_dump(exclude_unset=True))
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

# will likely remove/restrict this endpoint since ics feed are read-only 
# might want a hide option?
@router.delete("/tasks/{task_id}", include_in_schema=False)
def remove_task(task_id: int, session: SessionDep):
    task = session.get(m.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)  # TODO: need to think about how delete is handled
    session.commit()
    return {"ok": True}
# endregion

# region **** CATEGORY ****
@router.get("/categories", response_model=List[m.CategoryResponse])
def get_categories(session: SessionDep):
    return session.exec(select(m.Category)).all()

@router.post("/categories", response_model=m.CategoryResponse)
def add_category(category_data: m.CategoryBase, session: SessionDep):
    db_category = m.Category.model_validate(category_data)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

@router.delete("/categories/{cat_id}")
def remove_category(cat_id: int, session: SessionDep):
    category = session.get(m.Category, cat_id)
    if not category: # this could probably just fail silently
        raise HTTPException(status_code=404, detail="category not found")
    session.delete(category)
    session.commit()
    return {"ok": True}

@router.put("/categories/{cat_id}", response_model=m.CategoryResponse)
def update_category(cat_id: int, category_data: m.CategoryBase, session: SessionDep):
    db_category = session.get(m.Category, cat_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="category not found")
    db_category.sqlmodel_update(category_data.model_dump())
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category
# endregion

