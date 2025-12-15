from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

import dj_database_url
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ======================
# SECURITY
# ======================
SECRET_KEY = os.environ.get("SECRET_KEY", "changeme")

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    "api-proof-capacity.onrender.com",
    "localhost",
    "127.0.0.1",
]

# ======================
# APPLICATION
# ======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',

    'api_proof',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'corsheaders.middleware.CorsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ======================
# TEMPLATES
# ======================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # crée un dossier 'templates' si tu n'en as pas
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


ROOT_URLCONF = 'proof_capacity.urls'
WSGI_APPLICATION = 'proof_capacity.wsgi.application'

AUTH_USER_MODEL = 'api_proof.User'

# ======================
# DATABASE (Render)
# ======================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.environ.get("DATABASE_URL")


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
}

# ======================
# SESSIONS & CSRF
# ======================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

CSRF_TRUSTED_ORIGINS = [
    "https://api-proof-capacity.onrender.com",
    "https://poc-official.vercel.app",
]

# ======================
# CORS
# ======================
CORS_ALLOWED_ORIGINS = [
    "https://poc-official.vercel.app",
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True

# ======================
# DRF
# ======================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

# ======================
# STATIC FILES
# ======================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
