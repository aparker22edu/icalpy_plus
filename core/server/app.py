#
# Abbie Parker
# April 16, 2026
#
# Code to create and manage the app
# 

import logging
import os
from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import FastAPI     
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from server.service import data_service, sync_service
from server.api import router
import config

class ICalPyApp:
    def __init__(self):
        self.data_service = data_service
        self.app = FastAPI(
            title="iCalPy+ API", 
            lifespan=self.lifespan_context
        )

        # locking down url access
        origins = [
            "localhost", # The allowed frontend URL
            "127.0.0.1"
        ]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[origins],  #still in dev mode
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=origins
        )
        
        self.app.include_router(router)

        # Mount views
        self._mount_views(config.view_path)
        # mount default view to root
        default_view = os.path.join(config.view_path, config.default_folder)
        self.app.mount(
            "/", 
            StaticFiles(directory=default_view, html=True), 
            'default'
        )



    # Mount each folder in 'view' 
    def _mount_views(self, view_path):
        """Helper to iterate and mount static directories."""
        if not os.path.exists(view_path):
            return
        #loop through and mount each folder for FastAPI autoload index.html
        for view_name in os.listdir(view_path):
            view_dir = os.path.join(view_path, view_name)
            if os.path.isdir(view_dir):
                self.app.mount(
                    f"/view/{view_name}", 
                    StaticFiles(directory=view_dir, html=True), 
                    name=view_name
                )

    @asynccontextmanager
    async def lifespan_context(self, app: FastAPI):
        logging.debug(f'Lifespan startup in: {__name__}')
        logging.info("Application is starting up...")

        yield  # The application runs while "suspended" here

        # --- Shutdown Logic ---
        logging.info("Application shutting down. Cleaning up...")
        self.data_service.cleanup()