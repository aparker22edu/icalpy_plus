#
# Abbie Parker
# March 6, 2026
#
# This program will fetch ical and allow customization
#

# main.py
import logging
from server.app import ICalPyApp

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

backend = ICalPyApp()
app = backend.app  # for uvicorn

def main():
    logging.debug('')

# INIT
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
# TODO: add env settings to set debug load vs production