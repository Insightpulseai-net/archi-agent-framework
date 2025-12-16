"""
Superset Configuration for Production
Configures PostgreSQL as metadata database (not SQLite)
"""
import os

# Construct PostgreSQL connection URI from environment variables
DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
DATABASE_DB = os.getenv('DATABASE_DB', 'postgres')

# Metadata database (Superset's own data)
# Use Supabase Postgres, NOT SQLite
SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}'

# Security
SECRET_KEY = os.getenv('SUPERSET_SECRET_KEY', 'change-me-in-production')

# Performance
SUPERSET_WEBSERVER_TIMEOUT = 300
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20

# Feature flags
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'DASHBOARD_NATIVE_FILTERS_SET': True,
}

# Disable SQLite check (we're using Postgres)
PREVENT_UNSAFE_DB_CONNECTIONS = False

# Logging
import logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
ENABLE_TIME_ROTATE = True
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
LOG_LEVEL = logging.INFO

# Session configuration
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
