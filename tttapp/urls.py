# urls.py

from django.urls import path, include
from .views import (
    home,
    top_tracks_short_term,
    top_tracks_medium_term,
    top_tracks_long_term,
)

from .playlist_builder import (
    build_playlist,
    play_playlist,
    add_to_playlist,
    add_lastfm_track_to_playlist,
    delete_playlist_track,
    delete_all_playlist_tracks,
    shuffle_playlist_tracks,
    create_spotify_playlist,
)

from .spotify_client import spotify_auth, spotify_callback


urlpatterns = [
    path("top-tracks/short/", top_tracks_short_term, name="top_tracks_short_term"),
    path("top-tracks/medium/", top_tracks_medium_term, name="top_tracks_medium_term"),
    path("top-tracks/long/", top_tracks_long_term, name="top_tracks_long_term"),
    path("", home, name="home"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("spotify-auth/", spotify_auth, name="spotify_auth"),
    path("callback/", spotify_callback, name="spotify_callback"),
    path("playlist-builder/", build_playlist, name="build_playlist"),
    path("play-playlist/", play_playlist, name="play_playlist"),
    path("add-to-playlist/", add_to_playlist, name="add_to_playlist"),
    path(
        "add-lastfm-to-playlist/",
        add_lastfm_track_to_playlist,
        name="add_lastfm_track_to_playlist",
    ),
    path(
        "delete-playlist-track/<int:track_id>/",
        delete_playlist_track,
        name="delete_playlist_track",
    ),
    path(
        "delete-all-playlist-tracks/",
        delete_all_playlist_tracks,
        name="delete_all_playlist_tracks",
    ),
    path(
        "shuffle-playlist-tracks/",
        shuffle_playlist_tracks,
        name="shuffle_playlist_tracks",
    ),
    path(
        "create-spotify-playlist/",
        create_spotify_playlist,
        name="create_spotify_playlist",
    ),
]
