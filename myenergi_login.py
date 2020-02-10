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
import pprint
import paho.mqtt.client as mqtt
import schedule
from datetime import datetime
import os
import json
import requests
from requests.auth import HTTPDigestAuth
import urllib.request

config_file = 'config.ini'

###########
## Various URL's..

zappi_base_url = 'https://s9.myenergi.net/'
zappi_status_url = 'https://s9.myenergi.net/cgi-jstatus-Z'
zappi_eco_mode_url = 'https://s9.myenergi.net/cgi-zappi-mode-Z12007471-2-0-0-0000'
zappi_eco_mode_plus_url = 'https://s9.myenergi.net/cgi-zappi-mode-Z12007471-3-0-0-0000'
zappi_smart_boost_url = 'https://s9.myenergi.net/cgi-zappi-mode-Z12007471-0-11-12-0400'

###########


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.info("Startup myenergi_login: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
config_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), config_file)

# Get login details from 'config.ini'
parser = SafeConfigParser()
if os.path.exists(config_file_path):
    logging.info("Loaded config file " + config_file_path)
    #candidates = [ 'config.ini', 'my_config.ini' ]
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

# Get data from server
def get_zappi_status():
    logging.info("Geting Zappi info from Hub..")
    logging.info("login = %s , password = %s" % (hub_serial,hub_password) )
    logging.info("Prepare Session")

    url = 'https://s9.myenergi.net/cgi-jstatus-Z'

    req = urllib.request.Request(url)

    req.add_header('User-Agent', 'Wget/1.14 (linux-gnu)')

    auth_handler = urllib.request.HTTPPasswordMgr()
    auth_handler.add_password(user=hub_serial,
                  uri=url,
                  realm='MyEnergi Telemetry',
                  passwd=hub_password)

    handler = urllib.request.HTTPDigestAuthHandler(auth_handler)
    opener = urllib.request.build_opener(handler)
    urllib.request.install_opener(opener)

    stream = urllib.request.urlopen(req, timeout=20)
    log.debug('Response was %s', stream.getcode())

    logging.info("End update time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("Schedule API update every " + GET_UPDATE_INTERVAL + "min")
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
