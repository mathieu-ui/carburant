#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour l'application Prix Carburants
Version de production
"""

import os
import sys
import logging
from app import create_app

# Charger les variables d'environnement depuis .env si disponibles
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv non installé, les variables .env ne seront pas chargées")

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_production_app():
    """Crée l'application pour la production"""
    # Configuration de l'environnement (utiliser development par défaut pour les tests)
    os.environ.setdefault('FLASK_ENV', os.environ.get('FLASK_ENV', 'development'))
    
    # Créer l'application
    app = create_app()
    
    return app

if __name__ == '__main__':
    # Configuration du logging pour la production
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Créer l'application
    app = create_production_app()
    
    # Configuration du serveur
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Démarrage de l'application Prix Carburants en mode PRODUCTION")
    print(f"URL: http://{host}:{port}")
    print(f"Logs: app.log")
    
    # Lancer le serveur
    app.run(host=host, port=port, debug=False)