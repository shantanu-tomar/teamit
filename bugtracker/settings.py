import os
from dotenv import load_dotenv
from django.contrib.messages import constants as messages
import django_heroku

load_dotenv()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')


SECRET_KEY = 'b#8-k)_jh#s0c2u6d4q^s8qmw9n2ib7n%6!1=8k!vx+douy*qv'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG") == "True"

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    # Local Apps
    'users',
    'projects',
    'messaging',

    # 3RD PARTY APPS
    'crispy_forms',
    'rest_framework',
    'rest_framework.authtoken',
    'allauth',
    'allauth.account',
    'rest_auth',
    'rest_auth.registration',
    'allauth.socialaccount',
    'django.contrib.sites',
    'channels',
    'corsheaders',


    # Base Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
     # 3RD PARTY MIDDLEWARE
    'corsheaders.middleware.CorsMiddleware',
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'bugtracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR, ],
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

WSGI_APPLICATION = 'bugtracker.wsgi.application'
ASGI_APPLICATION = 'bugtracker.routing.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {'user_attributes': ('username', 'first_name', 'last_name',
                    'email', 'name')},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


CORS_ORIGIN_WHITELIST = [
    "http://127.0.0.1:4200",
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:4200",
]

# CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'X-CSRFToken',
    'x-requested-with',
)


REST_FRAMEWORK = {
    # use Django's standard 'django.contrib.auth' permissions,
    # or allow read-only access for unauthorized users.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'users.utils.custom_exception_handler',

}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}



# REST-AUTH SETTINGS

# REST_AUTH_REGISTER_SERIALIZERS = {
#     "REGISTER_SERIALIZER": "users.serializers.UserSerializer"
# }
EMAIL_VERIFICATION = None
AUTHENTICATION_METHOD = 'email'
USERNAME_REQUIRED = False
# in change password form
OLD_PASSWORD_FIELD_ENABLED = True


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

# STATIC_ROOT = (os.path.join(BASE_DIR, 'staticfiles'),)
STATIC_URL = '/static/'
STATICFILES_DIRS = (
                    os.path.join(BASE_DIR, 'static'),
                    os.path.join(BASE_DIR, 'static/ang/static'),
                )

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
IMAGE_UPLOAD_FOLDER = 'images'

AUTH_USER_MODEL = "users.User"
ACCOUNT_ADAPTER = "users.adapter.CustomAccountAdapter"
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
PASS_DECRYPT_KEY = '1234567891234569'

CRISPY_TEMPLATE_PACK = 'bootstrap4'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL')
EMAIL_HOST_PASSWORD = os.getenv('E_PASS')


# message tags to ensure compatability b/w bootstrap & django message colors
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

SITE_ID = 1
CLIENT_DOMAINS = []

# Base URL for http requests FROM this website
# BASE_URL = "http://127.0.0.1:8000/api"
BASE_URL = "http://127.0.0.1:4200"

django_heroku.settings(locals())