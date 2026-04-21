#
# Abbie Parker
# March 6, 2026
#
# This code will fetch and parse the ical data
#

#TODO: consider renaming this file to service.py or services.py

#imports
import logging, httpx
from icalendar import Calendar
import datetime
from contextlib import contextmanager
import server.schemas as m
from sqlmodel import SQLModel, Session, create_engine, select, text
from sqlalchemy import event
from typing import List, Dict, Set


#constants
DB_NAME = "icalpy_plus.sqlite3"
DATABASE_URL = f"sqlite:///{DB_NAME}"

class DataService:
    def __init__(self):
        self.url = DATABASE_URL
        self.engine = create_engine(
            self.url, 
            connect_args={"check_same_thread": False}
        )
        self.init_db()

    def init_db(self):
        """Creates the database and all defined tables."""
        try:
            SQLModel.metadata.create_all(self.engine)
            logging.info("Database tables initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")

    def cleanup(self):
        self.engine.dispose()
        logging.info("Disconnected from database.")
    
    def get_session(self):
        """Session for FastAPI"""
        with Session(self.engine) as session:
            session.exec(text("PRAGMA foreign_keys=ON"))
            yield session

    @contextmanager
    def session_context(self):
        """Standard context manager for processing ics file"""
        with Session(self.engine) as session:
            session.exec(text("PRAGMA foreign_keys=ON"))
            # status = session.exec(text("PRAGMA foreign_keys")).first()
            # logging.debug(f"PRAGMA status: {status}") # Should be 1
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()


class SyncService:
    def __init__(self, data_service: DataService):
        self.data_service = data_service
    
    def _fetch(self, url: str, feed_id: int) -> List[dict]:
        """
        Fetches data from a single iCal URL and returns a list 
        of dictionaries.
        """
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url)
                response.raise_for_status() # check for error
                calendar = Calendar.from_ical(response.content)
            
            entries = []
            for component in calendar.walk():
                if component.name == "VEVENT":
                    # logging.debug(f"DEBUG: Raw DT: {component.get('dtstart').dt} | Type: {type(component.get('dtstart').dt)}")
                    # TODO: user flag for all_day events
                    task_date = component.get('dtstart').dt
                    if task_date is datetime.date:
                        str_date = task_date.strftime('%Y-%m-%dT12:00:00') # noon hack for all day events
                    else:
                        str_date = task_date.isoformat()

                    logging.debug(f"DEBUG: converted DT: {str_date} | Type: {type(component.get('dtstart').dt)}")

                    entries.append({
                        "uid": str(component.get('uid')),
                        "summary": str(component.get('summary')),
                        "description": str(component.get('description', '')),
                        "start_time": str_date,
                        "source_id": feed_id
                    })
            return entries
        except Exception as e:
            logging.error(f"FAILURE: SyncService Error: {e}")
            raise e
        
    
    def _process_feed(self, session: Session, incoming_entries: List[dict], feed_id: int):
        """
        Bulk Process:
        1. Fetches all existing tasks for the specific feed.
        2. Decides Updates or inserts incoming tasks.
        3. Deletes tasks that exist in DB for this feed but are missing from incoming data.
        """
        if not incoming_entries and not feed_id:
            return

        # Fetch all from db
        statement = select(m.Task).where(m.Task.source_id == feed_id)
        result = session.exec(statement)
        existing_tasks = {t.uid: t for t in result.all()}

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
        
    def sync_feed(self, feed_id: int):
        """
        Handles the sync process for a single feed.
        Should be called from a background task.
        """
        # generate our own session
        with self.data_service.session_context() as session:
            feed = session.get(m.Feed, feed_id)
            if not feed:
                logging.error(f"No such feed id: {feed_id}")
                return
            try:
                ics_entries = self._fetch(feed.url, feed.id)
                self._process_feed(session, ics_entries, feed.id)

                feed.synced_at = datetime.datetime.now() 
                session.add(feed)
                # commit is handled by the session_context
                logging.info(f"SUCCESS: SyncService complete, count: {len(ics_entries)}")

            except Exception as e:
                #rollback is handled by the session_context
                logging.error(f"FAILURE: SyncService rolled back changes for {feed.label}: {e}. ")
            

# Create instance of each class 
#TODO: consider reworking this away from a singleton here
data_service = DataService()
sync_service = SyncService(data_service)       
        