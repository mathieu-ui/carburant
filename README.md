# 🚗 Application Prix Carburants - Version Production

Une application web moderne et performante utilisant Flask pour afficher les prix des carburants en France en temps réel.

## 🌟 Fonctionnalités

- **Recherche intelligente** : Recherche de stations-service par ville avec suggestions
- **Données en temps réel** : Prix des carburants actualisés automatiquement
- **Interface moderne** : Design responsive avec Bootstrap 5 et animations CSS
- **Filtrage avancé** : Par type de carburant, horaires, type de station
- **Intégration cartes** : Géolocalisation avec Google Maps
- **Cache intelligent** : Performance optimisée avec système de cache
- **Architecture modulaire** : Code refactorisé pour la production
- **API REST** : Endpoints API documentés
- **Gestion d'erreurs** : Pages d'erreur personnalisées
- **Monitoring** : Health checks et logging avancé

## 🏗️ Architecture

```
├── app/                    # Application principale
│   ├── __init__.py        # Factory Flask
│   ├── api/               # Routes API
│   ├── models/            # Modèles de données
│   ├── services/          # Services métier
│   └── utils/             # Utilitaires
├── config/                # Configuration
├── static/                # Ressources statiques
│   ├── css/              # Styles CSS
│   └── js/               # JavaScript
├── templates/             # Templates HTML
│   └── errors/           # Pages d'erreur
├── main.py               # Point d'entrée production
├── wsgi.py              # Configuration WSGI
└── Dockerfile           # Configuration Docker
```

## 🚀 Installation et Démarrage

### Méthode 1 : Installation locale

1. **Clonez le repository** :
```bash
git clone [URL_DU_REPO]
cd prix-carburants-web
```

2. **Créez un environnement virtuel** :
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Installez les dépendances** :
```bash
pip install -r requirements.txt
```

4. **Configurez l'environnement** :
```bash
cp .env.example .env
# Éditez .env avec vos paramètres
```

5. **Lancez l'application** :
```bash
# Mode développement
python app/__init__.py

# Mode production
python main.py
```

### Méthode 2 : Docker

1. **Construction et lancement** :
```bash
docker-compose up --build
```

2. **Accédez à l'application** : http://localhost:5000

## 📊 API Endpoints

### Recherche de stations
```
GET /api/search?ville=Paris&type=autoroute&carburants=SP95,Gazole
```

### Suggestions de villes
```
GET /api/suggestions?q=Par&limit=10
```

### Statut de l'application
```
GET /api/status
```

## 🎨 Utilisation

1. **Recherche simple** : Entrez une ville et cliquez sur "Rechercher"
2. **Recherche avancée** : Utilisez les filtres pour affiner vos résultats
3. **Navigation** : Cliquez sur une station pour la voir sur Google Maps
4. **Tri et filtres** : Organisez les résultats selon vos préférences

## 🛠️ Développement

### Structure modulaire
- **Models** : Dataclasses pour les structures de données
- **Services** : Logique métier (téléchargement, parsing, recherche)
- **Utils** : Utilitaires (cache, formatage, extracteurs)
- **API** : Routes REST avec gestion d'erreurs
- **Frontend** : JavaScript modulaire avec classes

## 📈 Performance

- **Cache en mémoire** : Réduction des appels API
- **Compression CSS/JS** : Ressources optimisées
- **Lazy loading** : Chargement asynchrone des données
- **Connection pooling** : Réutilisation des connexions HTTP

## 📚 Technologies

### Backend
- **Python 3.11+** : Langage principal
- **Flask 3.0** : Framework web
- **Requests** : Client HTTP
- **lxml** : Parsing XML performant
- **Gunicorn** : Serveur WSGI production

### Frontend
- **HTML5** : Structure sémantique
- **CSS3** : Styles modernes avec variables CSS
- **JavaScript ES6+** : Logique interactive
- **Bootstrap 5** : Framework UI
- **Font Awesome** : Icônes

## 📊 Données

**Source officielle** : [Données ouvertes du gouvernement français](https://donnees.roulez-eco.fr/opendata/instantane)

- **Format** : XML dans archive ZIP
- **Fréquence** : Mise à jour automatique chaque heure
- **Couverture** : Toutes les stations-service de France
- **Fraîcheur** : Indicateurs visuels selon l'âge des données

## 📄 Licence

Ce projet est sous licence MIT.