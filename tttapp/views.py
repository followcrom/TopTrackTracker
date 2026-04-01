# views.py

from django.shortcuts import redirect, render

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django_ratelimit.decorators import ratelimit

from django.views.decorators.http import require_POST


# -----------------------------------------

from .spotify_client import get_spotipy_client
from .spotify_utils import fetch_top_tracks
from .user_utils import rate


@ratelimit(key="user", rate=rate, block=True)
def top_tracks(request, time_range, name, context):
    request.session["pre_auth_url"] = request.get_full_path()
    print(f"Session pre_auth_url set to: {request.session['pre_auth_url']}")
    request.session.modified = True

    sp = get_spotipy_client(request)

    if not sp:
        print("No spotipy client. Running spotify_callback()")
        return redirect("spotify_auth")

    offset = int(context["offset"])
    limit = 10
    total_tracks = 50
    show_forward = True

    if offset + limit <= total_tracks:
        tracks = fetch_top_tracks(sp, time_range, limit=limit, offset=offset)
        print("Tracks in.")
        # print(f"Tracks: {tracks}")

        if offset >= 40:
            show_forward = False

    else:
        tracks = []
        show_forward = False

    return render(
        request,
        "top_tracks.html",
        {
            "name": name,
            "tracks": tracks if tracks else [],
            "next_offset": context["next_offset"],
            "back_offset": offset - 10 if offset > 0 else 0,
            "show_back": context["show_back"],
            "show_forward": show_forward,
            "time_range": time_range,
        },
    )

# -----------------------------------------


def top_tracks_short_term(request):
    offset = int(request.GET.get("offset", 0))
    limit = 10

    next_offset = offset + limit

    show_back = offset > 0

    context = {
        "offset": offset,
        "next_offset": next_offset,
        "show_back": show_back,
    }

    return top_tracks(request, "short_term", "Top 10 Short Term", context)


# -----------------------------------------


def top_tracks_medium_term(request):
    offset = int(request.GET.get("offset", 0))
    limit = 10

    next_offset = offset + limit

    show_back = offset > 0

    context = {
        "offset": offset,
        "next_offset": next_offset,
        "show_back": show_back,
    }

    return top_tracks(request, "medium_term", "Top 10 Medium Term", context)


# -----------------------------------------


def top_tracks_long_term(request):
    offset = int(request.GET.get("offset", 0))
    limit = 10

    next_offset = offset + limit

    show_back = offset > 0

    context = {
        "offset": offset,
        "next_offset": next_offset,
        "show_back": show_back,
    }

    return top_tracks(request, "long_term", "Top 10 Long Term", context)


# -----------------------------------------
from django.conf import settings

# @login_required
def home(request):
    welcome = "Welcome to followCrom's Top Track Tracker"

    lastfm_api_key = settings.LASTFM_API_KEY
    lastfm_username = settings.LASTFM_USERNAME

    lastfm = lastfm_play_count(lastfm_username, lastfm_api_key)

    return render(request, "home.html", {"welcome": welcome, "lastfm": lastfm})

# -----------------------------------------

import requests
import logging
import time
from datetime import datetime, timedelta
from django.http import JsonResponse


def lastfm_play_count(username, api_key):
    lastfm_info = []

    try:
        # Define the API endpoint for getting user's top tracks
        endpoint = f"http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&user={username}&api_key={api_key}&format=json"

        # Send a GET request to the Last.fm API
        response = requests.get(endpoint)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            top_tracks = data["toptracks"]["track"]

            # Extract the desired information for each track
            for track in top_tracks:
                artist_name = track.get("artist", {}).get("name", "")
                if artist_name in ["Cher", "Meat Loaf", "Sting", "O'Connor"]:
                    continue
                track_info = {
                    "name": track.get("name", ""),
                    "artist": artist_name,
                    "playcount": track.get("playcount", "0"),
                }
                lastfm_info.append(track_info)

    except Exception as e:
        print(f"An error occurred: {e}")
        # Log the error to the console
        logging.error(f"An error occurred: {e}")

    return lastfm_info


# -----------------------------------------

LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"


def _lastfm_call(method, api_key, params=None):
    base_params = {"method": method, "api_key": api_key, "format": "json"}
    if params:
        base_params.update(params)
    response = requests.get(LASTFM_BASE_URL, params=base_params)
    response.raise_for_status()
    return response.json()


def _get_top_tracks(username, api_key, limit=200):
    return _lastfm_call("user.getTopTracks", api_key, {"user": username, "period": "overall", "limit": limit})


def _get_recent_tracks_since(username, api_key, days=90):
    since = datetime.now() - timedelta(days=days)
    from_ts = int(time.mktime(since.timetuple()))
    results = []
    page = 1
    while True:
        data = _lastfm_call("user.getRecentTracks", api_key, {
            "user": username, "from": from_ts, "limit": 200, "page": page
        })
        tracks = data["recenttracks"]["track"]
        if not tracks:
            break
        results.extend(tracks)
        total_pages = int(data["recenttracks"]["@attr"]["totalPages"])
        if page >= total_pages:
            break
        page += 1
    return results


@ratelimit(key="ip", rate="10/m", block=True)
def forgotten_favourites(request):
    api_key = settings.LASTFM_API_KEY
    username = settings.LASTFM_USERNAME

    try:
        top = _get_top_tracks(username, api_key)
        recent = _get_recent_tracks_since(username, api_key)

        recent_keys = {
            (t["artist"]["#text"].lower(), t["name"].lower())
            for t in recent
            if isinstance(t, dict) and "artist" in t
        }

        forgotten = [
            {"artist": t["artist"]["name"], "track": t["name"], "playcount": t["playcount"]}
            for t in top["toptracks"]["track"]
            if (t["artist"]["name"].lower(), t["name"].lower()) not in recent_keys
        ][:20]

        return JsonResponse({"suggestions": forgotten})

    except Exception as e:
        logging.error(f"forgotten_favourites error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
