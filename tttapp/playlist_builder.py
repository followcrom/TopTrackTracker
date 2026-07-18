# playlist_builder.py
#
# Builds a one-off listening queue: a random sample from the three
# top-track time ranges, topped up with Last.fm similar-track
# recommendations, then starts playback on the active Spotify device.

import csv
import io
import logging
import random
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from spotipy import SpotifyException

from .lastfm_utils import gather_recommendations
from .models import CreatedPlaylist, PlaylistTrack
from .spotify_client import get_spotipy_client
from .user_utils import rate

logger = logging.getLogger(__name__)

TIME_RANGES = [
    ("short_term", "S"),
    ("medium_term", "M"),
    ("long_term", "L"),
]

DEFAULT_FAVORITES = 5
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
                "sources": ["LFM"],
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


# -----------------------------------------


def _next_position():
    top = PlaylistTrack.objects.aggregate(Max("position"))["position__max"]
    return (top or 0) + 1


# -----------------------------------------


def _tracks_to_csv(tracks):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["artist", "song", "uri", "popularity", "album", "release_year", "source_label"]
    )
    for t in tracks:
        writer.writerow(
            [t.artist, t.song, t.uri, t.popularity, t.album, t.release_year, t.source_label]
        )
    return buffer.getvalue()


# -----------------------------------------


def _next_playlist_name():
    highest = 0
    for name in CreatedPlaylist.objects.values_list("name", flat=True):
        match = re.fullmatch(r"TTT_(\d+)", name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"TTT_{highest + 1}"


@login_required
@ratelimit(key="user", rate=rate, block=True)
def build_playlist(request):
    fav_count = _int_param(request, "tracks", DEFAULT_FAVORITES, 0, 20)
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
            # Favorites and LFM are independent counts, so the
            # playlist gets up to fav_count + rec_count tracks.
            top_picks = random.sample(pool, min(fav_count, len(pool)))

            recommendations = []
            if rec_count and settings.LASTFM_API_KEY:
                seeds = random.sample(pool, min(MAX_LASTFM_SEEDS, len(pool)))
                exclude = {
                    (t["artist"].split(" & ")[0].lower(), t["song"].lower())
                    for t in pool
                }
                candidates = gather_recommendations(
                    seeds, settings.LASTFM_API_KEY, rec_count, exclude
                )
                recommendations = _resolve_on_spotify(sp, candidates, rec_count)

            if rec_count and not recommendations:
                message = "No Last.fm recommendations this time - playlist is top tracks only."

            new_tracks = top_picks + recommendations
            random.shuffle(new_tracks)

            existing_uris = set(PlaylistTrack.objects.values_list("uri", flat=True))
            new_tracks = [t for t in new_tracks if t["uri"] not in existing_uris]

            next_position = _next_position()
            PlaylistTrack.objects.bulk_create(
                PlaylistTrack(
                    artist=t["artist"],
                    song=t["song"],
                    uri=t["uri"],
                    popularity=t["popularity"],
                    source_label="/".join(t["sources"]),
                    position=next_position + i,
                )
                for i, t in enumerate(new_tracks)
            )

    playlist = PlaylistTrack.objects.all().order_by("-position")

    return render(
        request,
        "playlist.html",
        {
            "name": "Playlist Builder",
            "playlist": playlist,
            "fav_count": fav_count,
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
            source_label="USER",
            position=_next_position(),
        )
        return JsonResponse({"success": True, "message": "✓ Added to playlist"})

    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)


# -----------------------------------------


@login_required
def add_lastfm_track_to_playlist(request):
    """Homepage Last.fm rows only carry artist/song (no Spotify URI), so
    resolve the track on Spotify here, at add-click time, rather than
    pre-searching every row on page load."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

    artist = request.POST.get("artist", "").strip()
    song = request.POST.get("song", "").strip()
    if not artist or not song:
        return JsonResponse({"success": False, "message": "Missing artist/song."}, status=400)

    sp = get_spotipy_client(request)
    if not sp:
        return JsonResponse(
            {"success": False, "message": "Log into Spotify first (visit Top Tracks), then try again."}
        )

    query = f"track:{song} artist:{artist}"
    try:
        results = sp.search(q=query, type="track", limit=1)
    except SpotifyException as e:
        logger.warning(f"Spotify search failed for {query}: {e.http_status}")
        return JsonResponse({"success": False, "message": "Spotify search failed. Try again shortly."})

    items = results.get("tracks", {}).get("items", [])
    if not items:
        return JsonResponse({"success": False, "message": "✗ Not found on Spotify"})

    track = items[0]
    uri = track["uri"]

    if PlaylistTrack.objects.filter(uri=uri).exists():
        return JsonResponse({"success": False, "message": "✗ Already in playlist"})

    PlaylistTrack.objects.create(
        artist=" & ".join(a["name"] for a in track["artists"]),
        song=track["name"],
        uri=uri,
        popularity=track["popularity"],
        source_label="USER",
        position=_next_position(),
    )
    return JsonResponse({"success": True, "message": "✓ Added to playlist"})


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

    uris = list(
        PlaylistTrack.objects.order_by("-position").values_list("uri", flat=True)
    )
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


# -----------------------------------------


@login_required
@require_POST
def shuffle_playlist_tracks(request):
    tracks = list(PlaylistTrack.objects.all())
    ids = [t.id for t in tracks]
    random.shuffle(ids)

    by_id = {t.id: t for t in tracks}
    for new_position, track_id in enumerate(reversed(ids), start=1):
        by_id[track_id].position = new_position

    PlaylistTrack.objects.bulk_update(tracks, ["position"])
    return redirect("build_playlist")


# -----------------------------------------


@login_required
@ratelimit(key="user", rate=rate, block=True)
def create_spotify_playlist(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

    sp = get_spotipy_client(request)
    if not sp:
        return JsonResponse(
            {"success": False, "message": "Spotify session expired - reload the page."}
        )

    tracks = list(PlaylistTrack.objects.order_by("-position"))
    if not tracks:
        return JsonResponse({"success": False, "message": "No tracks in the playlist yet."})

    name = _next_playlist_name()
    uris = [t.uri for t in tracks]

    try:
        user_id = sp.current_user()["id"]
        playlist = sp.user_playlist_create(user_id, name, public=False)
        sp.playlist_add_items(playlist["id"], uris)
    except SpotifyException as e:
        logger.error(f"Creating Spotify playlist failed: {e.http_status}")
        return JsonResponse({"success": False, "message": f"Spotify error: {e.msg}"})

    CreatedPlaylist.objects.create(
        name=name,
        spotify_playlist_id=playlist["id"],
        csv_data=_tracks_to_csv(tracks),
    )

    return JsonResponse(
        {"success": True, "message": f"Created '{name}' on Spotify ({len(uris)} tracks) ♫"}
    )
