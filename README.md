# followCrom's Top Track Tracker

![followCrom's Top Track Tracker](readme_img.png)

Tracks your Spotify top tracks and builds a Playlist from those tracks plus Last.fm recommendations.

<br>

## Local Setup / Development 👨🏻‍💻

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env` into `tttracker/` (not tracked in git - get it from another machine or the droplet).

```bash
python manage.py migrate
python manage.py runserver
```

Visit http://127.0.0.1:8000/

Everything environment-specific is driven by a single `PLATFORM` variable, read
in `settings.py`:

- `PLATFORM=development` (the default if unset) gives you `DEBUG=True`,
  `ALLOWED_HOSTS` for localhost, static files served from local `static/`, and
  the local Spotify redirect URI.
- Any other value (e.g. `PLATFORM=production`, set in `/var/www/ttt/tttracker/.env`
  on the droplet) gives you `DEBUG=False`, HTTPS-only cookies, the production
  `ALLOWED_HOSTS`/redirect URI, and `STATIC_URL` pointed at the S3 bucket.

There's no need to hand-edit `settings.py` to switch between them - just set
(or unset) `PLATFORM` in the relevant `.env`.

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

Static files are served from `static/` locally and from S3 in production -
which one is active is decided purely by the `PLATFORM` variable described
above, not by editing `settings.py`.

**⚠️ Known gap:** `settings.py` sets `STATIC_URL` to the S3 bucket URL in
production, but doesn't currently configure `STATICFILES_STORAGE`/`STORAGES`
(the `django-storages` backend) or `STATIC_ROOT`, even though `django-storages`
and `boto3` are in `requirements.txt`. Without that wiring, `collectstatic`
won't actually push files to S3 - if you rely on `collectstatic` to update
static assets on the live site, verify it's still doing so before trusting
this step; it may need `STATICFILES_STORAGE` (or the Django 4.2+ `STORAGES`
dict) and `STATIC_ROOT` added back to the production branch of `settings.py`.

Once that's confirmed working, the workflow is:

```bash
PLATFORM=production python manage.py collectstatic
```

Confirm with `yes` to upload to the S3 bucket. No need to touch `settings.py`
- setting `PLATFORM` for just that one command is enough.

**Do not run `collectstatic` on the droplet** - it will overwrite the S3
bucket with whatever's on the server at the time.

<br>

## Database 💾

Migrations are changes that alter the database schema. If you add a model or
change a field, run:

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

### Superuser / Admin

Create a superuser (admin) account to access the Django admin interface:

```bash
python manage.py createsuperuser
```

### Regular Users

To create regular users, you can either:

1. use the Django admin interface at `/admin/`

2. run the `create_users.py` script in `/var/www/ttt/` on the server:

```bash
python create_users.py newuser securepassword

# Or with an email:
python create_users.py newuser securepassword newuser@example.com

# The email field is optional in Django by default, so you don't have to
# provide one if you don't need it.
```

### List Users

To list all users, you can either:

1. use the Django admin interface at `/admin/auth/user/`

2. run the `display_users.py` script in `/var/www/ttt/` on the server:

```bash
python display_users.py
```

This also shows the Django settings module, which is useful for troubleshooting.

<br>

## Production: DigitalOcean 🌊

### Initial Droplet Setup

**Step 1**: Create a Digital Ocean Droplet.

**Step 2**: SSH into it:

```bash
ssh -i ~/.ssh/digiocean root@<droplet-ip>
```

**Step 3**: Update and upgrade the system:

```bash
apt update && apt upgrade -y
```

**Step 4**: Install Python and Nginx:

```bash
apt install python3 python3-pip python3-venv nginx -y
```

On Ubuntu 22.04 droplets a reboot may be needed at this stage (`reboot`).

**Step 5**: Create a directory for the app (`/var/www/` is the standard
location for web apps):

```bash
mkdir /var/www/ttt
cd /var/www/ttt
```

**Step 6**: Clone the repo:

```bash
git clone https://github.com/followcrom/TopTrackTracker.git ttt/
```

**Step 7**: Transfer the `.env` file (not in the repo):

```bash
scp -i ~/.ssh/digiocean .env root@<droplet-ip>:/var/www/ttt/tttracker
```

Make sure it includes `PLATFORM=production` (see [Local Setup](#local-setup--development-)),
plus the correct permissions:

```bash
chown www-data:www-data /var/www/ttt/.env
chmod 600 /var/www/ttt/.env
```

**Step 8**: Set up a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

**Step 9**: Run migrations (see the [Database](#database-) section for the
gitignored-migrations gotcha):

```bash
python manage.py migrate
```

**Do not run `collectstatic` here** - see the [Design](#-design--static-files)
section above; it would overwrite the S3 bucket with whatever's on the server.

**Step 10**: Create a systemd service file for Gunicorn:

```bash
nano /etc/systemd/system/gunicorn.service   # could also call this ttt.service
```

```ini
[Unit]
Description=gunicorn daemon for ttt
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/ttt
ExecStart=/var/www/ttt/.venv/bin/gunicorn --access-logfile /var/www/ttt/logs/ttt_access.log --error-logfile /var/www/ttt/logs/ttt_error.log --capture-output --workers 3 --bind unix:/var/www/ttt/tttracker.sock tttracker.wsgi:application --log-level=info

[Install]
WantedBy=multi-user.target
```

**Step 11**: Fix permissions so Nginx (`www-data`) can access the project:

```bash
chown -R www-data:www-data /var/www/ttt
chmod -R 755 /var/www/ttt
```

**Step 12**: Start and enable Gunicorn:

```bash
systemctl daemon-reload   # if the unit file changed
systemctl start gunicorn
systemctl enable gunicorn
systemctl status gunicorn
```

**Step 13**: Create an Nginx config file:

```bash
nano /etc/nginx/sites-available/ttt
```

```nginx
server {
    listen 80;
    server_name www.ttt.followcrom.com ttt.followcrom.com <droplet-ip>;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/ttt/tttracker.sock;
    }

    # Static files are served from S3, not Nginx.
}
```

Certbot will rewrite this automatically once HTTPS is set up (below), adding
the `listen 443 ssl` block and a redirect from port 80.

Make sure `ALLOWED_HOSTS` in `settings.py` (production branch) includes every
domain/IP used in `server_name` - Django returns *400 Bad Request* otherwise.

**Step 14**: Symlink it into `sites-enabled`, test, and reload:

```bash
ln -s /etc/nginx/sites-available/ttt /etc/nginx/sites-enabled
nginx -t
systemctl reload nginx
```

*Reload* applies config changes without dropping active connections;
*restart* (`systemctl restart nginx`) is more disruptive but guarantees a
clean pickup of changes.

**Step 15**: Configure the firewall:

```bash
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw enable
ufw status verbose
```

**Step 16**: Restart Gunicorn first, then reload Nginx (Gunicorn runs the
actual app code, so it needs to be current before Nginx starts routing to it):

```bash
systemctl restart gunicorn
systemctl status gunicorn
systemctl reload nginx
systemctl status nginx
```

Visit your domain or droplet IP to confirm the app is up:
[Top Track Tracker](https://ttt.followcrom.com/)

<br>

### HTTPS with Let's Encrypt 🔐

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d ttt.followcrom.com -d www.ttt.followcrom.com
```

Verify auto-renewal:

```bash
certbot renew --dry-run
```

List certificates:

```bash
certbot certificates
```

Revoke/delete an unused certificate:

```bash
certbot revoke --cert-path /etc/letsencrypt/live/ttt.followcrom.com/fullchain.pem
certbot delete
```

<br>

### Picking Up New Code

```bash
cd /var/www/ttt
cp db.sqlite3 db.sqlite3.bak-$(date +%F)   # back up first, migrations can be destructive
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations tttapp   # migrations aren't in git - regenerate here
python manage.py migrate
systemctl restart gunicorn   # or ttt.service
systemctl reload nginx
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
