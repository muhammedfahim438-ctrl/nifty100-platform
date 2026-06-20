"""
Django Settings for Nifty 100 Financial Intelligence Platform
"""

from pathlib import Path
from decouple import config, Csv

# ─────────────────────────────────────────────
# Base Directory
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")
DEBUG = str(config("DEBUG", default="False")).strip().lower() in ("1", "true", "yes", "on")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ─────────────────────────────────────────────
# Installed Apps
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    # Our apps
    "companies",
    "ml_engine",
    "api_management",
    "dashboard",
    "accounts",
    "admin_insights",
    "api",
]

# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",          # must be before CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

# ─────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────
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

WSGI_APPLICATION = "core.wsgi.application"

# ─────────────────────────────────────────────
# Database — PostgreSQL
# ─────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE"  : "django.db.backends.postgresql",
        "NAME"    : config("DB_NAME",     default="nifty100"),
        "USER"    : config("DB_USER",     default="postgres"),
        "PASSWORD": config("DB_PASSWORD"),               # no fallback — must be in .env
        "HOST"    : config("DB_HOST",     default="localhost"),
        "PORT"    : config("DB_PORT",     default="5433"),
    }
}

# ─────────────────────────────────────────────
# Cache — Redis (django-redis, 60-min TTL)
# ─────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND" : "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
        "OPTIONS" : {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 3600,   # 60 minutes
    }
}

# ─────────────────────────────────────────────
# Password Validation
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─────────────────────────────────────────────
# Internationalisation
# ─────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Asia/Kolkata"
USE_I18N      = True
USE_TZ        = True

# ─────────────────────────────────────────────
# Static Files
# ─────────────────────────────────────────────
STATIC_URL       = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT      = BASE_DIR / "staticfiles"

# ─────────────────────────────────────────────
# Default Primary Key
# ─────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────
# Django REST Framework
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS"     : "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS" : "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE"                : 20,
    "DEFAULT_RENDERER_CLASSES" : [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon"     : "100/hour",   # public API anonymous limit
        "user"     : "1000/hour",  # authenticated user limit
        "login"    : "5/min",      # JWT login endpoint hard limit
    },
}

# ─────────────────────────────────────────────
# JWT Settings
# ─────────────────────────────────────────────
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME" : timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS" : True,
    "AUTH_HEADER_TYPES"     : ("Bearer",),
}

# ─────────────────────────────────────────────
# CORS — locked to explicit origins only
# ─────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOW_ALL_ORIGINS is intentionally NOT set (was True before — security risk)

# ─────────────────────────────────────────────
# API Documentation
# ─────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE"      : "Nifty 100 Financial Intelligence API",
    "DESCRIPTION": "REST API for Nifty 100 financial data",
    "VERSION"    : "1.0.0",
}

# ─────────────────────────────────────────────
# Celery — Redis broker
# ─────────────────────────────────────────────
CELERY_BROKER_URL        = config("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND    = config("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT    = ["json"]
CELERY_TASK_SERIALIZER   = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE          = "Asia/Kolkata"

# ─────────────────────────────────────────────
# Channel Partner API — Rate Limits per tier
# Required by api_management/throttling.py
# ─────────────────────────────────────────────
RATE_LIMITS = {
    "BASIC":      {"minute": 10,  "hour": 100,   "day": 500},
    "PRO":        {"minute": 60,  "hour": 1000,  "day": 10000},
    "ENTERPRISE": {"minute": 300, "hour": 10000, "day": None},
}

# ─────────────────────────────────────────────
# Celery Beat — Nightly Scheduled Tasks
# ─────────────────────────────────────────────
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "refresh-all-scores-nightly": {
        "task": "ml_engine.tasks.refresh_all_scores",
        "schedule": crontab(hour=2, minute=0),
    },
    "run-anomaly-detection-nightly": {
        "task": "ml_engine.tasks.run_anomaly_detection",
        "schedule": crontab(hour=3, minute=0),
    },
}

# ─────────────────────────────────────────────
# Power BI Gateway Token
# ─────────────────────────────────────────────
PBI_GATEWAY_TOKEN = config("PBI_GATEWAY_TOKEN", default="")
