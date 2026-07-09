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

    periods = [
        ("3month", "3 Months"),
        ("12month", "12 Months"),
    ]

    lastfm_periods = []
    for period, label in periods:
        lastfm_periods.append(
            {
                "label": label,
                "tracks": _top_tracks_for_period(lastfm_username, lastfm_api_key, period),
            }
        )

    return render(
        request, "home.html", {"welcome": welcome, "lastfm_periods": lastfm_periods}
    )

# -----------------------------------------

import requests
import logging

EXCLUDED_ARTISTS = {"Cher", "Meat Loaf", "Sting", "O'Connor"}


def _top_tracks_for_period(username, api_key, period, limit=10):
    tracks = []

    try:
        data = _get_top_tracks(username, api_key, period=period, limit=limit)
        for track in data["toptracks"]["track"]:
            artist_name = track.get("artist", {}).get("name", "")
            if artist_name in EXCLUDED_ARTISTS:
                continue
            tracks.append(
                {
                    "name": track.get("name", ""),
                    "artist": artist_name,
                    "playcount": track.get("playcount", "0"),
                }
            )
    except Exception as e:
        logging.error(f"An error occurred fetching {period} top tracks: {e}")

    return tracks


# -----------------------------------------

LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"


def _lastfm_call(method, api_key, params=None):
    base_params = {"method": method, "api_key": api_key, "format": "json"}
    if params:
        base_params.update(params)
    response = requests.get(LASTFM_BASE_URL, params=base_params, timeout=10)
    response.raise_for_status()
    return response.json()


def _get_top_tracks(username, api_key, period="overall", limit=200):
    return _lastfm_call("user.getTopTracks", api_key, {"user": username, "period": period, "limit": limit})

