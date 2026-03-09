#
# Abbie Parker
# March 6, 2026
#
# This program will fetch ical and allow customization
#

# main.py
import logging
from server.ics_service import create_db_and_tables
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from server.api import router as api_router



logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    logging.debug('')
    pass

# Initialize the database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.debug(f'{__name__}')

    # --- Startup Logic ---
    create_db_and_tables()
    print("Database initialized.")
    
    yield  # The app runs while it's "held" here
    
    # --- Shutdown Logic (if needed) ---
    print("Cleaning up...")

app = FastAPI(title="iCalPy+ API", lifespan=lifespan)
app.include_router(api_router)    

# Allows your local test.html to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev; narrow this down for production
    allow_methods=["*"],
    allow_headers=["*"],
)
    

# INIT

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=True)