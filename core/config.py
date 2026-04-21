#
# Abbie Parker
# April 18, 2026
#
# Loads config.ini
# 

import logging
import configparser
import os

CONFIG_FILE = "config.ini"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, CONFIG_FILE)

DEFAULTS = {
    'view_path': os.path.join(ROOT_DIR, 'view'),
    'port': '8000',
    'default_view': 'kanban'
}

# TODO: This code neeeds refactoring/cleanup
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

def _write_config():
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)
    logging.info("INI file updated and saved")
    config.read(CONFIG_PATH)

if 'SETTINGS' not in config:
    config['SETTINGS'] = DEFAULTS
    # Write them immediately so the file exists for the user to see
    _write_config()

def update_view_path(new_path):
    config['SETTINGS']['view_path'] = os.path.normpath(new_path)
    _write_config()

def update_default_folder(new_folder):
    config['SETTINGS']['default_view'] = new_folder
    _write_config()
    
def update_port(new_port):
    config['SETTINGS']['port'] = new_port
    _write_config()


view_path = config['SETTINGS']['view_path']
port = config.getint('SETTINGS', 'port')

default_folder = config['SETTINGS']['default_view']
