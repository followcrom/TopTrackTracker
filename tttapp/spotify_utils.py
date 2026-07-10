# spotify_utils.py

from spotipy import SpotifyException
# import logging
# logger = logging.getLogger(__name__)


def fetch_top_tracks(sp, time_range, limit, offset):
    print("Fetching tracks...")
    try:
        results = sp.current_user_top_tracks(
            time_range=time_range, limit=limit, offset=offset
        )

        tracks = process_spotify_results(sp, results)

        return tracks

    except SpotifyException as e:
        print(f"Spotify API request failed: Status {e.http_status}")
        print(f"\nResponse headers: {e.headers}")
        return None


# -----------------------------------------


def process_spotify_results(sp, results):
    print("Processing results...")
    list_of_results = results["items"]
    tracks = []

    for result in list_of_results:
        track_info = extract_track_info(sp, result)
        tracks.append(track_info)

    return tracks


# -----------------------------------------


def extract_track_info(sp, result):
    release_year = (
        result["album"]["release_date"].split("-")[0]
        if result["album"]["release_date"]
        else "Unknown"
    )
    # Extract track ID from URI and construct external URL
    # This will open the track in a browser, which I currently don't want
    track_id = result["uri"].split(':')[2] # could be [-1]?
    external_url = f"https://open.spotify.com/track/{track_id}"

    return {
        "artist": " & ".join(artist["name"] for artist in result["artists"]),
        "song": result["name"],
        "uri": result["uri"],
        "release_year": release_year,
        "album": result["album"]["name"],
        "track_number": result["track_number"],
        "popularity": result["popularity"],
        "external_url": external_url
    }

# -----------------------------------------
