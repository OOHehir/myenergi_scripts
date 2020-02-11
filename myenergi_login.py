#!/usr/bin/python3
#
#   Python Project to collect data from MyEnergi Server
#
#   Feb '20
#
#   Absolutely no warranty, use at your own risk!!
#

import time
from configparser import SafeConfigParser
import logging
import sys
import schedule
from datetime import datetime
import os
import json
import requests
from requests.auth import HTTPDigestAuth
from pprint import pprint

config_file = 'config.ini'

###########
## Various URL's..
## For more see https://github.com/twonk/MyEnergi-App-Api
# Note: Modify Character  X to reflect last digit in Hub serial number

zappi_base_url = 'https://sX.myenergi.net/'
zappi_status_url = 'https://sX.myenergi.net/cgi-jstatus-Z'

###########

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.info("Startup myenergi_login: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
config_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), config_file)

# Get login details from 'config.ini'
parser = SafeConfigParser()
if os.path.exists(config_file_path):
    logging.info("Loaded config file " + config_file_path)
    candidates = config_file_path
    found = parser.read(candidates)
    hub_serial = parser.get('get-myenergi-info', 'hub_serial')
    hub_password = parser.get('get-myenergi-info', 'hub_password')
    zappi_serial = parser.get('get-myenergi-info', 'zappi_serial')
    GET_UPDATE_INTERVAL = parser.get('get-myenergi-info', 'api_update_interval_min')
    logging.info("updating data from API every " + GET_UPDATE_INTERVAL +"min")
else:
    logging.error("ERROR: Config file not found " + config_file_path)
    quit()

# Set server address based on last digit in Hub serial number
zappi_base_url = zappi_base_url[:9] + hub_serial[-1:] + zappi_base_url[10:]
zappi_status_url = zappi_status_url[:9] + hub_serial[-1:] + zappi_status_url[10:]

# Get data from server
def get_zappi_status():
    logging.info("Geting Zappi info from Hub..")
    logging.debug("login = %s , password = %s" % (hub_serial,hub_password))
    logging.info("Based on Hub serial number using base URL: " + zappi_base_url)

    h = {'User-Agent': 'Wget/1.14 (linux-gnu)'}
    
    r = requests.get(zappi_status_url, headers = h, auth=HTTPDigestAuth(hub_serial, hub_password), timeout=10)
    if (r.status_code == 200):
        logging.info("Login successful..") 
    elif (r.status_code == 401):
        logging.info("Login unsuccessful!!! Please check username, password or URL")
        quit()
    else:
        logging.info("login unsuccessful, returned code: " + r.status_code)
        quit()
    
    logging.info(r.headers) 
    pprint(r.json())

    logging.info("End update time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    return ()

#########################################################################################################################
# Run on first time
get_zappi_status()

# Then schedule
logging.info("Schedule API update every " + GET_UPDATE_INTERVAL + "min")
schedule.every(int(GET_UPDATE_INTERVAL)).minutes.do(get_zappi_status)

while True:
    schedule.run_pending()
    time.sleep(1)
