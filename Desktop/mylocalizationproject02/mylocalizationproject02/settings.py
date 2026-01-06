# import os
# from pathlib import Path

# """
# Django settings for mylocalizationproject project.
# """

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECRET_KEY = "django-insecure-%kzv7eni0hy6j0duzjfx(6#jqz_9(*00ar6lj$cwka!-bk=s5e"
# DEBUG = True
# ALLOWED_HOSTS = ['88.222.241.110', '127.0.0.1', 'localhost']

# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "localizationtool",
#     "modeltranslation",
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# ROOT_URLCONF = "mylocalizationproject.urls"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [os.path.join(BASE_DIR, 'templates')],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = "mylocalizationproject.wsgi.application"

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
#     }
# }

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
# ]

# LANGUAGE_CODE = "en-us"
# TIME_ZONE = "UTC"

# from django.utils.translation import gettext_lazy as _

# LANGUAGES = (
#     ('en', _('English')),
#     ('en-us', _('American English')),
#     ('en-gb', _('British English')),
#     ('en-ca', _('Canadian English')),
#     ('en-au', _('Australian English')),
#     ('es', _('Spanish')),
#     ('es-es', _('Spanish (Spain)')),
#     ('es-mx', _('Spanish (Mexico)')),
#     ('es-ar', _('Spanish (Argentina)')),
#     ('de', _('German')),
#     ('de-de', _('German (Germany)')),
#     ('de-at', _('German (Austria)')),
#     ('de-ch', _('German (Switzerland)')),
#     ('fr', _('French')),
#     ('fr-fr', _('French (France)')),
#     ('fr-ca', _('French (Canada)')),
#     ('fr-be', _('French (Belgium)')),
#     ('pt', _('Portuguese')),
#     ('pt-br', _('Portuguese (Brazil)')),
#     ('pt-pt', _('Portuguese (Portugal)')),
#     ('hi', _('Hindi')),
#     ('ne', _('Nepali')),
# )

# MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'

# USE_I18N = True
# USE_TZ = True

# STATIC_URL = "static/"
# # STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Uncomment for production
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'localizationtool', 'static')]

# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# # Explicitly define storage backends to prevent overrides
# STORAGES = {
#     "default": {
#         "BACKEND": "django.core.files.storage.FileSystemStorage",
#         "LOCATION": MEDIA_ROOT,  # Must be /Users/mac/Desktop/mylocalizationproject/media
#         "OPTIONS": {
#             "base_url": MEDIA_URL,
#         },
#     },
#     "staticfiles": {
#         "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
#     },
# }

# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# import os
# from pathlib import Path
# from django.utils.translation import gettext_lazy as _

# """
# Django settings for mylocalizationproject project.
# """

# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = "django-insecure-%kzv7eni0hy6j0duzjfx(6#jqz_9(*00ar6lj$cwka!-bk=s5e"
# DEBUG = True
# ALLOWED_HOSTS = ['88.222.241.110', '127.0.0.1', 'localhost']

# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "localizationtool",
#     "modeltranslation",  # Keep this — we fixed it below
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# ROOT_URLCONF = "mylocalizationproject.urls"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [BASE_DIR / 'templates'],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.debug",
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = "mylocalizationproject.wsgi.application"

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
# ]

# # === INTERNATIONALIZATION ===
# LANGUAGE_CODE = 'en-us'  # Standard Django format (lowercase, hyphen)

# # === LANGUAGES: Only valid codes (Django accepts 'en-us', 'en-gb', etc.) ===


# LANGUAGES = [
#     ('en', 'English'),
#     ('en-us', 'English (US)'),
#     ('en-ca', 'English (Canada)'),
#     ('en-au', 'English (Australia)'),
#     ('en-nz', 'English (New Zealand)'),
    
#     ('es', 'Spanish'),
#     ('es-ar', 'Spanish (Argentina)'),
#     ('es-mx', 'Spanish (Mexico)'),
#     ('es-cl', 'Spanish (Chile)'),
#     ('es-co', 'Spanish (Colombia)'),
#     ('es-pe', 'Spanish (Peru)'),
    
#     ('fr', 'French'),
#     ('fr-ca', 'French (Canada)'),
    
#     ('pt', 'Portuguese'),
#     ('pt-br', 'Portuguese (Brazil)'),
    
#     ('de', 'German'),
#     ('it', 'Italian'),
#     ('nl', 'Dutch'),
#     ('nl-be', 'Dutch (Belgium)'),
#     ('pl', 'Polish'),
#     ('ru', 'Russian'),
#     ('ar', 'Arabic'),
#     ('ja', 'Japanese'),
#     ('ko', 'Korean'),
    
#     ('id', 'Indonesian'),
#     ('hi', 'Hindi'),
#     ('ne', 'Nepali'),
    
#     # === NEW LANGUAGES BELOW ===
#     ('th', 'Thai'),
#     ('tl', 'Filipino'),           # Philippines
#     ('sw', 'Swahili'),            # Kenya, Tanzania, Ghana
#     ('af', 'Afrikaans'),          # South Africa
#     ('sv', 'Swedish'),            # Sweden / Nordics
#     ('no', 'Norwegian'),          # Norway
#     ('da', 'Danish'),             # Denmark
#     ('fi', 'Finnish'),            # Finland
#     ('yo', 'Yoruba'),             # Nigeria
# ]

# # === MODELTRANSLATION SETTINGS ===
# MODELTRANSLATION_DEFAULT_LANGUAGE = 'en-us'  # Must match a code in LANGUAGES
# MODELTRANSLATION_LOCALE_PATH = BASE_DIR / 'locale'  # Optional: for .po files

# TIME_ZONE = "UTC"
# USE_I18N = True
# USE_TZ = True

# # === STATIC & MEDIA ===
# STATIC_URL = "/static/"
# STATICFILES_DIRS = [
#     BASE_DIR / "localizationtool" / "static",
# ]
# STATIC_ROOT = BASE_DIR / "staticfiles"

# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"

# STORAGES = {
#     "default": {
#         "BACKEND": "django.core.files.storage.FileSystemStorage",
#     },
#     "staticfiles": {
#         "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
#     },
# }

# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"




# import os
# from pathlib import Path
# from django.utils.translation import gettext_lazy as _

# """
# Django settings for mylocalizationproject02 project.
# """

# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = "django-insecure-%kzv7eni0hy6j0duzjfx(6#jqz_9(*00ar6lj$cwka!-bk=s5e"
# DEBUG = True
# ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "localizationtool",
#     "modeltranslation",
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# # Updated for copy project
# ROOT_URLCONF = 'mylocalizationproject02.urls'
# WSGI_APPLICATION = 'mylocalizationproject02.wsgi.application'

# # ✅ FIXED: Added Django template backend (required for admin)
# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [BASE_DIR / "templates"],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.debug",
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
# ]

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db_copy.sqlite3",  # separate DB for copy
#     }
# }

# AUTH_PASSWORD_VALIDATORS = [
#     {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
#     {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
#     {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
#     {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
# ]

# # === INTERNATIONALIZATION ===
# LANGUAGE_CODE = 'en-us'

# LANGUAGES = [
#     ('en', 'English'),
#     ('en-us', 'English (US)'),
#     ('en-ca', 'English (Canada)'),
#     ('en-au', 'English (Australia)'),
#     ('en-nz', 'English (New Zealand)'),

#     ('es', 'Spanish'),
#     ('es-ar', 'Spanish (Argentina)'),
#     ('es-mx', 'Spanish (Mexico)'),
#     ('es-cl', 'Spanish (Chile)'),
#     ('es-co', 'Spanish (Colombia)'),
#     ('es-pe', 'Spanish (Peru)'),

#     ('fr', 'French'),
#     ('fr-ca', 'French (Canada)'),

#     ('pt', 'Portuguese'),
#     ('pt-br', 'Portuguese (Brazil)'),

#     ('de', 'German'),
#     ('it', 'Italian'),
#     ('nl', 'Dutch'),
#     ('nl-be', 'Dutch (Belgium)'),
#     ('pl', 'Polish'),
#     ('ru', 'Russian'),
#     ('ar', 'Arabic'),
#     ('ja', 'Japanese'),
#     ('ko', 'Korean'),

#     ('id', 'Indonesian'),
#     ('hi', 'Hindi'),
#     ('ne', 'Nepali'),

#     # NEW LANGUAGES
#     ('th', 'Thai'),
#     ('tl', 'Filipino'),
#     ('sw', 'Swahili'),
#     ('af', 'Afrikaans'),
#     ('sv', 'Swedish'),
#     ('no', 'Norwegian'),
#     ('da', 'Danish'),
#     ('fi', 'Finnish'),
#     ('yo', 'Yoruba'),
# ]

# MODELTRANSLATION_DEFAULT_LANGUAGE = 'en-us'
# MODELTRANSLATION_LOCALE_PATH = BASE_DIR / 'locale'

# TIME_ZONE = "UTC"
# USE_I18N = True
# USE_TZ = True

# # === STATIC & MEDIA ===
# STATIC_URL = "/static/"
# STATICFILES_DIRS = [BASE_DIR / "localizationtool" / "static"]
# STATIC_ROOT = BASE_DIR / "staticfiles_copy"

# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media_copy"

# STORAGES = {
#     "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
#     "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
# }

# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"





# settings.py
# import os
# from pathlib import Path
# from django.utils.translation import gettext_lazy as _

# """
# Django settings for mylocalizationproject02 project.
# """

# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = "django-insecure-%kzv7eni0hy6j0duzjfx(6#jqz_9(*00ar6lj$cwka!-bk=s5e"
# DEBUG = True
# ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "localizationtool",
#     "modeltranslation",
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# ROOT_URLCONF = 'mylocalizationproject02.urls'
# WSGI_APPLICATION = 'mylocalizationproject02.wsgi.application'

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [BASE_DIR / "templates"],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.debug",
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
# ]

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db_copy.sqlite3",
#     }
# }

# AUTH_PASSWORD_VALIDATORS = [
#     {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
#     {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
#     {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
#     {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
# ]

# # === INTERNATIONALIZATION ===
# LANGUAGE_CODE = 'en-us'

# LANGUAGES = [
#     ('en', 'English'),
#     ('en-us', 'English (US)'),
#     ('en-gb', 'English (UK)'),
#     ('en-ca', 'English (Canada)'),
#     ('en-au', 'English (Australia)'),
#     ('en-nz', 'English (New Zealand)'),
#     ('en-ng', 'English (Nigeria)'),
#     ('en-za', 'English (South Africa)'),
#     ('en-gh', 'English (Ghana)'),

#     ('es', 'Spanish'),
#     ('es-ar', 'Spanish (Argentina)'),
#     ('es-mx', 'Spanish (Mexico)'),
#     ('es-cl', 'Spanish (Chile)'),
#     ('es-co', 'Spanish (Colombia)'),
#     ('es-pe', 'Spanish (Peru)'),

#     ('fr', 'French'),
#     ('fr-ca', 'French (Canada)'),

#     ('pt', 'Portuguese'),
#     ('pt-br', 'Portuguese (Brazil)'),

#     ('de', 'German'),
#     ('it', 'Italian'),
#     ('nl', 'Dutch'),
#     ('nl-be', 'Dutch (Belgium)'),
#     ('pl', 'Polish'),
#     ('ru', 'Russian'),
#     ('ar', 'Arabic'),
#     ('ar-eg', 'Arabic (Egypt)'),
#     ('ja', 'Japanese'),
#     ('ko', 'Korean'),

#     ('id', 'Indonesian'),
#     ('hi', 'Hindi'),
#     ('ne', 'Nepali'),

#     # NEW LANGUAGES
#     ('th', 'Thai'),
#     ('tl', 'Filipino'),
#     ('sw', 'Swahili'),
#     ('af', 'Afrikaans'),
#     ('sv', 'Swedish'),
#     ('no', 'Norwegian'),
#     ('da', 'Danish'),
#     ('fi', 'Finnish'),
#     ('yo', 'Yoruba'),
# ]

# MODELTRANSLATION_DEFAULT_LANGUAGE = 'en-us'
# MODELTRANSLATION_LOCALE_PATH = BASE_DIR / 'locale'

# TIME_ZONE = "UTC"
# USE_I18N = True
# USE_TZ = True

# # === STATIC & MEDIA ===
# STATIC_URL = "/static/"
# STATICFILES_DIRS = [BASE_DIR / "localizationtool" / "static"]
# STATIC_ROOT = BASE_DIR / "staticfiles_copy"

# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media_copy"

# STORAGES = {
#     "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
#     "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
# }

# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-%kzv7eni0hy6j0duzjfx(6#jqz_9(*00ar6lj$cwka!-bk=s5e"
DEBUG = True
# ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
ALLOWED_HOSTS = ['wptranslate.org', 'www.wptranslate.org', '88.222.241.110', '127.0.0.1', 'localhost']

# to fix the 403 Forbidden error
CSRF_TRUSTED_ORIGINS = [
    'https://wptranslate.org',
    'https://www.wptranslate.org'
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "localizationtool",
    "modeltranslation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'mylocalizationproject02.urls'
WSGI_APPLICATION = 'mylocalizationproject02.wsgi.application'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_copy.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === INTERNATIONALIZATION ===
LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
    ('de', _('German')),
    ('fr', _('French')),
    ('pt', _('Portuguese')),
    ('hi', _('Hindi')),
    ('ne', _('Nepali')),
    ('ar', _('Arabic')),
    ('it', _('Italian')),
    ('ja', _('Japanese')),
    ('pl', _('Polish')),
    ('ru', _('Russian')),
    ('nl', _('Dutch')),
    ('id', _('Indonesian')),
    ('th', _('Thai')),
    ('tl', _('Filipino')),
    ('ko', _('Korean')),
    ('en-gb', _('English (UK)')),
    # NEW LANGUAGES
    ('sw', 'Swahili'),       # Kenya
    ('da', 'Danish'),        # Denmark
    ('fi', 'Finnish'),       # Finland
    ('is', 'Icelandic'),     # Iceland
    ('no', 'Norwegian'),     # Norway
    ('sv', 'Swedish'),       # Sweden
    # ('ar', 'Arabic'),        # Egypt
    ('zh-CH', 'Chinese (Simplified)'),



)

MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_LOCALE_PATH = BASE_DIR / 'locale'

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "localizationtool" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles_copy"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR , "media_copy")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"