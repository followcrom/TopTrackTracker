# urls.py

from django.urls import path, include
from .views import (
    home,
    top_tracks_short_term,
    top_tracks_medium_term,
    top_tracks_long_term,
    forgotten_favourites,
)

from .trending_tracks import (
    start_spotify_playback,
    add_to_trending,
    view_trending_tracks,
    delete_trending_track,
    delete_all_trending_tracks,
    export_trending_tracks,
    upload_trending_tracks,
    get_recommendations,
    show_recommendations,
)

from .spotify_client import spotify_auth, spotify_callback


urlpatterns = [
    path("top-tracks/short/", top_tracks_short_term, name="top_tracks_short_term"),
    path("top-tracks/medium/", top_tracks_medium_term, name="top_tracks_medium_term"),
    path("top-tracks/long/", top_tracks_long_term, name="top_tracks_long_term"),
    path("", home, name="home"),
    path("add-to-trending/", add_to_trending, name="add_to_trending"),
    path("trending-tracks/", view_trending_tracks, name="view_trending_tracks"),
    path(
        "delete-trending-track/<int:track_id>/",
        delete_trending_track,
        name="delete_trending_track",
    ),
    path("delete-all-tracks/", delete_all_trending_tracks, name="delete_all_tracks"),
    path(
        "start_spotify_playback/",
        start_spotify_playback,
        name="start_spotify_playback",
    ),
    path("export-csv/", export_trending_tracks, name="export_csv"),
    path(
        "upload-trending-tracks/", upload_trending_tracks, name="upload-trending-tracks"
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("spotify-auth/", spotify_auth, name="spotify_auth"),
    path("callback/", spotify_callback, name="spotify_callback"),
    path("recommendations/", get_recommendations, name="get_recommendations"),
    path("show_recommendations/", show_recommendations, name="show_recommendations"),
    path("forgotten-favourites/", forgotten_favourites, name="forgotten_favourites"),
]
