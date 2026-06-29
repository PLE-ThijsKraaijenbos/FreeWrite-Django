from datetime import timedelta

import dj_database_url
from decouple import config, Csv
from django.urls import reverse_lazy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())

# Automatically trust Railway-injected hostname
_railway_domain = config("RAILWAY_PUBLIC_DOMAIN", default="")
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS) + [_railway_domain]

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "user",
    "journey",
    "community",
]

AUTH_USER_MODEL = "user.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FreeWrite API",
    "VERSION": "1.0.0",
    "DESCRIPTION": (
        "This is the HTTP API behind FreeWrite, the app that helps people cut back on "
        "or quit substance use. It backs the React Native client and covers three areas: "
        "accounts and onboarding, the personal journey of writing exercises, and the "
        "community feed.\n\n"
        "## Authentication\n\n"
        "Most endpoints need a logged in user. Authentication is JWT based. Call "
        "`POST /api/user/login/` (or `register`) to get an `access` and a `refresh` token, "
        "then send the access token on every following request as a header:\n\n"
        "```\nAuthorization: Bearer <access token>\n```\n\n"
        "Access tokens are short lived (5 minutes). When one expires, exchange your refresh "
        "token at `POST /api/user/token/refresh/` for a fresh access token instead of asking "
        "the user to log in again. Refresh tokens last 7 days.\n\n"
        "A handful of endpoints are open and need no token: registration, login, token "
        "refresh, and the health check.\n\n"
        "## Conventions\n\n"
        "All request and response bodies are JSON, except post creation and updates, which "
        "accept `multipart/form-data` so an image file can be attached. List endpoints are "
        "paginated 20 items per page unless noted otherwise. IDs are UUIDs unless the path "
        "says otherwise. Timestamps are ISO 8601 in UTC.\n\n"
        "## Errors\n\n"
        "Errors come back with a matching HTTP status and a JSON body. Validation problems "
        "are keyed by field name, while most business rule failures use a single `detail` "
        "string, for example `{\"detail\": \"Not enough coins to purchase this item.\"}`."
    ),
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "TAGS": [
        {
            "name": "User",
            "description": (
                "Registration, login, token refresh, onboarding, the user profile, and the "
                "avatar wardrobe. This is where an account is created and shaped before the "
                "rest of the app becomes useful."
            ),
        },
        {
            "name": "Journey",
            "description": (
                "The user's personal path of writing exercises. The journey is a list of "
                "steps that unlock one after another. These endpoints read the journey and "
                "move a step through its lifecycle: start it, complete it, or bookmark it."
            ),
        },
        {
            "name": "Community",
            "description": (
                "The shared feed where users post, browse, tag, and like each other's "
                "writing. Posts can carry an optional image and a set of tags."
            ),
        },
        {
            "name": "System",
            "description": "Operational endpoints that are not tied to a specific feature, such as the health check.",
        },
    ],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:3000", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="http://localhost:3000", cast=Csv())

import cloudinary
cloudinary.config(
    cloud_name=config("CLOUDINARY_CLOUD_NAME", default=""),
    api_key=config("CLOUDINARY_API_KEY", default=""),
    api_secret=config("CLOUDINARY_API_SECRET", default=""),
    secure=True,
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {filename} {funcName} {lineno} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} - {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'log_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'api.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'api_error.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django_project_api': {
            'handlers': ['console', 'log_file', 'error_file', 'mail_admins'],
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['mail_admins', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

UNFOLD = {
    "SITE_TITLE": "FreeWrite Admin",
    "SITE_HEADER": "FreeWrite",
    "SIDEBAR": {
        "navigation": [
            {
                "title": "Users",
                "items": [
                    {"title": "Users", "icon": "person", "link": reverse_lazy("admin:user_user_changelist")},
                    {"title": "User Profiles", "icon": "manage_accounts", "link": reverse_lazy("admin:user_userprofile_changelist")},
                ],
            },
            {
                "title": "Avatar",
                "items": [
                    {"title": "Avatar Items", "icon": "checkroom", "link": reverse_lazy("admin:user_avataritem_changelist")},
                    {"title": "User Avatar Items", "icon": "face", "link": reverse_lazy("admin:user_useravataritem_changelist")},
                ],
            },
            {
                "title": "Journey",
                "items": [
                    {"title": "Phases", "icon": "layers", "link": reverse_lazy("admin:journey_phase_changelist")},
                    {"title": "Journey Steps", "icon": "format_list_numbered", "link": reverse_lazy("admin:journey_journeystep_changelist")},
                    {"title": "Journeys", "icon": "route", "link": reverse_lazy("admin:journey_journey_changelist")},
                ],
            },
            {
                "title": "Minigame Content",
                "items": [
                    {"title": "Journal", "icon": "book", "link": reverse_lazy("admin:journey_journalcontent_changelist")},
                    {"title": "Letter", "icon": "mail", "link": reverse_lazy("admin:journey_lettercontent_changelist")},
                    {"title": "Choice Story", "icon": "account_tree", "link": reverse_lazy("admin:journey_choicestorycontent_changelist")},
                    {"title": "Speech Bubble", "icon": "chat_bubble", "link": reverse_lazy("admin:journey_speechbubblecontent_changelist")},
                    {"title": "Bubble Pop", "icon": "interests", "link": reverse_lazy("admin:journey_bubblepopcontent_changelist")},
                    {"title": "Scale", "icon": "balance", "link": reverse_lazy("admin:journey_scalecontent_changelist")},
                ],
            },
            {
                "title": "Community",
                "items": [
                    {"title": "Posts", "icon": "forum", "link": reverse_lazy("admin:community_post_changelist")},
                    {"title": "Tags", "icon": "sell", "link": reverse_lazy("admin:community_tag_changelist")},
                ],
            }
        ],
    },
}