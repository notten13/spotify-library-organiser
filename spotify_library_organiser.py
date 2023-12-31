import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

## Methods

def debug(msg):
  if os.getenv("DEBUG") == "True":
    print("[DEBUG] " + msg)

load_dotenv()

scope = "user-library-read,user-library-modify,user-follow-read,user-follow-modify"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

def chunk_list(list, chunk_size):
  """Split a list into chunks of chunk_size elements"""
  chunked_list = []
  for i in range(0, len(list), chunk_size):
    chunked_list.append(list[i:i + chunk_size])
  return chunked_list

def fetch_saved_tracks():
  """Fetch all the tracks saved in user's library"""
  saved_tracks = []
  more_saved_tracks = True
  limit = 50
  offset = 0

  print("⏳ Fetching saved tracks (this can take a while...)")

  while more_saved_tracks == True:
    result = sp.current_user_saved_tracks(limit, offset)
    saved_tracks_ids = list(map(lambda t: t["track"]["id"], result["items"]))
    saved_tracks += saved_tracks_ids
    offset += limit
    more_saved_tracks = len(result["items"]) == limit
  
  return saved_tracks

def fetch_followed_artists():
  """Fetch all the artists followed by user"""
  followed_artists = []
  more_followed_artists = True
  limit = 50
  last_artist_id = None

  print("⏳ Fetching followed artists (this can take a while...)")

  while more_followed_artists == True:
    result = sp.current_user_followed_artists(limit, last_artist_id)
    followed_artists_ids = list(map(lambda a: a["id"], result["artists"]["items"]))
    followed_artists += followed_artists_ids
    last_artist_id = result["artists"]["items"][-1]["id"]
    more_followed_artists = len(result["artists"]["items"]) == limit
  
  return followed_artists

def delete_saved_tracks_not_on_saved_albums(saved_tracks, tracks_that_should_be_saved):
  """Deletes all tracks that are currently saved, but not on a saved album"""
  to_delete = list(filter(lambda x: x not in tracks_that_should_be_saved, saved_tracks))

  if(len(to_delete) > 0):
    print("⏳ Deleting tracks that are not in saved albums...")
    # Spotify accepts up to 50 tracks in each API request
    to_delete_chunks = chunk_list(to_delete, 50)
    for idx, to_delete_chunk in enumerate(to_delete_chunks):
      debug("Deleting tracks: " + ' '.join(map(str, to_delete_chunks)))
      sp.current_user_saved_tracks_delete(to_delete_chunk)

def unfollow_artists_not_on_saved_albums(followed_artists, artists_that_should_be_followed):
  """Unfollow artists that are currently followed, but not on a saved album"""
  to_delete = list(filter(lambda a: a not in artists_that_should_be_followed, followed_artists))

  if(len(to_delete) > 0):
    print("⏳ Unfollowing artists that are not in saved albums...")
    # Spotify accepts up to 50 tracks in each API request
    to_delete_chunks = chunk_list(to_delete, 50)
    for idx, to_delete_chunk in enumerate(to_delete_chunks):
      debug("Deleting artists: " + ' '.join(map(str, to_delete_chunks)))
      sp.user_unfollow_artists(to_delete_chunk)

def update_library_from_saved_albums(saved_tracks, followed_artists):
  """Get all of the user's saved albums and make sure all the tracks on each album are saved
  in the 'Liked Songs' playlist."""
  print("⏳ Savings all tracks that are on saved albums...")
  
  more_saved_albums = True
  tracks_that_should_be_saved = []
  artists_that_should_be_followed = []
  limit = 50
  offset = 0

  while more_saved_albums == True:
    saved_albums = sp.current_user_saved_albums(limit, offset)

    for idx, saved_album in enumerate(saved_albums['items']):
      debug("Album: " + saved_album["album"]["name"])

      album_tracks = saved_album["album"]["tracks"]["items"]
      album_artists = saved_album["album"]["artists"]
      
      track_ids = list(map(lambda t: t["id"], album_tracks))
      artists_ids = list(map(lambda a: a["id"], album_artists))
      
      tracks_that_should_be_saved += track_ids
      artists_that_should_be_followed += artists_ids

      # Make sure all tracks are saved
      tracks_to_save = []

      for idy, track in enumerate(album_tracks):
        if(track["id"] in saved_tracks):
          debug("Track already saved: " + track["name"])
        else:
          debug("Saving track: " + track["name"])
          tracks_to_save.append(track["id"])

      if (len(tracks_to_save) > 0):
        sp.current_user_saved_tracks_add(tracks_to_save)

      # Make sure all artists are followed
      artists_to_follow = []

      for idz, artist in enumerate(album_artists):
        if(artist["id"] in followed_artists):
          debug("Artists already followed: " + artist["name"])
        else:
          debug("Following artist: " + artist["name"])
          artists_to_follow.append(artist["id"])
      
      if(len(artists_to_follow) > 0):
        sp.user_follow_artists(artists_to_follow)

    offset += limit
    more_saved_albums = len(saved_albums["items"]) == limit

  return tracks_that_should_be_saved, artists_that_should_be_followed

##################
## Begin script ##
##################

saved_tracks = fetch_saved_tracks()

followed_artists = fetch_followed_artists()

tracks_that_should_be_saved, artists_that_should_be_followed = update_library_from_saved_albums(saved_tracks, followed_artists)

delete_saved_tracks_not_on_saved_albums(saved_tracks, tracks_that_should_be_saved)

unfollow_artists_not_on_saved_albums(followed_artists, artists_that_should_be_followed)

print("✅ Done!")
