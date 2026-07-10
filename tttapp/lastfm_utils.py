# lastfm_utils.py
#
# Helpers for the Last.fm API (https://www.last.fm/api).
# All calls here are read-only and key-authenticated - no user session needed.

import logging
import random

import requests

logger = logging.getLogger(__name__)

LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"
REQUEST_TIMEOUT = 10  # seconds


# -----------------------------------------


def lastfm_call(method, api_key, params=None):
    base_params = {"method": method, "api_key": api_key, "format": "json"}
    if params:
        base_params.update(params)
    response = requests.get(
        LASTFM_BASE_URL, params=base_params, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


# -----------------------------------------


def get_similar_tracks(artist, track, api_key, limit=20):
    """Return a list of (artist, track) pairs similar to the given track,
    best match first. Returns [] on any API failure."""
    try:
        data = lastfm_call(
            "track.getSimilar",
            api_key,
            {"artist": artist, "track": track, "limit": limit, "autocorrect": 1},
        )
    except (requests.RequestException, ValueError) as e:
        logger.warning(f"Last.fm track.getSimilar failed for {artist} - {track}: {e}")
        return []

    similar = data.get("similartracks", {}).get("track", [])
    return [
        (t["artist"]["name"], t["name"])
        for t in similar
        if isinstance(t, dict) and t.get("artist") and t.get("name")
    ]


# -----------------------------------------


def gather_recommendations(seed_tracks, api_key, wanted, exclude_keys):
    """Build a shuffled pool of recommended {"artist", "song"} dicts from
    Last.fm, seeded by the user's own top tracks.

    seed_tracks: list of dicts with "artist" and "song" keys
    wanted: how many recommendations the caller ultimately needs; we
            over-collect (3x) because some won't resolve on Spotify later
    exclude_keys: set of (artist_lower, track_lower) the caller already has
    """
    candidates = []
    seen = set(exclude_keys)

    for seed in seed_tracks:
        # Artist strings from Spotify may be "A & B" joins; Last.fm wants one name
        seed_artist = seed["artist"].split(" & ")[0]
        for artist, track in get_similar_tracks(seed_artist, seed["song"], api_key):
            key = (artist.lower(), track.lower())
            if key in seen:
                continue
            seen.add(key)
            candidates.append({"artist": artist, "song": track})
        if len(candidates) >= wanted * 3:
            break

    random.shuffle(candidates)
    return candidates
