#
# Abbie Parker
# March 6, 2026
#
# This program will fetch ical and allow customization
#

# main.py
import logging
import threading
from tray import Tray
from server.app import ICalPyApp
import config

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

backend = ICalPyApp()

def run_server():
    """Function to run uvicorn in a background thread."""
    try:
        import uvicorn
        uvicorn.run(backend.app, host="127.0.0.1", port=config.port)
    except Exception as e:
        logging.error(f"Server failed to start: {e}")

def main():
    logging.debug('')

# INIT
if __name__ == "__main__":
    logging.debug("Starting ICalPy+")

    # Start the Backend Thread
    # daemon=True ensures the server dies when the Tray (main thread) is closed
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Start the Tray UI
    # This is a blocking call—it keeps the script alive
    ui = Tray() 
    ui.run()
