#
# Abbie Parker
# March 6, 2026
#
# This code will fetch and parse the ical data
#

#imports
import logging
import httpx, random
from uuidbase62 import base62 # will use for fake UID on local tasks
from icalendar import Calendar
import server.schemas as m
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy import event
from typing import List, Dict, Set

DB_NAME = "icalpy_plus.sqlite3"
DATABASE_URL = f"sqlite:///{DB_NAME}"


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Enables foreign key constraints in SQLite. 
    This is required for 'ON DELETE CASCADE' to function correctly.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class SyncService:
    
    @staticmethod
    def fetch_as_dicts(url: str, feed_id: int) -> List[dict]:
        """
        Fetches data from a single iCal URL and returns a list 
        of dictionaries.
        """
        try:
            with httpx.Client() as client:
                response = client.get(url)
                response.raise_for_status()
                calendar = Calendar.from_ical(response.content)
            
            entries = []
            for component in calendar.walk():
                if component.name == "VEVENT":
                    entries.append({
                        "uid": str(component.get('uid')),
                        "summary": str(component.get('summary')),
                        "description": str(component.get('description', '')),
                        "start_time": component.get('dtstart').dt.isoformat(),
                        "source_id": feed_id
                    })
            return entries
        except Exception as e:
            logging.error(f"SyncService Error: {e}")
            raise e
        
    @staticmethod
    def sync_ics_to_db(session: Session, incoming_entries: List[dict], feed_id: int):
        """
        Optimized Bulk Sync with Stale Cleanup:
        1. Fetches all existing tasks for the specific feed.
        2. Updates or inserts incoming tasks.
        3. Deletes tasks that exist in DB for this feed but are missing from incoming data.
        """
        if not incoming_entries and not feed_id:
            return

        # Fetch all from feed
        statement = select(m.Task).where(m.Task.source_id == feed_id)
        existing_tasks: Dict[str, m.Task] = {t.uid: t for t in session.exec(statement).all()}

        # all uids from feed 
        incoming_uids: Set[str] = {e["uid"] for e in incoming_entries}

        # Categorize ics entries into Updates and Inserts
        for entry in incoming_entries:
            uid = entry["uid"]
            if uid in existing_tasks:
                # UPDATE: Only syncable fields are modified
                db_task = existing_tasks[uid]
                db_task.sqlmodel_update(entry)
                session.add(db_task)
            else:
                # INSERT: Create new record
                new_task = m.Task(**entry)
                session.add(new_task)
        
        # handle deletes
        for uid, task_to_check in existing_tasks.items():
            if uid not in incoming_uids:
                session.delete(task_to_check)
        
        # commit everything
        session.commit()

    @staticmethod
    async def perform_sync(session: Session, feed: m.Feed):
        """
        Standalone async function to handle the sync process for a feed.
        Can be called from route handlers or background tasks.
        """
        statement = select(m.selectFeed)
        feeds = session.exec(statement).all()
        
        if not feeds:
            print("Initialization: No feeds found in database.")
            return

        print(f"Initializing sync for {len(feeds)} registered feeds...")
        for feed in feeds:
            try:
                # Fetch entries using the SyncService
                ics_entries = SyncService.fetch_as_dicts(feed.url, feed.id)
                # Process the sync and update the database
                SyncService.sync_ics_to_db(session, ics_entries, feed.id)
                logging.DEBUG(f"  ✓ {feed.label}: Synced {ics_entries.count} tasks.")
            except Exception as e:
                raise Exception(f"Sync process failed for feed {feed.id}: {str(e)}")
