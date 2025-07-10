#!/usr/bin/env python
from ast import RShift
import os
import sys
import time
import json
import requests
import logging
import glob
import shutil
import datetime
import re
from collections import defaultdict
from statistics import median
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import PlainTextResponse
import threading
import asyncio
import uvicorn

# Add the directory of the script to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# initialize fastapi
app = FastAPI()

os.environ["ANKERUSER"] = "YOUR EMAIL HERE" # your anker account email
os.environ["ANKERPASSWORD"] = "YOUR PASSWORD HERE" # your anker password
os.environ["ANKERCOUNTRY"] = "DE" # your region for anker
SIGNAL_SENDER = "+49160123456"
SIGNAL_TARGET = "+491601234567"

ANKER_SOLIX_DUID = "APCGQ80E22600912_" # avoids the solix uids to be part of the key name adjust your value here
ANKER_SOLIX_SITE_REFRESH_WAITING = 8 # sec to wait before repulling data, note pulling data, does not mean you get new data, sometimes it provides still olds
ANKER_SOLIX_DEVICE_REFRESH_WAITING = 8 # sec to wait before repulling data, note pulling data, does not mean you get new data, sometimes it provides still olds
ANKER_SOLIX_ENERGYSTATS_REFRESH_WAITING = 60 # sec to wait before repulling data, note pulling data, does not mean you get new data, sometimes it provides still olds
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather?lat=XX&lon=XX&appid=YOUR TOKEN"
WEATHER_API_REFRESH_WAITING = 60 # every 60s refresh weather from api, get temps, clouds, rain etc, 60s is for free
LOOP_API_SLEEP_WAITING = 10 # sleep timer to avoid high cpu load
LOOP_API_DEEPSLEEP_WAITING = 60 # sleep timer if solix goes into sleep mode normally arround 10%, slow down calls as api will not respond with new data anyway
LOG_DIR = "/app" # your local path where to put logs, results in /mnt/anker/latest.log and /mnt/anker/logs/yyy-mm-dd.log files
LOG_RETENTION_TIME = 7 # dates of logs to keep

"""Example exec module to use the Anker API for continuously querying and
displaying important solarbank parameters This module will prompt for the Anker
account details if not pre-set in the header.  Upon successful authentication,
you will see the solarbank parameters displayed and refreshed at regular
interval.

Note: When the system owning account is used, more details for the solarbank
can be queried and displayed.

Attention: During execution of this module, the used account cannot be used in
the Anker App since it will be kicked out on each refresh.

"""  # noqa: D205

import asyncio
import contextlib
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import sys

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError

# Add the anker_solix_api_latest directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'anker_api')))
from anker_api.api import api, errors  # pylint: disable=no-name-in-module
from anker_api.api.apitypes import (  # pylint: disable=no-name-in-module
    SolarbankRatePlan,
    SolarbankUsageMode,
)
import anker_api.common as common

# initial cleaning logs
def delete_old_logs(directory, days=LOG_RETENTION_TIME):
    cutoff_date = datetime.now() - timedelta(days=days)

    for log_file in glob.glob(os.path.join(directory, '*.log')):
        file_creation_date = datetime.fromtimestamp(os.path.getmtime(log_file))

        if file_creation_date < cutoff_date:
            os.remove(log_file)
            logging.info(f"Deleted old log file: {log_file}")


# Initial logging setup
def setup_logger(log_file):
    todays_log_file= f"{LOG_DIR}/logs/{log_file}"
    latest_log_file= f"{LOG_DIR}/latest.log"

    # Delete logs older than 7 days
    delete_old_logs(LOG_DIR+"/logs", days=LOG_RETENTION_TIME)

    logger = logging.getLogger()

    # Clear existing handlers (if any)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Set up new handlers
    file_handler = logging.FileHandler(todays_log_file)

    # Set logging format and level
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    #logger.setLevel(logging.DEBUG)

    if os.path.exists(todays_log_file):
        shutil.copy(todays_log_file, latest_log_file)

_LOGGER: logging.Logger = logging.getLogger(__name__)
CONSOLE: logging.Logger = common.CONSOLE

def clearscreen():
    """Clear the terminal screen."""
    if sys.stdin is sys.__stdin__:  # check if not in IDLE shell
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
        # CONSOLE.info("\033[H\033[2J", end="")  # ESC characters to clear terminal screen, system independent?

# Function to convert JSON to Prometheus format
def json_to_prometheus(data, masterkey=""):
    prometheus_lines = []
    # Regex pattern to match UUIDs followed by an underscore
    pattern = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}_"

    # Remove matches for guids
    masterkey = re.sub(pattern, "", masterkey)

    # Regex pattern to match anker solix uids followed by an underscore
    ankerPattern = r"_[\dA-Z]{16}"

    if isinstance(data, dict):
        for metric_name, metric_values in data.items():
            parsed_line = ""
            if re.search(ankerPattern, masterkey):
                labels = '{device_sn="'+data.get("device_sn", "")+'", alias="'+data.get("alias", "")+'", type="'+data.get("type", "")+'", status="'+data.get("status_desc", "")+'"}'

                # remove the base key from anker solix bank
                parsed_line = f"{json_to_prometheus(metric_values, f'{re.sub(ankerPattern, "", masterkey)}_{metric_name}'+labels)}"
            else:
                parsed_line = f"{json_to_prometheus(metric_values, f'{masterkey}_{metric_name}')}"

            if "strange entry" in parsed_line:
                parsed_line = "# " + parsed_line
            else:
                if any(char.isalpha() for char in parsed_line):
                    prometheus_lines.append(parsed_line)
    elif isinstance(data, bool) or (isinstance(data, str) and data in ["True", "False"]):
        return f"{masterkey} {1 if data == "True" else 0}"
    elif isinstance(data, list):
        for i, d in enumerate(data):
            parsed_line = f"{json_to_prometheus(d, f'{masterkey}_value_{i}')}"

            if "strange entry" in parsed_line:
                parsed_line = "# " + parsed_line
            else:
                if any(char.isalpha() for char in parsed_line):
                    prometheus_lines.append(parsed_line)
    else:
        if isinstance(data, (str)):
            try:
                data = float(data)
            except:
              return f"# strange entry {masterkey} {data} {type(data)}"
            return f"{masterkey} {data}"
        else:
            if data == "":
                return f"# empty {masterkey} {data}"
            elif not data:
                if data == "0" or data == 0:
                    return f"{masterkey} 0.0"
                return f"# null {masterkey} {data}"
            else:
                return f"{masterkey} {data}"
    return '\n'.join(prometheus_lines)

def pvgis_calculate_day():
    # Load JSON data from a file
    file_path = "metrics_pvgis.json"  # Replace with your JSON file path
    with open(file_path, "r") as file:
        data = json.load(file)

    # Process the data to calculate averages
    hourly_data = data.get("outputs", {}).get("hourly", [])
    aggregated_data = defaultdict(list)

    # Organize data by mm.dd.hh.mm and sum "P" values
    for entry in hourly_data:
        timeRecord = entry["time"]  # Example: "20220101:0010"
        p_value = entry["P"]

        # Extract mm.dd.hh.mm
        mm = timeRecord[4:6]
        dd = timeRecord[6:8]
        hh = timeRecord[9:11]
        minute = timeRecord[11:13]
        if dd == '29' and mm == '02':
            continue
        key = f"{mm}.{dd}.{hh}.{minute}"

        aggregated_data[key].append(p_value)

    file_path = "calculations_pvgis.json"

    with open(file_path, "w") as file:
        pass  # Clears the file by opening it in write mode without writing anything

    # Calculate averages and prepare the output
    f = open(file_path, "a")

    min_p_total = 0
    avg_p_total = 0
    max_p_total = 0

    for key, values in sorted(aggregated_data.items()):
        avg_p = sum(values) / len(values)
        min_p = min(values)
        max_p = max(values)
        med_p = median(values)

        # Extract mm.dd.hh.mm
        mm = key[0:2]
        dd = key[3:5]
        hh = key[6:8]
        minute = key[9:11]

        current_month = datetime.now().strftime("%m")
        current_day = datetime.now().strftime("%d")
        current_hour = datetime.now().strftime("%H")

        if mm != current_month or dd != current_day:
            continue

        min_p_total += min_p
        avg_p_total += avg_p
        max_p_total += max_p

        if hh != current_hour:
            continue

        f.write(f'pvgis_api_seriescalc_min {min_p:.2f}\n')
        f.write(f'pvgis_api_seriescalc_avg {avg_p:.2f}\n')
        f.write(f'pvgis_api_seriescalc_max {max_p:.2f}\n')

    f.write(f'pvgis_api_seriescalc_min_total {min_p_total:.2f}\n')
    f.write(f'pvgis_api_seriescalc_avg_total {avg_p_total:.2f}\n')
    f.write(f'pvgis_api_seriescalc_max_total {max_p_total:.2f}\n')
    f.close()

def pvgis_read_calulations():
    file_path = "calculations_pvgis.json"
    if not os.path.exists(file_path):
        pvgis_calculate_day()

    # Load data from a file
    file = open(file_path,"r")
    return file.read()

async def main() -> None:
    while True:
        try:
            current_unixtime = int(time.time())
            sunrise_date = 0
            current_date = 0
            sunrise = 0
            sunset = 0
            deviceResponse = ''
            siteResponse = ''

            """Create the aiohttp session and run the example."""
            CONSOLE.info("Loading Solix API:")
            async with ClientSession() as websession:
                myapi = api.AnkerSolixApi(
                    common.user(),
                    common.password(),
                    common.country(),
                    websession,
                    _LOGGER,
                )

                now = datetime.now().astimezone()
                next_weather_refr = now
                next_site_refr = now
                next_dev_refr = now
                next_stats_refr = now

                # Loop until the current time is within the range
                while True:
                    try:
                        current_unixtime = int(time.time())
                        now = datetime.now().astimezone()

                        if next_dev_refr <= now:
                            CONSOLE.info(now.isoformat()+": Running device details refresh...")
                            await myapi.update_device_details()

                            with open('metrics_device_details.json', 'w') as jsonfile:
                                deviceResponse = myapi.devices
                                json.dump(deviceResponse,jsonfile)

                                url = "http://signal-cli-rest-api:8080/v2/send"
                                headers = {
                                    "Accept": "application/json",
                                    "Content-Type": "application/json"
                                }
                                data = {
                                    "base64_attachments": [],
                                    "message": "BATTERY ALMOST FULL / WASTING SOLAR > 100w",
                                    "number": SIGNAL_SENDER,
                                    "recipients": [SIGNAL_TARGET]
                                }

                        if next_site_refr <= now:
                            CONSOLE.info(now.isoformat()+": Running site refresh...")
                            await myapi.update_sites()

                            with open('metrics_sites.json', 'w') as jsonfile:
                                siteResponse = myapi.sites
                                json.dump(siteResponse,jsonfile)
                            next_site_refr = now + timedelta(seconds=ANKER_SOLIX_SITE_REFRESH_WAITING)

                        if next_weather_refr <= now:
                            CONSOLE.info(now.isoformat()+": Running weather refresh...")
                            data_weather = requests.get(WEATHER_API_URL).json()
                            with open('metrics_weather.json', 'w') as jsonfile:
                                json.dump(data_weather,jsonfile)
                            next_weather_refr = now + timedelta(seconds=WEATHER_API_REFRESH_WAITING)

                            # Extract sunrise and sunset times
                            sunrise = data_weather['sys']['sunrise']
                            sunset = data_weather['sys']['sunset']

				next_dev_refr = now + timedelta(seconds=ANKER_SOLIX_DEVICE_REFRESH_WAITING)

                        if next_stats_refr <= now: # and sunrise <= current_unixtime <= sunset:
                            CONSOLE.info(now.isoformat()+": Running energy details refresh...")
                            await myapi.update_device_energy()

                            with open('metrics_energy_details.json', 'w') as jsonfile:
                                for site_id, site in myapi.sites.items():
                                    json.dump(site.get("energy_details"),jsonfile)
                            next_stats_refr = now + timedelta(seconds=ANKER_SOLIX_ENERGYSTATS_REFRESH_WAITING)

                        current_minute = datetime.now().minute
                        # Replace with the desired minute
                        if current_minute == 13 and current_unixtime > sunrise and current_unixtime < sunset:
                            pvgis_calculate_day()
        ########## READ FILEs here and combine

                        # Open the JSON file and read its contents
                        with open('metrics_weather.json', 'r') as file:
                            metrics_weather = json.load(file)
                        with open('metrics_sites.json', 'r') as file:
                            metrics_sites = json.load(file)
                        with open('metrics_energy_details.json', 'r') as file:
                            metrics_energy = json.load(file)
                        with open('metrics_device_details.json', 'r') as file:
                            metrics_device_details = json.load(file)
                    except Exception as err:
                        if "connect" in str(type(err)).lower():
                            print(f"Connection error: {err}. Type:{str(type(err)).lower()} The connection was reset by the peer. Retrying...")
                            break
                        CONSOLE.exception(now.isoformat()+": %s: %s", type(err), err)

                    if int(deviceResponse[ANKER_SOLIX_DUID[:-1]]['charging_status']) not in {7}:
                        time.sleep(LOOP_API_SLEEP_WAITING)
                    else:
                        CONSOLE.info(now.isoformat() +f": Sleeping {LOOP_API_DEEPSLEEP_WAITING} sec charging_status: {deviceResponse[ANKER_SOLIX_DUID[:-1]]['charging_status']}")
                        time.sleep(LOOP_API_DEEPSLEEP_WAITING)
                # end of while loop
        except (ClientError, errors.AnkerSolixError) as err:
            CONSOLE.error("%s: %s", type(err), err)
        except KeyboardInterrupt:
            CONSOLE.warning("\nAborted!")
        except Exception as exception:  # pylint: disable=broad-exception-caught  # noqa: BLE001
            CONSOLE.exception("%s: %s", type(exception), exception)

# To run the background task on server startup, you can use threading:
def start_background_task():
    thread = threading.Thread(target=run_uvicorn)
    thread.daemon = True  # Daemon thread will stop when the main program exits
    thread.start()

# Start the FastAPI app in the background
def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=9005, log_level="warning")

@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    # Open the JSON file and read its contents
    with open('metrics_weather.json', 'r') as file:
        metrics_weather = json.load(file)
    with open('metrics_sites.json', 'r') as file:
        metrics_sites = json.load(file)
    with open('metrics_energy_details.json', 'r') as file:
        metrics_energy = json.load(file)
    with open('metrics_device_details.json', 'r') as file:
        metrics_device_details = json.load(file)

    results = "\n".join([
        json_to_prometheus(metrics_weather, "open_weather_api"),
        json_to_prometheus(metrics_sites, "anker_solix_api_sites"),
        json_to_prometheus(metrics_energy, "anker_solix_api_energy"),
        json_to_prometheus(metrics_device_details, "anker_solix_api_devices"),
        pvgis_read_calulations()
    ])
    return f"{results}"


# run async main
if __name__ == "__main__":
    # Start the background task
    start_background_task()

    if not asyncio.run(main(), debug=False):
        CONSOLE.warning("\nAborted!")
