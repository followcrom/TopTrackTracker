from django.db import models


class TrendingTracks(models.Model):
    """

    This model stores information about tracks that are marked as 'Trending'.

    """

    artist = models.CharField(max_length=200)
    song = models.CharField(max_length=200)
    album = models.CharField(max_length=200)
    release_year = models.CharField(max_length=200)
    popularity = models.CharField(max_length=200)
    uri = models.CharField(max_length=200)
    genres = models.CharField(max_length=200)
    energy = models.CharField(max_length=200)
    key = models.CharField(max_length=200)
    valence = models.CharField(max_length=200)
    mood = models.CharField(max_length=200)
    tempo = models.CharField(max_length=200)
    artist_uri = models.CharField(max_length=200)


class PlaylistTrack(models.Model):
    """

    Tracks added to the Playlist Builder, either manually (from Top
    Tracks / Trending) or via a Reshuffle (top tracks + Last.fm recs).

    """

    artist = models.CharField(max_length=200)
    song = models.CharField(max_length=200)
    uri = models.CharField(max_length=200)
    popularity = models.CharField(max_length=200)
    album = models.CharField(max_length=200, default="", blank=True)
    release_year = models.CharField(max_length=200, default="", blank=True)
    genres = models.CharField(max_length=200, default="", blank=True)
    artist_uri = models.CharField(max_length=200, default="", blank=True)
    # S/M/L/NEW (or a combo like "S/M") for Reshuffle-added tracks; blank
    # for tracks added manually from Top Tracks / Trending.
    source_label = models.CharField(max_length=200, default="", blank=True)
