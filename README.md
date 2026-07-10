# 𝄞⨾💿✮˚.⋆ Top Track Tracker 🛤️

<p align="center"><img src="readme_img.png" width="420" alt="followCrom's Top Track Tracker"/></p>

Track your Spotify plays and generate a playlist from your top tracks and Last.fm recommendations.

---

## Local Development 👨🏻‍💻

```bash
source .venv/bin/activate

python manage.py runserver
```

In `settings.py`, `PLATFORM=development` (default) gives you:
- `DEBUG=True`
- local static files
- local Spotify redirect URI.

On the VM, `PLATFORM="production"` is set in /var/www/ttt/tttracker/.env, giving you:
- `DEBUG=False`
- S3 static
- HTTPS-only cookies.

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

## 🎨 Design / Static Files

Static files are served from `static/` locally and from S3 in production.

To update static files (CSS/images) on the live site, edit them locally, then
run `collectstatic` with production settings to push everything to the
`static-ttt` S3 bucket:

```bash
PLATFORM=production python manage.py collectstatic --noinput

# --noinput skips the "are you sure?" confirmation prompt
```

(`collectstatic` uses the `django-storages` backend configured via the
`STORAGES` dictionary in **Platform-specific configurations** in `settings.py`)

Add `--dry-run` first to preview what would be uploaded without touching S3:

```bash
PLATFORM=production python manage.py collectstatic --dry-run
```

Also uploaded are Django admin's own CSS/JS (bundled via
`django.contrib.staticfiles`), so `/admin/` gets styled too.

🚧 **Do not run this on the droplet**

Always run it from your local machine so
the bucket reflects your local `static/`, not whatever happens to be on the server at the time.

<br>

## Database 💾

Migrations are changes that alter the database schema. If you add a model or
change a field, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

Check the size of the SQLite file if disk space is ever a concern:

```bash
du -sh db.sqlite3
```

`DELETE`/`DROP TABLE` don't shrink the file - SQLite just marks the freed
pages reusable. To actually reclaim disk space (stop the app first so
nothing's writing to the DB):

```bash
sqlite3 db.sqlite3 "VACUUM;"
```

`manage.py migrate` only applies schema changes - it doesn't migrate data. If
you need existing data (users, playlist tracks) on a new machine, copy the
`db.sqlite3` file itself.

<br>

## Users 🙋🏻

### Superuser / Admin 👱🏻‍♀️👩🏻‍🦰👩🏻

Create a superuser (admin) account to access the Django admin interface:

```bash
python manage.py createsuperuser
```

Then log in at `/admin/` to manage users*.

* My Nginx config puts HTTP Basic Auth in front of /admin/ (auth_basic_user_file /etc/nginx/.htpasswd_admin). Fine for me, but to use the Django admin interface without the extra password prompt, comment out the two `auth_basic` lines in `/etc/nginx/sites-available/ttt` and reload Nginx:

```bash
nginx -t && systemctl reload nginx
```

### Regular Users 👧🏾👩🏻‍🦰👩🏻

To create regular users, you can either:

1. use the Django admin interface at `/admin/`

2. run the `create_users.py` script in `/var/www/ttt/` on the server:

```bash
python create_users.py newuser securepassword

# Or with an email:
python create_users.py newuser securepassword newuser@example.com
# The email field is optional
```

### List Users 👧🏽👩🏻‍🦰👩🏻

To list all users, you can either:

1. use the Django admin interface at `/admin/auth/user/`

2. run the `display_users.py` script in `/var/www/ttt/` on the server:

```bash
python display_users.py
```

This also shows the Django settings module, which is useful for troubleshooting.

---

## Production / DigitalOcean 🌊

The .env file includes `PLATFORM=production` to select production settings in `settings.py`. Ensure the .env file has the correct permissions:

```bash
chown www-data:www-data /var/www/ttt/tttracker/.env
chmod 600 /var/www/ttt/tttracker/.env
```


Nginx config file:

```bash
nano /etc/nginx/sites-available/ttt
```

```nginx
# Block 1: The main HTTPS block for the canonical domain.
# This is where your application runs.
server {
    listen 443 ssl http2;
    server_name ttt.followcrom.com;

    # SSL configuration (no changes)
    ssl_certificate /etc/letsencrypt/live/ttt.followcrom.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ttt.followcrom.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # HSTS: browsers refuse plain-HTTP to this domain for a year after first visit
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Django admin: challenged at the web-server level, before Django sees it
    location /admin/ {
        auth_basic "Admin";
        auth_basic_user_file /etc/nginx/.htpasswd_admin;

        # Alternative: fixed-IP allowlist. Comment out the two auth_basic
        # lines above and uncomment these (find your IP: curl ifconfig.me)
        # allow YOUR.HOME.IP;
        # deny all;

        include proxy_params;
        proxy_pass http://unix:/var/www/ttt/tttracker.sock;
    }

    # Reverse proxy to your application (no changes)
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/ttt/tttracker.sock;
    }
}

# Block 2: A single block to redirect the 'www' version and all HTTP traffic.
server {
    listen 80;
    listen 443 ssl;
    server_name www.ttt.followcrom.com;

    # We need the SSL certs here too, just to handle https://www... requests
    ssl_certificate /etc/letsencrypt/live/ttt.followcrom.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ttt.followcrom.com/privkey.pem;

    # This one line redirects all traffic to the correct, canonical URL
    return 301 https://ttt.followcrom.com$request_uri;
}
```

Make sure `ALLOWED_HOSTS` in `settings.py` (production branch) includes every
domain/IP used in `server_name` - Django returns *400 Bad Request* otherwise.

Configure the firewall:

```bash
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw enable
ufw status verbose
```


<br>

### Logs

```bash
journalctl -u gunicorn -f
tail -f /var/log/nginx/error.log
```

To clear the Gunicorn logs (e.g. `ttt_access.log` can contain the Spotify
OAuth `code` param from `/callback/?code=...`), truncate rather than delete -
Gunicorn holds the file open, so deleting it won't free disk space until the
service restarts, whereas truncating in place is safe to do live:

```bash
truncate -s 0 /var/www/ttt/logs/ttt_access.log
truncate -s 0 /var/www/ttt/logs/ttt_error.log
```

<br>

### Troubleshooting 🕵

**Verify both services are running:**

```bash
systemctl status gunicorn
systemctl status nginx
```

**Nginx <-> Gunicorn socket issues:** if `ls -l /var/www/ttt/tttracker.sock`
shows the socket missing, or Nginx can't reach it, try running Gunicorn
manually to see errors directly:

```bash
/var/www/ttt/.venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/ttt/tttracker.sock tttracker.wsgi:application
```

Then re-check permissions:

```bash
chown -R www-data:www-data /var/www/ttt
chmod -R 755 /var/www/ttt
ls -l /var/www/ttt/tttracker.sock
# expect: srwxrwxrwx 1 root www-data 0 <date> /var/www/ttt/tttracker.sock
```

**Spotify token cache:** `SpotifyOAuth` (in `spotify_client.py`) writes a
`.cache` file to disk by default, separate from the token also stored in the
Django session. If you change your Spotify account password, existing
tokens are revoked and you'll see `invalid_grant: Refresh token revoked` -
delete the cache file and re-authenticate:

```bash
rm .cache
```

**Allowed Hosts:** a *400 Bad Request* means the request's `Host` header
isn't in `ALLOWED_HOSTS` (`settings.py`, production branch) - add the missing
domain/IP.

**Quick endpoint tests:**

```bash
curl --request GET \
  --url 'https://api.spotify.com/v1/me/top/tracks?time_range=short_term&offset=0' \
  --header 'Authorization: Bearer xxx'

curl "https://ttt.followcrom.com/callback/?code=<auth-code>"
```

<br>

## Renew Secret Key 🔐

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```
