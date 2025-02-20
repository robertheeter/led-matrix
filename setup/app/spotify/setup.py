import os
import json

from spotipy.oauth2 import Spotify, SpotifyOAuth


# PARAMETERS
SPOTIFY_CLIENT_ID = "" # string of alphanumeric characters
SPOTIFY_CLIENT_SECRET = "" # string of alphanumeric characters
SPOTIPY_REDIRECT_URI = "" # should likely be a https:// type address

SPOTIFY_CACHE_PATH = ".cache" # path to token cache file
SPOTIFY_TOKENS_PATH = "tokens.json" # path to token json file


# AUTHORIZATION VIA SPOTIPY
if os.path.exists(SPOTIFY_CACHE_PATH):
    os.remove(SPOTIFY_CACHE_PATH) # delete any cached access tokens to generate a new access token

if os.path.exists(SPOTIFY_TOKENS_PATH):
    os.remove(SPOTIFY_TOKENS_PATH) # delete any existing token json file

scope = 'user-read-currently-playing user-read-playback-state'
sp = Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI))

currently_playing = sp.current_user_playing_track() # check access token by getting currently playing track
song_name = currently_playing['item']['name']

print(f"currently playing: {song_name}")


# FORMAT TOKENS
with open(SPOTIFY_CACHE_PATH, 'r') as file:
    data = json.load(file) # load tokens from cache json file

access_token = data.get('access_token')
refresh_token = data.get('refresh_token')

with open(SPOTIFY_TOKENS_PATH, 'w') as file:
    data = {'access_token': access_token, 'refresh_token': refresh_token}
    json.dump(data, file) # write tokens to token json file
