# type: ignore

from wifi import radio
from ssl import create_default_context
from socketpool import SocketPool
from adafruit_requests import Session
from adafruit_connection_manager import connection_manager_close_all

import circuitpython_base64 as base64

import os
import time
import json

import board
from gc import mem_free
from terminalio import FONT
from rgbmatrix import RGBMatrix
from framebufferio import FramebufferDisplay

from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label

from jpegio import JpegDecoder
from displayio import Group, OnDiskBitmap, Bitmap, TileGrid, ColorConverter, Colorspace, release_displays


# PARAMETERS
VERBOSE = False # print data

TEXT_LABEL_LATENCY = 0.06 # scroll speed for top text label (and refresh speed at the end of each scroll) [seconds]
RETRY_LATENCY = 5  # latency (wait) before retrying between iterations after error [seconds]

APP_PATH = "/app/spotify/app.py" # app file path
LOG_PATH = "/code_out.txt" # log file path

WIFI_SSID = os.getenv("CIRCUITPY_WIFI_SSID")
WIFI_PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

SPOTIFY_TOKENS_PATH = "/app/spotify/tokens.json"
SPOTIFY_IMAGE_PATH = "/app/spotify/temp.jpeg"
SPOTIFY_IMAGE_PATH_FILL = "/app/spotify/fill.bmp"

SPOTIFY_REFRESH_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_CURRENTLY_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"

BACKGROUND_COLOR = 0x000000 # black
BIT_DEPTH = 2 # color depth

TEXT_FONT = FONT # default font
TEXT_COLOR = 0x919492 # gray-white


# METHOD TO GET SPOTIFY TOKENS
def get_tokens():
    with open(SPOTIFY_TOKENS_PATH, 'r') as file:
        data = json.load(file) # load tokens from json file
    
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')

    return access_token, refresh_token


# METHOD TO UPDATE SPOTIFY TOKENS
def update_tokens(requests, refresh_token):
    try:
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode('utf-8')
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }

        response = requests.post(SPOTIFY_REFRESH_TOKEN_URL, headers=headers, data=data)

        if response.status_code != 200: # error status code
            exit_code = 1
            return exit_code, None, refresh_token, response

        else:
            exit_code = 0
            tokens = response.json()
            
            if 'refresh_token' in tokens: # refresh token may not be in response
                refresh_token = tokens['refresh_token']

            access_token = tokens['access_token']

            with open(SPOTIFY_TOKENS_PATH, 'w') as file:
                data = {'access_token': access_token, 'refresh_token': refresh_token}
                json.dump(data, file) # write tokens to json file

            return exit_code, access_token, refresh_token, None
    
    except Exception as e:
        if VERBOSE:
            print(f"update_tokens error: {e}")

        with open(LOG_PATH, 'a') as file:
            file.write(f"app error: {APP_PATH}: update_tokens error: {e}\n")
        
        exit_code = 1
        return exit_code, None, None, None


# METHOD TO GET SPOTIFY CURRENTLY PLAYING SONG
def get_currently_playing(requests, access_token):
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(SPOTIFY_CURRENTLY_PLAYING_URL, headers=headers)
        
        if response.status_code not in [200, 204]: # error status code
            exit_code = 1
            return exit_code, None, None, None, None, None, response

        exit_code = 0

        if response.status_code == 204: # no content status code
            # active
            active = False

        elif response.status_code == 200: # success status code
            data = response.json()

            # active
            active = data.get('is_playing')
        
        if active:
            # song name
            song_name = data.get('item', {}).get('name')
            
            # artist list
            artists = data.get('item', {}).get('artists', [{}])
            artist_list = []
            for a in artists:
                artist_list.append(a.get('name'))
            
            # album name
            album_name = data.get('item', {}).get('album', {}).get('name')

            # image url
            images = data.get('item', {}).get('album', {}).get('images', [{}])
            image_url = None
            for i in images:
                if i.get('height') == 64 and i.get('width') == 64:
                    image_url = i.get('url')
                    break
            
            return exit_code, active, song_name, artist_list, album_name, image_url, None
        
        else:
            return exit_code, active, None, None, None, None, None

    except Exception as e:
        if VERBOSE:
            print(f"get_currently_playing error: {e}")

        with open(LOG_PATH, 'a') as file:
            file.write(f"app error: {APP_PATH}: get_currently_playing error: {e}\n")
        
        exit_code = 1
        return exit_code, None, None, None, None, None, None

    
# METHOD TO FORMAT SONG AND ARTIST TEXT
def format_song_artist(song_name, artist_list, spacer=5):
    formatted_song = song_name
    formatted_artist = ', '.join(artist_list)

    formatted_song += f"{spacer * ' '}{formatted_song}" * ((len(formatted_artist) - len(formatted_song)) // (len(formatted_song) + spacer))
    formatted_artist += f"{spacer * ' '}{formatted_artist}" * ((len(formatted_song) - len(formatted_artist)) // (len(formatted_artist) + spacer))

    if len(formatted_song) < spacer: # ensure good length
        formatted_song += f"{(spacer - len(formatted_song)) * ' '}"
    
    if len(formatted_artist) < spacer: # ensure good length
        formatted_artist += f"{(spacer - len(formatted_artist)) * ' '}"
    
    if len(formatted_song) > len(formatted_artist) and len(formatted_song) <= spacer:
        artist_spacer = len(formatted_song) - len(formatted_artist) + spacer
        formatted_song += f"{spacer * ' '}{formatted_song}"
        formatted_artist += f"{artist_spacer * ' '}{formatted_artist}"

    elif len(formatted_song) < len(formatted_artist) and len(formatted_artist) <= spacer:
        song_spacer = len(formatted_artist) - len(formatted_song) + spacer
        formatted_song += f"{song_spacer * ' '}{formatted_song}"
        formatted_artist += f"{spacer * ' '}{formatted_artist}"
    
    if len(formatted_song) > len(formatted_artist):
        formatted_artist += f"{(len(formatted_song) - len(formatted_artist)) * ' '}"
        
    elif len(formatted_song) < len(formatted_artist):
        formatted_song += f"{(len(formatted_artist) - len(formatted_song)) * ' '}"
    
    return formatted_song, formatted_artist


# METHOD TO GET ALBUM ART IMAGE
def get_image(requests, image_url):
    try:
        response = requests.get(image_url)

        if response.status_code != 200: # error status code
            exit_code = 1
            return exit_code, None, response
        
        exit_code = 0
        image_path = SPOTIFY_IMAGE_PATH

        with open(image_path, 'wb') as file:
            file.write(response.content) # write image to jpeg file

        return exit_code, image_path, None

    except Exception as e:
        if VERBOSE:
            print(f"get_image error: {e}")

        with open(LOG_PATH, 'a') as file:
            file.write(f"app error: {APP_PATH}: get_image error: {e}\n")
        
        exit_code = 1
        return exit_code, None, None


# METHOD TO DOWNSAMPLE 64x64 TO 32x32 BITMAP
def downsample_bitmap(bitmap, corner=[0, 0]):
    downsampled_bitmap = Bitmap(32, 32, 65535) # 256-color 16-bit palette
    
    for y in range(0, 64, 2):
        for x in range(0, 64, 2):
            x_shift = corner[0] # corner of 2x2 window to use for downsampling
            y_shift = corner[1]

            downsampled_bitmap[x // 2, y // 2] = bitmap[x + x_shift, y + y_shift]

    return downsampled_bitmap


# METHOD TO SCROLL TEXT HORIZONTALLY
def scroll(label):
    group = label[0]
    group.x -= 1  # move label left

    if group.x < (-1*6*len(label.text) - 32):  # if label has moved full length, refresh to initial position and return True
        group.x = 0
        return True
    
    return False


# WIFI SETUP
radio.connect(WIFI_SSID, WIFI_PASSWORD)

if VERBOSE:
    print(f"connected to {WIFI_SSID}\n")

pool = SocketPool(radio)
context = create_default_context()
requests = Session(pool, context)


# IMAGE DECODER SETUP
decoder = JpegDecoder()


# DISPLAY SETUP
release_displays() # release any existing displays

master_group = Group()
blank_group = Group()

matrix = RGBMatrix(
    width=64,
    height=32,
    bit_depth=BIT_DEPTH,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2,
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
    serpentine=False,
    doublebuffer=True
)

display = FramebufferDisplay(matrix, auto_refresh=True)

# blank rectangle
blank_rectangle = Rect(
    width=64, height=32, x=0, y=0, fill=BACKGROUND_COLOR
)

# draw initialization for blank group
blank_group.append(blank_rectangle)

# placeholder text labels
text_label_top = Label(
    font=TEXT_FONT, color=TEXT_COLOR, text='', x=32, y=10, scale=1
)
text_label_bottom = Label(
    font=TEXT_FONT, color=TEXT_COLOR, text='', x=32, y=22, scale=1
)

# border rectangles
border_rectangle_left = Rect(
    width=32, height=32, x=0, y=0, fill=BACKGROUND_COLOR
)
border_rectangle_right = Rect(
    width=2, height=32, x=62, y=0, fill=BACKGROUND_COLOR
)
border_rectangle_top = Rect(
    width=64, height=2, x=0, y=0, fill=BACKGROUND_COLOR
)
border_rectangle_bottom = Rect(
    width=64, height=2, x=0, y=30, fill=BACKGROUND_COLOR
)

# image and border rectangles
image_bitmap_fill = OnDiskBitmap(SPOTIFY_IMAGE_PATH_FILL) # open fill image bitmap
image_tilegrid_fill = TileGrid(image_bitmap_fill, pixel_shader=image_bitmap_fill.pixel_shader, x=0, y=0) # make tilegrid with fill image bitmap

album_border_rectangle_left = Rect(
    width=2, height=32, x=0, y=0, fill=BACKGROUND_COLOR
)
album_border_rectangle_right = Rect(
    width=2, height=32, x=30, y=0, fill=BACKGROUND_COLOR
)

# draw initialization for master group
master_group.append(text_label_top)
master_group.append(text_label_bottom)

master_group.append(border_rectangle_left)
master_group.append(border_rectangle_right)

master_group.append(image_tilegrid_fill)

master_group.append(border_rectangle_top)
master_group.append(border_rectangle_bottom)

master_group.append(album_border_rectangle_left)
master_group.append(album_border_rectangle_right)

# set display root group to master group and refresh display to update
display.root_group = master_group
display.refresh()


# MAIN LOOP TO SHOW SONGS
setup = False
reset = True
previous_image_url = None

while True:
    if reset:
        if VERBOSE:
            print(f"setup: {setup}")
            print(f"free memory: {mem_free()}")

        if mem_free() < 1000: # reset if low memory
            display.root_group = blank_group
            display.refresh()
            break

        # get saved tokens and currently playing song
        access_token, refresh_token = get_tokens()
        
        if VERBOSE:
            print(f"access token: {access_token}")
            print(f"refresh token: {refresh_token}")
        
        exit_code, active, song_name, artist_list, album_name, image_url, response = get_currently_playing(requests, access_token)

        if VERBOSE:
            print(f"exit_code [get_currently_playing]: {exit_code}")
            
        # update tokens if expired and get currently playing song
        if exit_code == 1:
            exit_code, access_token, refresh_token, response = update_tokens(requests, refresh_token) # get new tokens

            if VERBOSE:
                print(f"exit_code [update_tokens]: {exit_code}")

            if exit_code == 0:
                exit_code, active, song_name, artist_list, album_name, image_url, response = get_currently_playing(requests, access_token)
                
                if VERBOSE:
                    print(f"exit_code [get_currently_playing]: {exit_code}")
        
        if VERBOSE:
            print(f"active: {active}")

        # get song details if active and update on master group
        if exit_code == 0 and active:
            if VERBOSE:
                print(f"song_name: {song_name}")
                print(f"artist_list: {artist_list}")
                print(f"album_name: {album_name}")
                print(f"image_url: {image_url}")

            # mark setup as complete
            setup = True
            
            # format song and artist text
            formatted_song, formatted_artist = format_song_artist(song_name, artist_list)
            
            if VERBOSE:
                print(f"formatted_song: {formatted_song}")
                print(f"formatted_artist: {formatted_artist}")
            
            # draw text 
            text_label_top = Label(
                font=TEXT_FONT, color=TEXT_COLOR, text=formatted_song, x=64, y=10, scale=1
            )
            text_label_bottom = Label(
                font=TEXT_FONT, color=TEXT_COLOR, text=formatted_artist, x=64, y=22, scale=1
            )
            
            # update text labels on master group
            master_group.pop(0)
            master_group.insert(0, text_label_top)

            master_group.pop(1)
            master_group.insert(1, text_label_bottom)

        else:
            # mark setup as incomplete
            setup = False
            
        # get new image and update on master group
        if image_url != previous_image_url:
            previous_image_url = image_url

            if image_url == None:
                image_tilegrid = image_tilegrid_fill # placeholder fill image

            else:
                exit_code, image_file, response = get_image(requests, image_url)

                if VERBOSE:
                    print(f"exit_code [get_image]: {exit_code}")

                if exit_code == 0:
                    width, height = decoder.open(image_file) # open jpeg file
                    bitmap = Bitmap(width, height, 65535) # create a blank bitmap (256-color 16-bit palette)
                    decoder.decode(bitmap) # decode the jpeg into the blank bitmap

                    downsampled_bitmap = downsample_bitmap(bitmap, corner=[0, 0]) # downsample 64x64 to 32x32 bitmap
                    
                    pixel_shader = ColorConverter(input_colorspace=Colorspace.RGB565_SWAPPED)
                    image_tilegrid = TileGrid(downsampled_bitmap, pixel_shader=pixel_shader, x=0, y=0) # make tilegrid with decoded bitmap

                if exit_code == 1:
                    image_tilegrid = image_tilegrid_fill # placeholder fill image

            # update image on master group
            master_group.pop(4)
            master_group.insert(4, image_tilegrid)

        # set display root group to master group
        display.root_group = master_group

    # if setup completed
    if setup:
        # scroll text and update reset condition
        reset = scroll(text_label_top) or scroll(text_label_bottom) # scroll both text labels

        # refresh display to update
        if not reset:
            display.refresh(minimum_frames_per_second=0)
        
        # wait before next iteration
        time.sleep(TEXT_LABEL_LATENCY)

    # if setup failed
    else:
        reset = True
        
        # wait before retrying
        time.sleep(RETRY_LATENCY)


# CLEANUP
display.root_group = blank_group
connection_manager_close_all(pool)
