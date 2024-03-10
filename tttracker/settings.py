# settings.py

from pathlib import Path
import os
from dotenv import load_dotenv

# ENVIROMENTAL VARIABLES
load_dotenv(".env")

SECRET_KEY = os.environ.get("SECRET_KEY")

# SPOTIFY API settings
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8000/callback/"

# AWS S3 settings
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = "static-ttt"
AWS_S3_CUSTOM_DOMAIN = "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME
AWS_DEFAULT_ACL = "public-read"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

# LastFM API settings
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY")
LASTFM_USERNAME = os.environ.get("LASTFM_USERNAME")


# Turn off for production
DEBUG = False

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "18.171.147.94", # AWS Public IP
    "tttapp.followcrom.online",
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tttapp",
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tttracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tttracker.wsgi.application"

SESSION_ENGINE = "django.contrib.sessions.backends.db"

SESSION_COOKIE_AGE = 5000

SESSION_EXPIRE_AT_BROWSER_CLOSE = True


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Local static settings
# STATIC_URL = "/static/"  # uncomment to `collectstatic``
# STATICFILES_DIRS = [os.path.join("static")]


# S3 Static settings
STATIC_LOCATION = "static"
AWS_S3_CUSTOM_DOMAIN = "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATIC_LOCATION)
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

CORS_ALLOW_ALL_ORIGINS = True

# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True
