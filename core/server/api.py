#
# Abbie Parker
# March 8, 2026
#
# This is a file for the api endpoint definitions
#

from server.ics_service import get_session, SyncService
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
import server.schemas as m

router = APIRouter(prefix="/api")

# **** FEED ****
@router.get("/feeds", response_model=List[m.FeedResponse])
def get_feeds(session: Session = Depends(get_session)):
    return session.exec(select(m.Feed)).all()

@router.post("/feeds", response_model=m.FeedResponse)
def add_feed(feed_data: m.FeedBase, session: Session = Depends(get_session)):
    db_feed = m.Feed.model_validate(feed_data)
    session.add(db_feed)
    session.commit()
    session.refresh(db_feed)
    return db_feed

@router.delete("/feeds/{feed_id}")
def remove_feed(feed_id: int, session: Session = Depends(get_session)):
    feed = session.get(m.Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    session.delete(feed)
    session.commit()
    return {"ok": True}

@router.put("/feeds/{feed_id}", response_model=m.FeedResponse)
def update_feed(feed_id: int, feed_data: m.FeedBase, session: Session = Depends(get_session)):
    db_feed = session.get(m.Feed, feed_id)
    if not db_feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    db_feed.sqlmodel_update(feed_data.model_dump())
    session.add(db_feed)
    session.commit()
    session.refresh(db_feed)
    return db_feed

@router.post("/feeds/{feed_id}/sync")
async def sync_feed(feed_id: int, session: Session = Depends(get_session)):
    feed = session.get(m.Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    try:
        ics_entries = SyncService.fetch_as_dicts(feed.url, feed.id)
        SyncService.sync_ics_to_db(session, ics_entries, feed.id)
        return {"status": "sync complete", "count": len(ics_entries)}
        pass 
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to sync ICS feed")
        
    return {"status": "sync complete"}

# **** TASKS ****
# TODO: Implementation for filtering and sorting
#     Handle query parametersfor example:
#     GET /api/tasks?status=in_progress&since=2023-01-01
# TODO: handle locally added events/tasks

@router.get("/tasks", response_model=List[m.TaskResponse])
def get_tasks(session: Session = Depends(get_session)):
    # Use selectinload to ensure tags are included in the response
    statement = select(m.Task).options(selectinload(m.Task.tags))
    return session.exec(statement).all()

@router.post("/tasks", response_model=m.TaskResponse)
def add_task(task_data: m.TaskSyncBase, session: Session = Depends(get_session)):
    # Generate a unique UID if not provided for local tasks
    db_task = m.Task.model_validate(task_data)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.put("/tasks/{task_id}", response_model=m.TaskResponse)
def update_task(task_id: int, task_data: m.TaskUpdate, session: Session = Depends(get_session)):
    db_task = session.get(m.Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Handle Many-to-Many Tags Linker Table
    if task_data.tag_ids is not None:
        if task_data.tag_ids:
            # Resolve tag_ids to actual Tag objects to update the linker table
            tag_statement = select(m.Tag).where(m.Tag.id.in_(task_data.tag_ids))
            db_task.tags = session.exec(tag_statement).all()
        else:
            # Clear all tags for this task
            db_task.tags = []
    db_task.sqlmodel_update(task_data.model_dump(exclude_unset=True))
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.delete("/tasks/{task_id}")
def remove_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(m.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)  # TODO: need to think about how delete is handled
    session.commit()
    return {"ok": True}

# **** TAGS ****
@router.get("/tags", response_model=List[m.TagResponse])
def get_tags(session: Session = Depends(get_session)):
    return session.exec(select(m.Tag)).all()

@router.post("/tags", response_model=m.TagResponse)
def add_tag(tag_data: m.TagBase, session: Session = Depends(get_session)):
    db_tag = m.Tag.model_validate(tag_data)
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag

@router.delete("/tags/{tag_id}")
def remove_tag(tag_id: int, session: Session = Depends(get_session)):
    tag = session.get(m.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    session.delete(tag)
    session.commit()
    return {"ok": True}