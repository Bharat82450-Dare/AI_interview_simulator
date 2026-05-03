# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from environs import Env

env = Env()
env.read_env()

ENV = env.str("FLASK_ENV", default="production")
DEBUG = ENV == "development"
SQLALCHEMY_DATABASE_URI = env.str("DATABASE_URL", default="sqlite:///dev2.db")
SECRET_KEY = env.str("SECRET_KEY")
SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT")
GOOGLE_API_KEY = env.str("GOOGLE_API_KEY")
GEMINI_MODEL = env.str("GEMINI_MODEL", default="gemini-2.0-flash")
BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
DEBUG_TB_ENABLED = env.bool("DEBUG_TB_ENABLED", default=False)
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = "SimpleCache"  # Can be "MemcachedCache", "RedisCache", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False
