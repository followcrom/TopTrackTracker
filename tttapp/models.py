from django.db import models


class PlaylistTrack(models.Model):
    """

    Tracks added to the Playlist Builder, either manually (from Top
    Tracks) or via a Reshuffle (top tracks + Last.fm recs).

    """

    artist = models.CharField(max_length=200)
    song = models.CharField(max_length=200)
    uri = models.CharField(max_length=200)
    popularity = models.CharField(max_length=200)
    album = models.CharField(max_length=200, default="", blank=True)
    release_year = models.CharField(max_length=200, default="", blank=True)
    # S/M/L/NEW (or a combo like "S/M") for Reshuffle-added tracks; "USER"
    # for tracks added manually from Top Tracks.
    source_label = models.CharField(max_length=200, default="", blank=True)
    # Display order (higher = shown first). Lets Shuffle reorder tracks
    # independently of insertion order.
    position = models.IntegerField(default=0)


class CreatedPlaylist(models.Model):
    """A record of a playlist pushed to Spotify from the builder, so past
    playlists (TTT_1, TTT_2, ...) can be recreated or inspected later."""

    name = models.CharField(max_length=200)
    spotify_playlist_id = models.CharField(max_length=200, default="", blank=True)
    csv_data = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
