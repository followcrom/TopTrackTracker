# settings.py

from pathlib import Path
import os
from dotenv import load_dotenv


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# print("BASE_DIR:", BASE_DIR)


dotenv_path = BASE_DIR / "tttracker" / ".env"
# print("Path to .env:", dotenv_path)
load_dotenv(dotenv_path=dotenv_path)
if os.path.exists(dotenv_path):
    print(".env file loaded successfully.")
else:
    print(".env file not found.")


# ENVIROMENTAL VARIABLES
SECRET_KEY = os.environ.get("SECRET_KEY")
if SECRET_KEY:
    print("Secret key loaded successfully.")
else:
    print("SECRET_KEY is not set!")


# LastFM API settings
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY")
LASTFM_USERNAME = os.environ.get("LASTFM_USERNAME")

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

# Determine platform
PLATFORM = os.environ.get("PLATFORM", "Development").lower()

# Source directory for static files, used by collectstatic regardless of platform
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# Platform-specific configurations
if PLATFORM == "development":
    DEBUG = True
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
    SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8000/callback/"
    # Local static settings
    STATIC_URL = "/static/"
    print("Running in Development mode")
    print("STATICFILES_DIRS:", STATICFILES_DIRS)
    print(f"Running on platform: {PLATFORM}")
else:
    DEBUG = False
    ALLOWED_HOSTS = ["ttt.followcrom.com", "www.ttt.followcrom.com"]
    SPOTIFY_REDIRECT_URI = "https://ttt.followcrom.com/callback/"
    # Site is HTTPS-only behind nginx: never send session/CSRF cookies in clear
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # S3 Static settings
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = "static-ttt"
    AWS_REGION = "eu-west-2"
    AWS_S3_REGION_NAME = AWS_REGION  # setting name django-storages actually reads
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com"
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
    }
    print("Static files served from S3 at:", STATIC_URL)
    print(f"Running on platform: {PLATFORM}")


# ALLOWED_HOSTS = [
#     "localhost",
#     "127.0.0.1",
#     "www.ttt.followcrom.com",
#     "ttt.followcrom.com",
# ]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "tttapp",
]

MIDDLEWARE = [
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
        "DIRS": [BASE_DIR / "templates"],
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


SESSION_ENGINE = "django.contrib.sessions.backends.db" # Use the database for sessions
SESSION_COOKIE_AGE = 60 * 60 * 24 * 180  # 180 days, matches Spotify's refresh token lifetime
SESSION_EXPIRE_AT_BROWSER_CLOSE = False



DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# Internationalization
LANGUAGE_CODE = "en-uk"

TIME_ZONE = "GMT"

USE_I18N = True

USE_TZ = True
