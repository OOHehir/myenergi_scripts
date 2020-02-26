#!/usr/bin/python3
#
#   Python Project to check, at a set time (i.e. start of night rate electricity),
#   battery level of a Nissan Leaf & set the appropriate boost amount on Zappi
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
import pycarwings2

config_file = 'config.ini'

###########
TRUE = 1
FALSE = 0

###########
leaf_battery_kwh = 30
target_leaf_km = 100
winter_time_night_rate_start = '23:05'
summer_time_night_rate_start = '00:05'
target_finish_time = '0500'
sleepsecs = 30     # Time to wait before polling Nissan servers for update
###########
## Various URL's..
## For more see https://github.com/twonk/MyEnergi-App-Api
# Note: Modify Character  X to reflect last digit in Hub serial number

zappi_base_url = 'https://sX.myenergi.net/'
zappi_status_url = 'https://sX.myenergi.net/cgi-jstatus-Z'
# Below - K is KWh to add (eg 10.5) (Pos 52), T is time to be finished (eg 0500) (Pos 54)
zappi_smart_boost_url = 'https://sX.myenergi.net/cgi-zappi-mode-Z12007471-0-10-K-T'

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
    leaf_username = parser.get('get-leaf-info', 'username')
    leaf_password = parser.get('get-leaf-info', 'password')
    nissan_region_code = parser.get('get-leaf-info', 'nissan_region_code')
    battery_cap = int(parser.get('get-leaf-info', 'battery_cap'))
    battery_target_amnt = int(parser.get('get-leaf-info', 'battery_target_amnt'))
    #logging.info("updating data from API every " + GET_UPDATE_INTERVAL +"min")
else:
    logging.error("ERROR: Config file not found " + config_file_path)
    quit()

# Set server address based on last digit in Hub serial number
zappi_base_url = zappi_base_url[:9] + hub_serial[-1:] + zappi_base_url[10:]
zappi_status_url = zappi_status_url[:9] + hub_serial[-1:] + zappi_status_url[10:]
zappi_smart_boost_url = zappi_smart_boost_url[:9] + hub_serial[-1:] + zappi_smart_boost_url[10:]

# Get data from server
def get_zappi_status(parameter):
    logging.info("Geting Zappi info from Hub..")
    logging.debug("login = %s , password = %s" % (hub_serial,hub_password))
    logging.info("Based on Hub serial number using base URL: " + zappi_base_url)

    h = {'User-Agent': 'Wget/1.14 (linux-gnu)'}

    try:
        r = requests.get(zappi_status_url, headers = h, auth=HTTPDigestAuth(hub_serial, hub_password), timeout=10)
    except:
        logging.error("MyEnergi API error")
        return

    if (r.status_code == 200):
        logging.info("Login successful..")
    elif (r.status_code == 401):
        logging.info("Login unsuccessful!!! Please check username, password or URL")
        quit()
    else:
        logging.info("login unsuccessful, returned code: " + r.status_code)
        quit()

    #logging.info(r.headers)
    #pprint(r.json())
    logging.info("End update time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if (parameter):
        logging.info("Searching for.."+ parameter)
        # Return single parameter from json
        data = r.json()
        #print (data['zappi'][0][parameter])
        return (data['zappi'][0][parameter])
    else:
        # Return all data
        return (r.json())

def set_boost_mode(mode, kwh, target_time):
    logging.info("Seting Zappi Smart Charge..")
    logging.debug("login = %s , password = %s" % (hub_serial,hub_password))
    logging.info("Based on Hub serial number using base URL: " + zappi_base_url)
    logging.info("Mode = %s, Target kWh= %2.1f, target time = %s" % (mode, kwh, target_time))

    # Set parameters
    zappi_smart_boost_url_A = zappi_smart_boost_url.replace("K", "%.0f"% (kwh))
    zappi_smart_boost_url_B = zappi_smart_boost_url_A.replace("T", "%s" % (target_time))
    if (mode == 'smart'):
        #Set smart boost mode
        zappi_smart_boost_url_C = zappi_smart_boost_url_B.replace("10", "11")
    else:
         zappi_smart_boost_url_C = zappi_smart_boost_url_B

    logging.info("zappi_smart_boost_url is now: " + zappi_smart_boost_url_C)

    # Build request
    h = {'User-Agent': 'Wget/1.14 (linux-gnu)'}

    try:
        r = requests.get(zappi_smart_boost_url_C, headers = h, auth=HTTPDigestAuth(hub_serial, hub_password), timeout=10)
    except:
        logging.error("MyEnergi API error")
        return

    if (r.status_code == 200):
        data = json.loads(r.text)
        if (data['status'] == 0):
            logging.info("Smart boost set successfully")
        elif (data['status'] == -14):
            logging.info("Smart boost not set, check Kwh (interger only) & Time (15 min intervals only)")
        else:
            logging.info("Smart boost not set, returned code %s" + data['status'])
    else:
        logging.info("login unsuccessful, returned code: " + r.status_code)
        return(-1)

    #logging.info(r.headers)
    pprint(r.json())

    return (data['status'])

def charge_wintertime():
    # Need to check if winter time

    if (time.localtime().tm_isdst == FALSE):
        logging.info("Wintertime in effect, starting charge session")
    else:
        logging.info("Summertime in effect, not starting charge session")


def charge_summertime():
    # Need to check if summertime time
    if (time.localtime().tm_isdst == TRUE):
        logging.info("Summertime in effect, starting charge session")
    else:
        logging.info("Wintertime in effect, charge session should be already started!")


def update_battery_status(leaf, wait_time=1):
    key = leaf.request_update()
    status = leaf.get_status_from_update(key)
    # Currently the nissan servers eventually return status 200 from get_status_from_update(), previously
    # they did not, and it was necessary to check the date returned within get_latest_battery_status().
    while status is None:
        print("Waiting {0} seconds".format(sleepsecs))
        time.sleep(wait_time)
        status = leaf.get_status_from_update(key)
    return status


    ## Get last updated data from Nissan server
def get_leaf_status():
  logging.debug("login = %s , password = %s" % (leaf_username,leaf_password) )
  logging.info("Prepare Session")
  s = pycarwings2.Session(leaf_username, leaf_password, nissan_region_code)
  logging.info("Login...")
  logging.info("Start update time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

  try:
    l = s.get_leaf()
  except:
    logging.error("CarWings API error")
    return

  logging.info("get_latest_battery_status")

  leaf_info = l.get_latest_battery_status()

  if leaf_info:
      logging.info("date %s" % leaf_info.answer["BatteryStatusRecords"]["OperationDateAndTime"])
      logging.info("date %s" % leaf_info.answer["BatteryStatusRecords"]["NotificationDateAndTime"])
      logging.info("battery_capacity2 %s" % leaf_info.answer["BatteryStatusRecords"]["BatteryStatus"]["BatteryCapacity"])
      logging.info("battery_capacity %s" % leaf_info.battery_capacity)
      logging.info("charging_status %s" % leaf_info.charging_status)
      logging.info("battery_capacity %s" % leaf_info.battery_capacity)
      logging.info("battery_remaining_amount %s" % leaf_info.battery_remaining_amount)
      logging.info("charging_status %s" % leaf_info.charging_status)
      logging.info("is_charging %s" % leaf_info.is_charging)
      logging.info("is_quick_charging %s" % leaf_info.is_quick_charging)
      logging.info("plugin_state %s" % leaf_info.plugin_state)
      logging.info("is_connected %s" % leaf_info.is_connected)
      logging.info("is_connected_to_quick_charger %s" % leaf_info.is_connected_to_quick_charger)
      logging.info("time_to_full_trickle %s" % leaf_info.time_to_full_trickle)
      logging.info("time_to_full_l2 %s" % leaf_info.time_to_full_l2)
      logging.info("time_to_full_l2_6kw %s" % leaf_info.time_to_full_l2_6kw)
      logging.info("leaf_info.battery_percent %s" % leaf_info.battery_percent)

      # logging.info("getting climate update")
      # climate = l.get_latest_hvac_status()
      # pprint.pprint(climate)

      logging.info("End update time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      logging.info("Schedule API update every " + GET_UPDATE_INTERVAL + "min")
      return (leaf_info)
  else:
      logging.info("Did not get any response from the API")
      return

def main():
    # Check zappi in eco mode & car connected
    zappi_data = get_zappi_status('')

    if (zappi_data['zappi'][0]['pst'] != 'A') & (zappi_data['zappi'][0]['zmo'] == 3):
        # Get battery charge of leaf -> need to update battery status
        logging.info("Car connected & zappi in Eco+ mode")
        logging.info("Getting latest leaf battery status")

        print("Preparing Carwings Session")
        s = pycarwings2.Session(leaf_username, leaf_password, nissan_region_code)
        print("Login...")

        try:
            leaf = s.get_leaf()
        except:
            logging.error("CarWings API error")
            return

        # Give the nissan servers a bit of a delay so that we don't get stale data
        time.sleep(1)

        # Update servers - warning depletes 12v onboard battery!
        #update_status = update_battery_status(leaf, sleepsecs)

        logging.info("get_latest_battery_status from servers")
        leaf_info = leaf.get_latest_battery_status()
        #start_date = leaf_info.answer["BatteryStatusRecords"]["OperationDateAndTime"]
        #logging.info("start_date=", start_date)

        battery_remaining_amount = int(int(leaf_info.battery_percent) * battery_cap / 100)
        logging.info("Leaf battery remaining amount = %d KwH", battery_remaining_amount)

        if (battery_target_amnt < battery_remaining_amount):
            # Don't need to charge
            logging.info("Current battery charge %d, exceeds target" % battery_remaining_amount)
        else:
            # Need to charge
            add_kwh = (battery_target_amnt - battery_remaining_amount)
            logging.info("Need to add %d Kwh" % add_kwh)
            #set_boost_mode('', add_kwh, '0000')
            # Check Zappi didn't do a hard reset..
            time.sleep(30)
            # Refresh data
            zappi_data = get_zappi_status('')
            if "tbh" not in zappi_data:
                # Not set, try again!
                set_boost_mode('', add_kwh,'0000')

    elif(zappi_data['zappi'][0]['pst'] == 'A'):
        logging.info("Car not connected")
        # Try looping?
        return('Not connected')
    elif(zappi_data['zappi'][0]['zmo'] != 3):
        logging.info("Zappi not in Eco+ mode")
        return('Not in Eco+ mode')
    else:
        logging.info("Unknown error")
        return('Unknown error')


#########################################################################################################################
# Run on first time
pprint(get_zappi_status(''))

main()

# Kwh must be interger (i.e no fractions, time in 15min intervals)
#set_smart_mode(kwh=4, target_time=600)

# Then schedule
#schedule.every(int(GET_UPDATE_INTERVAL)).minutes.do(get_zappi_status)

schedule.every().day.at(winter_time_night_rate_start).do(main)
#schedule.every().day.at(summertime_time_night_rate_start).do(charge_summertime)

logging.info("Entering schedule loop")
while True:
    schedule.run_pending()
    time.sleep(1)
