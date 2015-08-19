import os
import dj_database_url

DEBUG = 'ZOO_DEBUG' in os.environ
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
if DEBUG:
	ALLOWED_HOSTS = ['*']
else:
	ALLOWED_HOSTS = ['zoo2translate.herokuapp.com']
	SECURE_HSTS_SECONDS = 31536000

INSTALLED_APPS = (
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'zoo2',
	'djcelery',
	'djkombu',
	'django_markdown',
)

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
# CELERY_RESULT_SERIALIZER = 'json'

MARKDOWN_EXTENSIONS = ['toc']
MARKDOWN_EXTENSION_CONFIGS = {'toc': {'baselevel': 2}}

MIDDLEWARE_CLASSES = (
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'zoo2.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'zoo2.urls'

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
			],
		},
	},
]

AUTHENTICATION_BACKENDS = (
	'mozilla.persona.PersonaBackend',
	'github.auth.GitHubBackend',
)

WSGI_APPLICATION = 'zoo2.wsgi.application'

DATABASES = {
	'default': dj_database_url.config()
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
	os.path.join(BASE_DIR, 'zoo2/static'),
)
