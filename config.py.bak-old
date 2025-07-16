#!/usr/bin/env python3
"""
Configuration for DSR Circuits Application
Includes database, cache, and application settings
"""

import os
import redis

class Config:
    """Base configuration"""
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Redis Configuration
    REDIS_URL = 'redis://localhost:6379/0'
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour
    
    # Application Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dsrcircuits-dev-key-2025'
    
    # Data Directories
    JSON_CACHE_DIR = "/var/www/html/json-cache"
    MERAKI_DATA_DIR = "/var/www/html/meraki-data"
    TRACKING_DATA_DIR = "/var/www/html/circuitinfo"
    
    # Performance Settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set to True for SQL debugging

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Redis connection helper
def get_redis_connection():
    """Get Redis connection with error handling"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return None