import os


def pytest_configure():
    from django.conf import settings

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_TEMPLATE_DIR = os.path.join(os.path.dirname(BASE_DIR), 'templates')

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL='/static/',
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'django.contrib.staticfiles',

            'tutelary',
            'tests',
        ),
        AUTHENTICATION_BACKENDS=[
            'tutelary.backends.Backend'
        ],
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        },
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [BASE_TEMPLATE_DIR],
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                    'loaders': [
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader'
                    ],
                },
            },
        ]
    )

    try:
        import django
        django.setup()
    except AttributeError:
        pass
