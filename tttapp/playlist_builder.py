# playlist_builder.py
#
# Builds a one-off listening queue: a random sample from the three
# top-track time ranges, topped up with Last.fm similar-track
# recommendations, then starts playback on the active Spotify device.

import logging
import random

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from spotipy import SpotifyException

from .lastfm_utils import gather_recommendations
from .models import PlaylistTrack
from .spotify_client import get_spotipy_client
from .user_utils import rate

logger = logging.getLogger(__name__)

TIME_RANGES = [
    ("short_term", "S"),
    ("medium_term", "M"),
    ("long_term", "L"),
]

DEFAULT_TOTAL = 5
DEFAULT_RECS = 2  # number of Last.fm recommendations to include
MAX_LASTFM_SEEDS = 8


# -----------------------------------------


def _gather_top_pool(sp):
    """Fetch the top 50 for each time range and dedupe by URI.

    Returns a list of dicts with artist / song / uri / sources, where
    sources is e.g. ["S", "M"] if a track appears in both the short and
    medium term lists. No per-track genre lookups here - keeps this to
    three Spotify calls total.
    """
    pool = {}
    for time_range, label in TIME_RANGES:
        results = sp.current_user_top_tracks(time_range=time_range, limit=50)
        for item in results["items"]:
            uri = item["uri"]
            if uri in pool:
                pool[uri]["sources"].append(label)
            else:
                pool[uri] = {
                    "artist": " & ".join(a["name"] for a in item["artists"]),
                    "song": item["name"],
                    "uri": uri,
                    "popularity": item["popularity"],
                    "sources": [label],
                }
    return list(pool.values())


# -----------------------------------------


def _resolve_on_spotify(sp, candidates, wanted):
    """Resolve (artist, song) candidates to Spotify tracks via search,
    stopping once we have enough. Candidates that don't match are skipped."""
    resolved = []
    for cand in candidates:
        if len(resolved) >= wanted:
            break
        query = f"track:{cand['song']} artist:{cand['artist']}"
        try:
            results = sp.search(q=query, type="track", limit=1)
        except SpotifyException as e:
            logger.warning(f"Spotify search failed for {query}: {e.http_status}")
            continue
        items = results.get("tracks", {}).get("items", [])
        if not items:
            continue
        track = items[0]
        resolved.append(
            {
                "artist": " & ".join(a["name"] for a in track["artists"]),
                "song": track["name"],
                "uri": track["uri"],
                "popularity": track["popularity"],
                "sources": ["NEW"],
            }
        )
    return resolved


# -----------------------------------------


def _int_param(request, name, default, lo, hi):
    try:
        value = int(request.GET.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, value))


@login_required
@ratelimit(key="user", rate=rate, block=True)
def build_playlist(request):
    total = _int_param(request, "tracks", DEFAULT_TOTAL, 1, 100)
    rec_count = _int_param(request, "recs", DEFAULT_RECS, 0, 20)
    message = ""

    # Reshuffle form submits "tracks" - rebuild the whole playlist from
    # Spotify top tracks + Last.fm recs. A plain page load just shows
    # whatever's already been added (manually or by a previous Reshuffle).
    if "tracks" in request.GET:
        request.session["pre_auth_url"] = request.get_full_path()
        request.session.modified = True

        sp = get_spotipy_client(request)
        if not sp:
            return redirect("spotify_auth")

        try:
            pool = _gather_top_pool(sp)
        except SpotifyException as e:
            logger.error(f"Fetching top tracks failed: {e.http_status}")
            pool = []
            message = "Could not fetch your top tracks from Spotify. Try again shortly."

        if pool:
            # "recs" is an absolute number of songs; it can't exceed the total
            rec_target = min(rec_count, total)
            top_target = total - rec_target

            top_picks = random.sample(pool, min(top_target, len(pool)))

            recommendations = []
            if rec_target and settings.LASTFM_API_KEY:
                seeds = random.sample(pool, min(MAX_LASTFM_SEEDS, len(pool)))
                exclude = {
                    (t["artist"].split(" & ")[0].lower(), t["song"].lower())
                    for t in pool
                }
                candidates = gather_recommendations(
                    seeds, settings.LASTFM_API_KEY, rec_target, exclude
                )
                recommendations = _resolve_on_spotify(sp, candidates, rec_target)

            if rec_target and not recommendations:
                message = "No Last.fm recommendations this time - playlist is top tracks only."

            new_tracks = top_picks + recommendations
            random.shuffle(new_tracks)

            existing_uris = set(PlaylistTrack.objects.values_list("uri", flat=True))
            new_tracks = [t for t in new_tracks if t["uri"] not in existing_uris]

            PlaylistTrack.objects.bulk_create(
                PlaylistTrack(
                    artist=t["artist"],
                    song=t["song"],
                    uri=t["uri"],
                    popularity=t["popularity"],
                    source_label="/".join(t["sources"]),
                )
                for t in new_tracks
            )

    playlist = PlaylistTrack.objects.all().order_by("-id")

    return render(
        request,
        "playlist.html",
        {
            "name": "Playlist Builder",
            "playlist": playlist,
            "total": total,
            "rec_count": rec_count,
            "message": message,
        },
    )


# -----------------------------------------


@login_required
def add_to_playlist(request):
    if request.method == "POST":
        uri = request.POST.get("uri")

        if PlaylistTrack.objects.filter(uri=uri).exists():
            return JsonResponse({"success": False, "message": "✗ Already in playlist"})

        PlaylistTrack.objects.create(
            artist=request.POST.get("artist"),
            song=request.POST.get("song"),
            uri=uri,
            popularity=request.POST.get("popularity"),
            album=request.POST.get("album", ""),
            release_year=request.POST.get("release_year", ""),
            genres=request.POST.get("genres", ""),
            artist_uri=request.POST.get("artist_uri", ""),
            source_label="USER",
        )
        return JsonResponse({"success": True, "message": "✓ Added to playlist"})

    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)


# -----------------------------------------


@login_required
@require_POST
def delete_playlist_track(request, track_id):
    PlaylistTrack.objects.filter(id=track_id).delete()
    return redirect("build_playlist")


# -----------------------------------------


@login_required
@require_POST
def delete_all_playlist_tracks(request):
    PlaylistTrack.objects.all().delete()
    return redirect("build_playlist")


# -----------------------------------------


@login_required
def play_playlist(request):
    sp = get_spotipy_client(request)
    if not sp:
        return JsonResponse(
            {"success": False, "message": "Spotify session expired - reload the page."}
        )

    uris = list(PlaylistTrack.objects.values_list("uri", flat=True))[::-1]
    if not uris:
        return JsonResponse({"success": False, "message": "No tracks in the playlist yet."})

    try:
        sp.start_playback(uris=uris)
        return JsonResponse(
            {"success": True, "message": f"Playing {len(uris)} tracks ♫"}
        )
    except SpotifyException as e:
        if e.reason == "NO_ACTIVE_DEVICE" or e.http_status == 404:
            msg = "No active Spotify device - start playing anything in the app first, then retry."
        else:
            msg = f"Spotify error: {e.msg}"
        return JsonResponse({"success": False, "message": msg})
