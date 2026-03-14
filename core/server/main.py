#
# Abbie Parker
# March 6, 2026
#
# This program will fetch ical and allow customization
#

# main.py
import logging
from server.ics_service import DataService
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from server.api import router as api_router
from fastapi.middleware.trustedhost import TrustedHostMiddleware

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    logging.debug('')
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.debug(f'{__name__}')

    # --- Startup Logic ---
    DataService.init_db()
    logging.info("Database initialized.")
    
    yield  # The app runs while it's "held" here
    
    # --- Shutdown Logic ---
    logging.info("Cleaning up...")
    DataService.cleanup()


app = FastAPI(title="iCalPy+ API", lifespan=lifespan)
app.include_router(api_router)    

# Allows local test.html to talk to this API 
origins = [
    "localhost", # The allowed frontend URL
    "127.0.0.1"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #still in dev mode
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(
#     TrustedHostMiddleware, allowed_hosts=origins
# )

# INIT
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=True)
# TODO: add env settings to set debug load vs production