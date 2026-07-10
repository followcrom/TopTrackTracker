# followCrom's Top Track Tracker

![followCrom's Top Track Tracker](readme_img.png)

Tracks your Spotify top tracks and lets you build a one-off listening
queue (Playlist Builder) from your top tracks plus Last.fm recommendations.

<br>

## Local Setup 👨🏻‍💻

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env` into `tttracker/` (not tracked in git - get it from another machine or the droplet).

Apply migrations, then start the dev server:

```bash
python manage.py migrate
python manage.py runserver
```

Visit http://127.0.0.1:8000/

In `settings.py`, `PLATFORM=development` (default) gives you `DEBUG=True`, local
static files, and the local Spotify redirect URI. Unset/other values switch to
production settings (S3 static, HTTPS-only cookies).

<br>

## Usage 🎧

- **Top Tracks** (Short / Medium / Long Term): your Spotify top tracks, paged
  10 at a time. Each track has an **Add to Playlist** button.
- **Playlist Builder**: shows everything added to the playlist so far.
  - **Generate Tracks**: tops up the playlist with a random sample of your top
    tracks plus Last.fm recommendations (`tracks`/`recs` fields control totals).
    Adds to the existing playlist rather than overwriting it.
  - **Play in Spotify**: starts playback of the playlist on your active
    Spotify device.
  - **Delete** / **Delete All Tracks**: remove one or all tracks.
  - Badges show where each track came from: S/M/L (top tracks time range),
    NEW (Last.fm recommendation), USER (added manually).

<br>

## Static Files (S3) 🎨

Static files are served from S3 in production, but from `static/` locally.

To make a static-file change (CSS/images) available on the live site:

1. Make your changes locally with `PLATFORM=development` (local static
   settings active).
2. Temporarily switch to production settings in `settings.py` and run:
   ```bash
   python manage.py collectstatic
   ```
   Confirm with `yes` to upload to the S3 bucket.
3. Switch back to `PLATFORM=development` for local work.

**Do not run `collectstatic` on the droplet** - it will overwrite the S3
bucket with whatever's on the server at the time.

<br>

## Database 💾

```bash
python manage.py makemigrations
python manage.py migrate
```

Note: `tttapp/migrations/` is gitignored, so migration files don't travel via
`git pull` - run `makemigrations` on each machine (dev, droplet) after a model
change, rather than committing/copying the migration files themselves.

Check the size of the SQLite file if disk space is ever a concern:

```bash
du -sh db.sqlite3
```

Note: `DELETE`/`DROP TABLE` don't shrink the file - SQLite just marks the
freed pages reusable. To actually reclaim disk space (stop the app first so
nothing's writing to the DB):

```bash
sqlite3 db.sqlite3 "VACUUM;"
```

<br>

## Users 🙋🏻

```bash
python manage.py createsuperuser
```

Then create/manage regular users via `/admin/`, or with `create_users.py`
(on the server, in `/var/www/ttt/`):

```bash
python create_users.py newuser securepassword
```

List users via `/admin/auth/user/` or `python display_users.py`.

<br>

## Production (DigitalOcean) 🌊

The droplet setup, Gunicorn/Nginx config, HTTPS, and troubleshooting steps
are documented in [SURFACE.md](SURFACE.md).

Quick reference for picking up new code:

```bash
cd /var/www/ttt
cp db.sqlite3 db.sqlite3.bak-$(date +%F)   # back up first, migrations can be destructive
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
systemctl restart gunicorn   # or ttt.service
systemctl reload nginx
```

Logs:

```bash
journalctl -u gunicorn -f
tail -f /var/log/nginx/error.log
```

<br>

## Renew Secret Key 🔐

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```
