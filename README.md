# 🔥 Top Track Tracker 🛤️

<p align="center"><img src="readme_img.png" width="520" alt="followCrom's Top Track Tracker"/></p>

Track your Spotify plays and generate a playlist from your top tracks and Last.fm recommendations.

## GitHub

To make the local branch an exact copy of origin/SURFACE (discarding any local differences):

```bash
git fetch origin
git reset --hard origin/SURFACE
```

If you want a normal pull/merge instead:

```bash
git pull origin SURFACE
```

## Development / Local 👨🏻‍💻

```bash
source .venv/bin/activate

python manage.py runserver
```

In `settings.py`:

```bash
PLATFORM = os.environ.get("PLATFORM", "Development").lower()
```

`PLATFORM=development` (set as default by above) gives you:
- `DEBUG=True`
- local static files
- local Spotify redirect URI.

On the VM, `PLATFORM="production"` is set in `/var/www/ttt/tttracker/.env`, giving you:
- `DEBUG=False`
- S3 static
- HTTPS-only cookies.

<br>

## 🎨 Design / Static Files 🖼️

Static files are served from `static/` locally and from S3 in production.

To update static files on the live site, edit them locally, then
run `collectstatic` with production settings to push everything to the
`static-ttt` S3 bucket:

```bash
# --dry-run previews what would be uploaded without touching S3
PLATFORM=production python manage.py collectstatic --dry-run

PLATFORM=production python manage.py collectstatic

# --noinput skips the "are you sure?" confirmation prompt
PLATFORM=production python manage.py collectstatic --noinput
```

1️⃣ `collectstatic` uses the `django-storages` backend configured via the
`STORAGES` dictionary in **Platform-specific configurations** in `settings.py`

2️⃣ Also uploaded are Django admin's own CSS/JS (bundled via
`django.contrib.staticfiles`), so `/admin/` gets styled too.

3️⃣ **Do NOT run this on the droplet** 🚧

Always run it from your local machine so
the bucket reflects your local `static/`, not what is on the server.

<br>

## Database 💾

Migrations are changes that alter the database schema. If you add a model or
change a field:

**1️⃣ Locally** — generate the migration file and commit it:

```bash
python manage.py makemigrations
git add tttapp/migrations/
git commit -m "Add migration for ..."
git push origin SURFACE
```

**2️⃣ On the VM** — pull the migration file, then apply it to the database:

```bash
git pull origin SURFACE
python manage.py migrate
```

🚧 **Don't run `makemigrations` on the VM.** It only generates migration
files (it doesn't touch the database by itself), but generating them there
risks drifting from what's committed to git. Always generate and commit
migrations locally, then just run `migrate` on the VM to apply them.

`manage.py migrate` only applies schema changes - it doesn't migrate data. If
you need existing data (users, playlist tracks) on a new machine, copy the
`db.sqlite3` file itself.

📐 Check the size of the SQLite file if disk space is ever a concern:

```bash
du -sh db.sqlite3
```

<br>

## 🚀 Deploying a Change: Dev → Live

Checklist for pushing a local change to the live site.

**1️⃣ Push your code:**

```bash
git push origin SURFACE
```

**2️⃣ If you changed static files** (CSS/JS/images in `static/`) — run this
**locally**, not on the VM (see **Design / Static Files** above):

```bash
PLATFORM=production python manage.py collectstatic --noinput
```

**3️⃣ On the VM** — pull the code and apply the rest:

```bash
cd /var/www/ttt
git pull origin SURFACE

# only if a model/field changed - see Database above
python manage.py migrate

systemctl restart ttt.service
```

Restarting Gunicorn is what actually loads your new code (`git pull` alone
doesn't reload the running process). Nginx doesn't need a restart unless you edited its config.

<br>

## Users 🙋🏻

### Superuser / Admin 👱🏻‍♀️

Create a superuser (admin) account to access the Django admin interface:

```bash
python manage.py createsuperuser
```

Then log in at `/admin/` to manage users.

NOTE on locking down the admin interface via Nginx:
My Nginx config puts HTTP Basic Auth in front of `/admin/` (_auth_basic_user_file /etc/nginx/.htpasswd_admin_). To use the admin interface without the extra password prompt, comment out the two `auth_basic` lines in `/etc/nginx/sites-available/ttt` and reload Nginx:

```bash
nginx -t && systemctl reload nginx
```

### Regular Users 👧🏾👩🏻‍🦰👩🏻

To create regular users, you can either:

1. use the Django admin interface at `/admin/`

2. run the `create_users.py` script in `/var/www/ttt/` on the server:

```bash
python create_users.py newuser securepassword

# Or with an email (email is optional):
python create_users.py newuser securepassword newuser@example.com
```

### List Users 👩🏻👧🏽👧🏾

To list all users, you can either:

1. use the Django admin interface at `/admin/auth/user/`

2. run the `display_users.py` script in `/var/www/ttt/` on the server:

```bash
python display_users.py
```

`display_users.py` also shows the Django settings module, which is useful for troubleshooting.

<br>

## 📦 Production / DigitalOcean 🌊

The `PLATFORM` environment variable is what determines which settings are used in `settings.py`.

`PLATFORM=development` is set by default and used for local development.

On the production server, the `.env` sets `PLATFORM=production` to select production settings.

Ensure the `.env` file has the correct permissions:

```bash
chown www-data:www-data /var/www/ttt/tttracker/.env
chmod 600 /var/www/ttt/tttracker/.env
```

<br>

### 🧩 Nginx config

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

<br>

### Logs 🪵

```bash
journalctl -u gunicorn -f
tail -f /var/log/nginx/error.log
```

To clear the Gunicorn logs, truncate rather than delete:

```bash
truncate -s 0 /var/www/ttt/logs/ttt_access.log
truncate -s 0 /var/www/ttt/logs/ttt_error.log
```

<br>

## 🛠️ Troubleshooting 🕵

**Verify both services are running:**

```bash
systemctl status gunicorn
systemctl status nginx
```

**Spotify token cache:**

`SpotifyOAuth` (in `spotify_client.py`) writes a
`.cache` file to disk by default, separate from the token also stored in the
Django session. If you change your Spotify account password, existing
tokens are revoked and you'll see `invalid_grant: Refresh token revoked`. Delete the cache file and re-authenticate:

```bash
rm .cache
```

**Allowed Hosts:**

A *400 Bad Request* means the request's `Host` header
isn't in `ALLOWED_HOSTS` (`settings.py`, production branch). Add the missing
domain/IP.

<br>

## Renew Secret Key 🔐

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

<br>

## 📅 Commit Activity 🕹️

![GitHub last commit](https://img.shields.io/github/last-commit/followcrom/TopTrackTracker)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/followcrom/TopTrackTracker)
![GitHub repo size](https://img.shields.io/github/repo-size/followcrom/TopTrackTracker)

<br>

## ✍ Authors 

📫 [Get in touch](https://followcrom.com/contact/contact.php) 👋

[![Static Badge](https://img.shields.io/badge/followcrom-online-blue)](http://followcrom.com)