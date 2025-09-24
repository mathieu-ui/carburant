# Configuration pour serveur WSGI (Gunicorn, uWSGI, etc.)
import os
import sys

# Ajouter le répertoire de l'application au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Créer l'application WSGI
application = create_app()

if __name__ == "__main__":
    application.run()