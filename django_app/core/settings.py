"""
Django Settings for Nifty 100 Financial Intelligence Platform
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# ─────────────────────────────────────────────
# Base Directory
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-nifty100-dev-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

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
    "corsheaders",
    "drf_spectacular",
    # Our apps
    "companies",
    "api",
    "admin_insights",
]

# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "NAME"    : os.getenv("DB_NAME",     "nifty100"),
        "USER"    : os.getenv("DB_USER",     "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres123"),
        "HOST"    : os.getenv("DB_HOST",     "localhost"),
        "PORT"    : os.getenv("DB_PORT",     "5433"),
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
STATIC_URL        = "/static/"
STATICFILES_DIRS  = [BASE_DIR / "static"]
STATIC_ROOT       = BASE_DIR / "staticfiles"

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
}

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
# ─────────────────────────────────────────────
# API Documentation
# ─────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE"      : "Nifty 100 Financial Intelligence API",
    "DESCRIPTION": "REST API for Nifty 100 financial data",
    "VERSION"    : "1.0.0",
}