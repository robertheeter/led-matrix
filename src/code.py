# type: ignore

import os
import time
import json


# PARAMETERS
VERBOSE = False # print data

APP_PATH = "/app.json"

LOG_PATH = "/code_out.txt" # log file path
MAX_LOG_SIZE = 5000 # max log file size [bytes]

ERROR_LATENCY = 30 # latency (wait) after error before retrying [seconds]


# LOG SETUP
log_size = os.stat(LOG_PATH)[6] # get log file size

if VERBOSE:
    print(f"log_size: {log_size}")

if log_size > MAX_LOG_SIZE:
    os.remove(LOG_PATH)


# APP SELECTION
with open(APP_PATH, 'r') as file:
    data = json.load(file) # read previous app from json file

app_list = data['app_list']
previous_app = data['previous_app']
reload = data['reload']

if reload:
    app = previous_app
else:
    previous_app_index = app_list.index(previous_app)
    app = app_list[(previous_app_index + 1) % len(app_list)] # select next sequential app

with open(APP_PATH, 'w') as file:
    data = {'previous_app': app, 'app_list': app_list, 'reload': False}
    json.dump(data, file) # write current app to json file (reload = False since app not completed)


# START SELECTED APP
if VERBOSE:
    print(f"app execution: {app}")

complete = False
while not complete:
    try:
        exec(open(f"{app}").read()) # execute app file

        complete = True
        if VERBOSE:
            print(f"app completion: {app}")

    except Exception as e:
        if VERBOSE:
            print(f"app error: {app}: {e}")

        with open(LOG_PATH, 'a') as file:
            file.write(f"app error: {app}: {e}\n")
        
        complete = False
        
        # wait before retrying
        if VERBOSE:
            print(f"app reload: {ERROR_LATENCY} seconds")
        
        time.sleep(ERROR_LATENCY)

with open(APP_PATH, 'w') as file:
    data = {'previous_app': app, 'app_list': app_list, 'reload': True}
    json.dump(data, file) # write current app to json file (reload = True since app completed)
