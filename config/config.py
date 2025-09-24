#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration de l'application Prix Carburants
"""

import os
from datetime import timedelta


class Config:
    """Configuration de base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuration Flask
    DEBUG = False
    TESTING = False
    
    # Configuration de l'application
    APP_NAME = "Prix Carburants France"
    APP_VERSION = "1.0.0"
    
    # Configuration des données
    DATA_URL = "https://donnees.roulez-eco.fr/opendata/instantane"
    DATA_REFRESH_INTERVAL = timedelta(hours=1)
    REQUEST_TIMEOUT = 60
    MAX_RETRIES = 3
    
    # Configuration des logs
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configuration cache
    CACHE_TTL = timedelta(minutes=30)
    
    # Headers HTTP
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'


class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    
    # Configuration sécurisée - sera vérifiée au moment de l'utilisation
    SECRET_KEY = os.environ.get('SECRET_KEY', 'PRODUCTION_SECRET_KEY_NOT_SET')


class TestingConfig(Config):
    """Configuration de test"""
    TESTING = True
    DEBUG = True
    DATA_REFRESH_INTERVAL = timedelta(seconds=10)


# Sélection automatique de la configuration
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Récupère la configuration selon l'environnement"""
    env = os.environ.get('FLASK_ENV', 'default')
    config_class = config_map.get(env, DevelopmentConfig)
    
    # Vérification spéciale pour la production
    if env == 'production' and not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY doit être définie en production")
    
    return config_class