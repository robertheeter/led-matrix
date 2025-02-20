# type: ignore

import os
import time
import json


# PARAMETERS
VERBOSE = False # print data

APP_PATH = "/app.json"

LOG_PATH = "/code_out.txt" # log file path
MAX_LOG_SIZE = 50000 # max log file size [bytes]

ERROR_LATENCY = 30 # latency (wait) after error before retrying [seconds]


# LOG SETUP
log_size = os.stat(LOG_PATH)[6]

if VERBOSE:
    print(f"log_size: {log_size}")

if log_size > MAX_LOG_SIZE:
    os.remove(LOG_PATH)


# APP SELECTION
with open(APP_PATH, 'r') as file:
    data = json.load(file) # read previous app from json file

app_list = data['app_list']
previous_app = data['previous_app']
previous_app_index = app_list.index(previous_app)

if previous_app_index == len(app_list) - 1: # select next sequential app
    app = app_list[0]
else:
    app = app_list[previous_app_index + 1]

with open(APP_PATH, 'w') as file:
    data = {'previous_app': app, 'app_list': app_list}
    json.dump(data, file) # write current app to json file


# START SELECTED APP
print(f"app execution: {app}")

complete = False
while not complete:
    try:
        exec(open(f"{app}").read()) # execute app file

        complete = True
        print(f"app completion: {app}")

    except Exception as e:
        print(f"app error: {app}: {e}")

        with open(LOG_PATH, 'a') as file:
            file.write(f"app error: {app}: {e}\n")
        
        complete = False
        
        # wait before retrying
        print(f"app reload: {ERROR_LATENCY} seconds")
        time.sleep(ERROR_LATENCY)
