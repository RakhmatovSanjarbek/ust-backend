import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

SECRET_KEY = 'django-insecure-_mqoid!+$309xe_a+2v$+z6%m@_a_6$(ts()0o^yzt#n&^j*-b'

DEBUG = True

ALLOWED_HOSTS = ['46.8.176.172', 'utsgroup.uz', 'www.utsgroup.uz', '127.0.0.1', 'localhost']

CSRF_TRUSTED_ORIGINS = [
    'http://46.8.176.172',
    'http://utsgroup.uz',
    'https://utsgroup.uz',
]

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'import_export',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'accounts',
    'cargo',
    'warehouse',
    'services',
    'whitenoise.runserver_nostatic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOW_ALL_ORIGINS = True

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_L10N = True
USE_TZ = True


LANGUAGES = [
    ('uz', _('Uzbek')),
    ('ru', _('Russian')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JAZZMIN_SETTINGS = {
    "site_title": "UTS Cargo",
    "site_header": "UTS Cargo",
    "site_brand": "UTS Admin",
    "site_logo": "images/logo.png",
    "login_logo": "images/logo.png",
    "site_icon": "images/logo.png",
    "site_logo_classes": "img-circle",
    "welcome_sign": "UTS Cargo boshqaruv paneliga xush kelibsiz",
    "copyright": "UTS Cargo Ltd",
    "search_model": ["accounts.User", "cargo.Cargo"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "language_chooser": True,
    "order_with_respect_to": [
        "accounts",
        "auth",
        "warehouse",
        "cargo",
        "services",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "accounts.User": "fas fa-user-friends",
        "accounts.OtpCode": "fas fa-shield-alt",
        "cargo.Cargo": "fas fa-boxes",
        "cargo.WarehouseCargo": "fas fa-warehouse",
        "cargo.OnWayCargo": "fas fa-shipping-fast",
        "cargo.ArrivedCargo": "fas fa-map-marker-alt",
        "cargo.DeliveredCargo": "fas fa-check-double",
        "services.SupportMessage": "fas fa-comments",
        "services.TutorialVideo": "fa-solid fa-video",
        "services.CalculationRequest": "fa-solid fa-calculator",
        "warehouse.ArrivedGroup": "fa-solid fa-layer-group",
        "warehouse.PaymentRequest": "fa-solid fa-credit-card",
        "warehouse.DeliveryQueue": "fa-solid fa-cart-flatbed",



    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-cube",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "theme": "flatly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}