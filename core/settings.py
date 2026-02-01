import os
from pathlib import Path
from datetime import timedelta # JWT vaqti uchun

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-_mqoid!+$309xe_a+2v$+z6%m@_a_6$(ts()0o^yzt#n&^j*-b'

DEBUG = True

ALLOWED_HOSTS = ['*'] # Dev rejimida hamma joydan ulanishga ruxsat

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# Application definition

INSTALLED_APPS = [
    'jazzmin',  # Eng tepaga qo'shing
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Qo'shilgan kutubxonalar
    'import_export',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'accounts',
    'cargo',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # Eng yuqorida turishi kerak
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Custom User Model ulanishi (MUHIM!)
AUTH_USER_MODEL = 'accounts.User'

# REST Framework sozlamalari
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

# JWT sozlamalari (Access va Refresh token muddati)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Flutter bilan ulanish uchun CORS ruxsatnomasi
CORS_ALLOW_ALL_ORIGINS = True 

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

JAZZMIN_SETTINGS = {
    "site_title": "UTS Cargo",
    "site_header": "UTS Cargo",
    "site_brand": "UTS Admin",
    "site_logo": None,  # Agar logotip bo'lsa yo'lini ko'rsating
    "welcome_sign": "UTS Cargo boshqaruv paneliga xush kelibsiz",
    "copyright": "UTS Cargo Ltd",
    "search_model": ["accounts.User", "cargo.Cargo"],
    "user_avatar": None,

    # Sidebar sozlamalari
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["accounts", "cargo"],

    # IKONKALAR - Rasmdagi barcha modullar uchun
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "accounts.User": "fas fa-user-friends",
        "accounts.OtpCode": "fas fa-shield-alt",  # OTP kodlar uchun ikonka
        "cargo.Cargo": "fas fa-boxes",
        "cargo.WarehouseCargo": "fas fa-warehouse",
        "cargo.OnWayCargo": "fas fa-shipping-fast",
        "cargo.ArrivedCargo": "fas fa-map-marker-alt",
        "cargo.DeliveredCargo": "fas fa-check-double",
        "cargo.SupportMessage": "fas fa-comments",
    },

    # Standart ikonka (Ikonka berilmaganlar uchun circle chiqmasligi uchun)
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-cube",  # Circle o'rniga kubik chiqadi

    "topmenu_links": [
        {"name": "Bosh sahifa", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "accounts.User"},
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary", # To'q rangli sidebar
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Til va vaqt
LANGUAGE_CODE = 'uz-uz' # Admin panelni o'zbekcha qilamiz
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'