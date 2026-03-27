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



engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, )


def get_session():
    with Session(engine) as session:
        session.exec(text("PRAGMA foreign_keys=ON"))
        status = session.exec(text("PRAGMA foreign_keys")).first()
        logging.debug(f"PRAGMA status: {status}") # Should be 1
        yield session

# implementing contextmanager fix from 
# https://stackoverflow.com/questions/75118223/working-with-generator-context-manager-in-fastapi-db-session
#  for the background session
session_context = contextmanager(get_session)

class DataService:
    @staticmethod
    def init_db():
        """Creates the database and all defined tables."""
        try:
            SQLModel.metadata.create_all(engine)
            with engine.connect() as connection:
                connection.execute(text("PRAGMA foreign_keys=ON"))  # for SQLite only

            logging.info("Database tables initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")

    def cleanup():
        engine.dispose()
        logging.info("Disconnected from database.")
    

class SyncService:
    
    @staticmethod
    def fetch_as_dicts(url: str, feed_id: int) -> List[dict]:
        """
        Fetches data from a single iCal URL and returns a list 
        of dictionaries.
        """
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url)
                response.raise_for_status()
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
        
    @staticmethod
    def sync_ics_to_db(session: Session, incoming_entries: List[dict], feed_id: int):
        """
        Bulk Sync:
        1. Fetches all existing tasks for the specific feed.
        2. Updates or inserts incoming tasks.
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
        
        # commit everything
        session.commit()

    @staticmethod
    def perform_sync(feed_id: int):
        """
        Handles the sync process for a single feed.
        Should be called from a background task.
        """
        # generate our own session
        with session_context() as session:
            feed = session.get(m.Feed, feed_id)
            if not feed:
                logging.error(f"No such feed id: {feed_id}")
                return
            try:
                ics_entries = SyncService.fetch_as_dicts(feed.url, feed.id)
                SyncService.sync_ics_to_db(session, ics_entries, feed.id)

                feed.synced_at = datetime.datetime.now() 
                session.add(feed)
                session.commit()
            
                logging.info(f"SUCCESS: SyncService complete, count: {len(ics_entries)}")

            except Exception as e:
                session.rollback()
                logging.error(f"FAILURE: SyncService rolled back changes for {feed.label}: {e}. ")
            

        
        