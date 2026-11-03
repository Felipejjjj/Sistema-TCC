from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'somente-demonstracao-local-catalogo-tcc-2026')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes',
    'rest_framework', 'rest_framework.authtoken', 'drf_spectacular',
    'corsheaders', 'django_filters', 'catalogo',
]
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware',
              'django.middleware.security.SecurityMiddleware',
              'django.middleware.common.CommonMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
              'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Fortaleza'
USE_I18N = True
USE_TZ = True
CORS_ALLOWED_ORIGINS = ['http://localhost:5500', 'http://127.0.0.1:5500']
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAdminUser'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 6,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend',
                              'rest_framework.filters.SearchFilter', 'rest_framework.filters.OrderingFilter'],
    'DEFAULT_THROTTLE_RATES': {'anon': '20/min'},
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'catalogo.exceptions.api_exception_handler',
}
SPECTACULAR_SETTINGS = {
    'TITLE': 'Catálogo de TCCs', 'VERSION': '1.0.0',
    'DESCRIPTION': 'Acervo público v1 e gestão exclusiva da coordenação por token.',
    'SERVE_INCLUDE_SCHEMA': False,
}
