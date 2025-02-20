# type: ignore

import os
import board
import time
import touchio


# PARAMETERS
VERBOSE = False # print data

APP_LIST = [
    "app/subway/app.py",
    "app/spotify/app.py"
    ] # list of app file names

APP_INDEX_DEFAULT = 0 # default app index

LOG_PATH = "/code_out.txt" # log file path
MAX_LOG_SIZE = 50000 # max log file size [bytes]

SETUP_DURATION = 10 # duration of setup mode [seconds]
SETUP_LATENCY = 0.1 # latency (wait) between button presses [seconds]

ERROR_LATENCY = 30 # latency (wait) after error before retrying [seconds]


# LOG SETUP
log_size = os.stat(LOG_PATH)[6]

if VERBOSE:
    print(f"log_size: {log_size}")

if log_size > MAX_LOG_SIZE:
    os.remove(LOG_PATH)


# DEVICE SETUP
button_up = touchio.TouchIn(board.BUTTON_UP)
button_down = touchio.TouchIn(board.BUTTON_DOWN)

app_index = APP_INDEX_DEFAULT
start_time = time.time()

while True:
    if button_up.value:
        app_index += 1
        if VERBOSE:
            print("BUTTON UP")
        while button_up.value:
            time.sleep(SETUP_LATENCY)
    
    if button_down.value:
        app_index -= 1
        if VERBOSE:
            print("BUTTON DOWN")
        while button_down.value:
            time.sleep(SETUP_LATENCY)
    
    if app_index > (len(APP_LIST) - 1):
        app_index = len(APP_LIST) - 1
    elif app_index < 0:
        app_index = 0

    time.sleep(SETUP_LATENCY)

    if VERBOSE:
        print(f"app_index: {app_index}")
    
    if time.time() - start_time > SETUP_DURATION:
        break


# START SELECTED APP
app = APP_LIST[app_index]
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
