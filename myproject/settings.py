"""
Django settings for myproject project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
import dj_database_url

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING
SECRET_KEY = 'django-insecure-xr1kibek!kpjz(z)3-vj%7yrhbqx0%3lthlnk))=u*&=o(mn*+'

IS_PROD = os.getenv('RENDER', '') != '' or os.getenv('DJANGO_ENV', '') == 'production'
DEBUG = not IS_PROD

ALLOWED_HOSTS = [
    '*',
    'vilio-shop.onrender.com', 
    'vilio.shop', 
    'www.vilio.shop',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '192.168.1.63',
    '192.168.1.45',
    '192.168.1.12',
    '192.168.1.11',
]

CSRF_TRUSTED_ORIGINS = [
    'https://vilio-shop.onrender.com',
    'https://vilio.shop',
    'https://www.vilio.shop',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://192.168.1.134:8000',
    'http://192.168.1.12:8000',
    'http://192.168.1.11:8000',
    'http://192.168.1.45:8000',
    'http://192.168.1.63:8000',
    'https://*.lhr.life',
]

# Security Settings
CSRF_COOKIE_SECURE = IS_PROD
SESSION_COOKIE_SECURE = IS_PROD
CSRF_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ======================
# Application definition
# ======================

INSTALLED_APPS = [
    'cloudinary_storage',  # Sabse upar zaroori hai
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', 
    
    'cloudinary',
    'app1',
    'django.contrib.sites',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Development tool
    'django.contrib.sitemaps',
    
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # 🚀 Hyper-fast response: compresses HTML by ~80%
    'whitenoise.middleware.WhiteNoiseMiddleware', # Static files handling
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app1.context_processors.cart_count_processor',
                'app1.context_processors.menu_categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# ==========================================
# DATABASE - NEON POSTGRES
# ==========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres.esqnwszpvbnozqtgckyj',
        'PASSWORD': 'g9ML7v$-d.wX?8t',  # Special characters bina kisi dikkat ke chalenge
        'HOST': 'aws-1-ap-south-1.pooler.supabase.com',  # Naya validated host
        'PORT': '6543',
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 600,  # 🚀 Persistent connection pooling avoids re-connecting on every page
    }
}

# =========================
# STORAGE & MEDIA CONFIG
# =========================



# Static and Media URLs
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_DIRS = [
    BASE_DIR / "app1" / "static",
    BASE_DIR / "static",
]

# ==========================================
# STORAGE CONFIGURATION (Django 5.1 & Cloudinary)
# ==========================================

# WhiteNoise settings (Missing files par crash nahi karega)
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = True
# Niche wali line ko change karke simple kar do (Bina compression ke)
# 1. Pehle variables define karo (Inhe STORAGES ke upar hona chahiye)
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', 'iftjznoq')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '279582544763469')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', 'KrTpyDKhg88jFySMC-NdbbVaU7I') # <--- Apni secret key yahan string mein daal de local testing ke liye

# 2. Base Configuration
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

# 3. Ab STORAGES block aayega (Ab ye crash nahi karega)
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        "OPTIONS": {
            "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
            "API_KEY": CLOUDINARY_API_KEY,
            "API_SECRET": CLOUDINARY_API_SECRET,
            "QUALITY": "auto:eco",       
            "FETCH_FORMAT": "auto",    
            "USE_FILENAME": True,       # 🚀 Version number ke jhanjhat ko बाईपास karega
            "UNIQUE_FILENAME": False,
        }
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.StaticFilesStorage",
    },
}

# 4. Old compatibility config (Isko bhi niche rehne do)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET,
}

# Legacy support (Sirf compatibility ke liye, agar koi purani library ise dhoonde)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# =================
# Authentication
# =================

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SESSION_REMEMBER = True

# Allauth redirects
LOGIN_REDIRECT_URL = '/post-login/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True

# Google OAuth2 Provider Configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'FETCH_USERINFO': True,
    }
}

# Live site requires HTTPS protocol for OAuth callbacks; local uses HTTP
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https' if IS_PROD else 'http'

# Authentication Login / Logout URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'post_login'
LOGOUT_REDIRECT_URL = 'home'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

load_dotenv() # Ye line .env file se saari keys load kar degi

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

# ✅ Webhook Secret (yahi add karna hai)
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

# Email Config
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'aiman7417@gmail.com'
EMAIL_HOST_PASSWORD = 'rhun pqyy uqwd onzq'
DEFAULT_FROM_EMAIL = f"Vilio Store <{EMAIL_HOST_USER}>"


# settings.py ke bilkul last mein paste karein
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'vilio-local-cache',
    }
}


INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# ==========================================
# META ADS TRACKING (PIXEL & CONVERSIONS API)
# ==========================================
META_PIXEL_ID = os.getenv('META_PIXEL_ID', '27446769361621989')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN', '')