#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Factory pour créer l'application Flask
"""

import os
import logging
import threading
from flask import Flask, render_template
from flask_cors import CORS

from config.config import get_config
from .api import api_bp
from .services import data_service


def create_app(config_name=None):
    """Factory pour créer l'application Flask"""
    
    # Créer l'application Flask
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Configuration
    config = get_config() if config_name is None else config_name
    app.config.from_object(config)
    
    # Configuration des logs
    setup_logging(app)
    
    # CORS
    CORS(app)
    
    # Enregistrer les blueprints
    app.register_blueprint(api_bp)
    
    # Routes principales
    @app.route('/')
    def index():
        """Page principale"""
        return render_template('index.html')
    
    @app.route('/health')
    def health_check():
        """Health check pour les déploiements"""
        return {'status': 'healthy', 'service': 'prix-carburants'}, 200
    
    # Gestionnaires d'erreur
    setup_error_handlers(app)
    
    # Initialiser les services en arrière-plan
    setup_services(app)
    
    return app


def setup_logging(app):
    """Configure le système de logging"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_format = app.config.get('LOG_FORMAT')
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            # Ajouter un FileHandler pour la production si nécessaire
        ]
    )
    
    # Logger pour l'application
    logger = logging.getLogger(__name__)
    logger.info(f"Application {app.config['APP_NAME']} v{app.config['APP_VERSION']} démarrée")
    logger.info(f"Mode: {'DEBUG' if app.debug else 'PRODUCTION'}")


def setup_error_handlers(app):
    """Configure les gestionnaires d'erreur globaux"""
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Erreur interne: {error}')
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return render_template('errors/503.html'), 503


def setup_services(app):
    """Initialise les services en arrière-plan"""
    def init_services():
        logger = logging.getLogger(__name__)
        logger.info("Initialisation des services...")
        
        # Chargement initial des données
        success = data_service.load_data()
        if success:
            logger.info("Services initialisés avec succès")
            # Démarrer l'actualisation automatique
            data_service.start_auto_refresh()
        else:
            logger.error("Échec de l'initialisation des services")
    
    # Lancer l'initialisation en arrière-plan
    init_thread = threading.Thread(target=init_services, daemon=True)
    init_thread.start()


def create_directories():
    """Crée les dossiers nécessaires s'ils n'existent pas"""
    directories = ['templates', 'static', 'static/css', 'static/js']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Dossier créé: {directory}")


if __name__ == '__main__':
    # Créer les dossiers nécessaires
    create_directories()
    
    # Créer l'application
    app = create_app()
    
    # Configuration du serveur
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\nApplication web démarrée!")
    print(f"URL: http://localhost:{port}")
    print(f"Appuyez sur Ctrl+C pour arrêter")
    
    # Lancer le serveur
    app.run(host=host, port=port, debug=debug)