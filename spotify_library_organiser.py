import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def debug(msg):
  if os.getenv("DEBUG") == "True":
    print("[DEBUG] " + msg)

load_dotenv()

scope = "user-library-read,user-library-modify,user-follow-read,user-follow-modify"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

limit = 50
offset = 0
finished = False

while finished == False:
  saved_albums = sp.current_user_saved_albums(limit, offset)

  for idx, saved_album in enumerate(saved_albums['items']):
      debug("Album: " + saved_album["album"]["name"])

      album_tracks = saved_album['album']['tracks']['items']

      track_ids = list(map(lambda t: t["id"], album_tracks))
    
      saved_statuses = sp.current_user_saved_tracks_contains(track_ids)

      tracks_to_save = []
      for idy, track in enumerate(album_tracks):
        if(saved_statuses[idy] == True):
          debug("Track already saved: " + track["name"])
        else:
          debug("Saving track: " + track["name"])
          tracks_to_save.append(track["id"])

      if (len(tracks_to_save) > 0):
        sp.current_user_saved_tracks_add(tracks_to_save)

  offset += limit
  finished = len(saved_albums["items"]) < limit

print("✅ Done!")