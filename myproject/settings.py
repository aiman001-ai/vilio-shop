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

# DEBUG: Error check karne ke liye True rakha hai
DEBUG = True

ALLOWED_HOSTS = [
    '*',
    'vilio-shop.onrender.com', 
    'vilio.shop', 
    'www.vilio.shop',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '192.168.1.63',
]

CSRF_TRUSTED_ORIGINS = [
    'https://vilio-shop.onrender.com',
    'https://vilio.shop',
    'https://www.vilio.shop',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://192.168.1.134:8000',
]

# Security Settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
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
        'CONN_MAX_AGE': 0,
    }
}

# =========================
# STORAGE & MEDIA CONFIG
# =========================

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'drda3jvoc',
    'API_KEY': '743562395273835',
    'API_SECRET': '4u7e4Qc9AzyeeQDFwANbuF2F0bU',
}

cloudinary.config(
    cloud_name='drda3jvoc',
    api_key='743562395273835',
    api_secret='4u7e4Qc9AzyeeQDFwANbuF2F0bU',
    secure=True
)

# Static and Media URLs
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_DIRS = [
    BASE_DIR / "app1" / "static",
]

# ==========================================
# STORAGE CONFIGURATION (Django 5.1 & Cloudinary)
# ==========================================

# WhiteNoise settings (Missing files par crash nahi karega)
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = True
# Niche wali line ko change karke simple kar do (Bina compression ke)
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.StaticFilesStorage", # 'CompressedManifest' hata diya
    },
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

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_REDIRECT_URL = '/post-login/'
LOGOUT_REDIRECT_URL = '/'

# settings.py mein ye teen lines dhyan se update karo:

LOGIN_REDIRECT_URL = '/post-login/' # Ye sahi hai
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False # 🚀 YE SABSE ZAROORI HAI. Isse Allauth next parameter ko bypass nahi karega.
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True

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