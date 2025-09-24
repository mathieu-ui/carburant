#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Web Prix Carburants France
Interface web moderne utilisant Flask pour afficher les prix des carburants
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET
import zipfile
import io
from datetime import datetime
import threading
import time
import os


app = Flask(__name__)
CORS(app)

# Variables globales pour stocker les données
stations_data = []
data_loaded = False
last_update = None


def download_and_parse_data():
    """Télécharge et analyse les données XML"""
    global stations_data, data_loaded, last_update
    
    try:
        print("📥 Téléchargement des données...")
        
        # URL des données
        url = "https://donnees.roulez-eco.fr/opendata/instantane"
        
        # Headers pour éviter les blocages
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Télécharger le fichier ZIP avec retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"📡 Tentative {attempt + 1}/{max_retries}...")
                response = requests.get(url, timeout=60, headers=headers)
                response.raise_for_status()
                
                # Vérifier que c'est bien un fichier ZIP
                if not response.content.startswith(b'PK'):
                    raise Exception("Le fichier téléchargé n'est pas un ZIP valide")
                
                print(f"✅ Téléchargement réussi ({len(response.content)} bytes)")
                break
                
            except (requests.RequestException, Exception) as e:
                print(f"❌ Tentative {attempt + 1} échouée: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Impossible de télécharger après {max_retries} tentatives: {e}")
                time.sleep(2)  # Attendre 2 secondes avant de réessayer
        
        print("📦 Extraction et analyse des données...")
        
        # Extraire le fichier XML du ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Lister tous les fichiers dans le ZIP
            files_in_zip = zip_file.namelist()
            print(f"📋 Fichiers dans l'archive: {files_in_zip}")
            
            # Trouver le fichier XML dans le ZIP
            xml_filename = None
            for filename in files_in_zip:
                if filename.endswith('.xml'):
                    xml_filename = filename
                    break
            
            if not xml_filename:
                raise Exception(f"Aucun fichier XML trouvé dans l'archive. Fichiers disponibles: {files_in_zip}")
            
            print(f"📄 Fichier XML trouvé: {xml_filename}")
            
            # Lire le contenu XML
            with zip_file.open(xml_filename) as xml_file:
                xml_content = xml_file.read()
        
        print(f"📊 Taille du fichier XML: {len(xml_content)} octets")
        
        # Vérifier que le contenu n'est pas vide
        if len(xml_content) == 0:
            raise Exception("Le fichier XML est vide")
        
        # Parser le XML
        print("🔍 Analyse du fichier XML...")
        
        try:
            root = ET.fromstring(xml_content)
            print(f"🏗️ XML parsé avec succès. Élément racine: {root.tag}")
        except ET.ParseError as e:
            print(f"❌ Erreur de parsing XML: {e}")
            # Afficher les premiers caractères pour diagnostic
            try:
                preview = xml_content[:500].decode('utf-8', errors='ignore')
                print(f"📋 Aperçu du contenu: {preview}")
            except:
                print("📋 Impossible d'afficher l'aperçu du contenu")
            raise Exception(f"Erreur de parsing XML: {e}")
        
        new_stations = []
        pdv_elements = root.findall('pdv')
        print(f"🏪 {len(pdv_elements)} stations trouvées dans le XML")
        
        for i, pdv in enumerate(pdv_elements):
            # Afficher la progression tous les 1000 éléments
            if i > 0 and i % 1000 == 0:
                print(f"⏳ Traitement en cours... {i}/{len(pdv_elements)} stations ({i*100//len(pdv_elements)}%)")
            
            station = {
                'id': pdv.get('id', ''),
                'latitude': pdv.get('latitude', ''),
                'longitude': pdv.get('longitude', ''),
                'cp': pdv.get('cp', ''),
                'pop': pdv.get('pop', ''),  # R = Route, A = Autoroute
                'adresse': '',
                'ville': '',
                'horaires': {},
                'prix': {},
                'services': [],
                'marque': '',
                'automate_24h': False
            }
            
            # Adresse et ville
            adresse_elem = pdv.find('adresse')
            if adresse_elem is not None:
                station['adresse'] = adresse_elem.text or ''
            
            ville_elem = pdv.find('ville')
            if ville_elem is not None:
                station['ville'] = ville_elem.text or ''
            
            # Marque/nom de la station - amélioration de la détection
            nom_station = ''
            if station['adresse']:
                adresse_upper = station['adresse'].upper()
                
                # Liste étendue des marques de stations-service
                marques_principales = {
                    'TOTAL': ['TOTAL', 'TOTALENERGIES'],
                    'SHELL': ['SHELL'],
                    'BP': ['BP'],
                    'ESSO': ['ESSO'],
                    'AGIP': ['AGIP'],
                    'CARREFOUR': ['CARREFOUR'],
                    'LECLERC': ['LECLERC', 'E.LECLERC'],
                    'INTERMARCHE': ['INTERMARCHE', 'INTERMARCHÉ'],
                    'SUPER U': ['SUPER U', 'MAGASINS U'],
                    'CASINO': ['CASINO'],
                    'AUCHAN': ['AUCHAN'],
                    'HYPER U': ['HYPER U'],
                    'SYSTÈME U': ['SYSTEME U'],
                    'CORA': ['CORA'],
                    'GÉANT': ['GEANT'],
                    'STATION': ['STATION'],
                    'RELAIS': ['RELAIS'],
                    'MARKET': ['MARKET'],
                    'SPAR': ['SPAR'],
                    'VIVAL': ['VIVAL'],
                    'PROXY': ['PROXY'],
                    'PETIT CASINO': ['PETIT CASINO'],
                    'LEADER PRICE': ['LEADER PRICE'],
                    'MONOPRIX': ['MONOPRIX'],
                    'SIMPLY': ['SIMPLY'],
                    'FRANPRIX': ['FRANPRIX']
                }
                
                # Recherche de marque dans l'adresse
                for marque_affichee, variantes in marques_principales.items():
                    for variante in variantes:
                        if variante in adresse_upper:
                            nom_station = marque_affichee
                            break
                    if nom_station:
                        break
                
                # Si aucune marque trouvée, essayer d'extraire un nom depuis l'adresse
                if not nom_station:
                    # Recherche de patterns de noms de stations
                    mots = station['adresse'].split()
                    for i, mot in enumerate(mots):
                        mot_upper = mot.upper()
                        # Patterns courants
                        if any(pattern in mot_upper for pattern in ['STATION', 'GARAGE', 'RELAIS', 'SHOP', 'MARKET']):
                            # Prendre le mot précédent s'il existe
                            if i > 0 and len(mots[i-1]) > 2:
                                nom_station = mots[i-1].title()
                            else:
                                nom_station = mot.title()
                            break
                
                # Dernière tentative : prendre le premier mot s'il semble être un nom
                if not nom_station and station['adresse']:
                    premier_mot = station['adresse'].split()[0] if station['adresse'].split() else ''
                    if len(premier_mot) > 3 and premier_mot.upper() not in ['ROUTE', 'RUE', 'AVENUE', 'PLACE', 'BOULEVARD']:
                        nom_station = premier_mot.title()
            
            station['marque'] = nom_station or 'Station-service'
            
            # Prix
            for prix in pdv.findall('prix'):
                nom = prix.get('nom', '')
                valeur = prix.get('valeur', '')
                maj = prix.get('maj', '')
                
                if nom and valeur:
                    try:
                        station['prix'][nom] = {
                            'valeur': float(valeur),
                            'maj': maj,
                            'maj_formatted': format_date(maj)
                        }
                    except ValueError:
                        continue
            
            # Services
            services_elem = pdv.find('services')
            if services_elem is not None:
                for service in services_elem.findall('service'):
                    if service.text:
                        station['services'].append(service.text.strip())
            
            # Horaires
            horaires_elem = pdv.find('horaires')
            if horaires_elem is not None:
                station['automate_24h'] = horaires_elem.get('automate-24-24') == '1'
                
                for jour in horaires_elem.findall('jour'):
                    jour_nom = jour.get('nom', '')
                    ferme = jour.get('ferme', '') == '1'
                    
                    if jour_nom:
                        station['horaires'][jour_nom] = {
                            'ferme': ferme,
                            'horaires_detail': []
                        }
                        
                        # Horaires détaillés
                        for horaire in jour.findall('horaire'):
                            ouverture = horaire.get('ouverture', '')
                            fermeture = horaire.get('fermeture', '')
                            if ouverture and fermeture:
                                station['horaires'][jour_nom]['horaires_detail'].append({
                                    'ouverture': ouverture,
                                    'fermeture': fermeture
                                })
            
            # Ajouter la station seulement si elle a une ville
            if station['ville']:
                new_stations.append(station)
        
        stations_data = new_stations
        data_loaded = True
        last_update = datetime.now()
        
        print(f"✅ {len(stations_data)} stations chargées avec succès!")
        
    except requests.RequestException as e:
        print(f"❌ Erreur de téléchargement: {str(e)}")
        print("🌐 Vérifiez votre connexion internet")
        data_loaded = False
    except zipfile.BadZipFile as e:
        print(f"❌ Erreur de ZIP: {str(e)}")
        print("📦 Le fichier téléchargé n'est pas un ZIP valide")
        data_loaded = False
    except ET.ParseError as e:
        print(f"❌ Erreur XML: {str(e)}")
        print("📄 Le fichier XML est malformé ou corrompu")
        data_loaded = False
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")
        print(f"📋 Type d'erreur: {type(e).__name__}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        data_loaded = False


def format_date(date_str):
    """Formate une date pour l'affichage"""
    if not date_str:
        return "Non renseigné"
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return date.strftime('%d/%m/%Y à %H:%M')
    except ValueError:
        return date_str


def get_latest_update_date(prix_dict):
    """Récupère la date de mise à jour la plus récente"""
    if not prix_dict:
        return "Non renseigné"
    
    dates = []
    for prix_info in prix_dict.values():
        if 'maj' in prix_info and prix_info['maj']:
            try:
                date = datetime.strptime(prix_info['maj'], '%Y-%m-%d %H:%M:%S')
                dates.append(date)
            except ValueError:
                continue
    
    if dates:
        latest = max(dates)
        return latest.strftime('%d/%m/%Y à %H:%M')
    
    return "Non renseigné"


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')


@app.route('/api/search')
def api_search():
    """Recherche des stations par ville"""
    ville = request.args.get('ville', '').strip()
    
    if not ville:
        return jsonify({'error': 'Nom de ville requis'}), 400
    
    if not data_loaded:
        return jsonify({'error': 'Données non chargées'}), 503
    
    # Recherche des stations
    ville_lower = ville.lower()
    results = []
    
    for station in stations_data:
        if ville_lower in station['ville'].lower():
            # Convertir le dictionnaire des prix en liste pour le frontend
            prix_list = []
            for nom, info in station['prix'].items():
                prix_list.append({
                    'nom': nom,
                    'valeur': info['valeur'],
                    'maj': info['maj_formatted']
                })
            
            # Formater les horaires en texte lisible
            horaires_text = "Horaires non disponibles"
            if station['automate_24h']:
                horaires_text = "Automate 24h/24"
            elif station['horaires']:
                # Simplifier l'affichage des horaires
                jours_ouverts = []
                for jour, info in station['horaires'].items():
                    if not info['ferme'] and info['horaires_detail']:
                        premier_horaire = info['horaires_detail'][0]
                        jours_ouverts.append(f"{jour}: {premier_horaire['ouverture']}-{premier_horaire['fermeture']}")
                
                if jours_ouverts:
                    horaires_text = "; ".join(jours_ouverts[:3])  # Limiter à 3 jours pour l'affichage
                    if len(jours_ouverts) > 3:
                        horaires_text += "..."
            
            # Préparer les données de la station pour l'API
            station_data = {
                'id': station['id'],
                'adresse': station['adresse'],
                'ville': station['ville'],
                'cp': station['cp'],
                'marque': station['marque'],
                'type': 'Autoroute' if station['pop'] == 'A' else 'Route',
                'automate_24h': station['automate_24h'],
                'prix': prix_list,
                'services': station['services'],
                'horaires': horaires_text,
                'latitude': station['latitude'],
                'longitude': station['longitude'],
                'derniere_maj': get_latest_update_date(station['prix'])
            }
            results.append(station_data)
    
    # Trier par date de mise à jour (plus récent en premier), puis par ville et adresse
    def get_sort_key(station):
        # Convertir la date de mise à jour en timestamp pour le tri
        if station['derniere_maj'] and station['derniere_maj'] != "Non renseigné":
            try:
                # Parse la date au format "dd/mm/yyyy à hh:mm"
                date_str = station['derniere_maj']
                date_obj = datetime.strptime(date_str, '%d/%m/%Y à %H:%M')
                # Retourner un timestamp négatif pour avoir les plus récents en premier
                return (-date_obj.timestamp(), station['ville'], station['adresse'])
            except ValueError:
                # Si le parsing échoue, mettre à la fin
                return (float('inf'), station['ville'], station['adresse'])
        else:
            # Stations sans date de mise à jour à la fin
            return (float('inf'), station['ville'], station['adresse'])
    
    results.sort(key=get_sort_key)
    
    return jsonify({
        'stations': results,
        'count': len(results),
        'ville': ville
    })


def auto_refresh_data():
    """Actualise automatiquement les données toutes les heures"""
    while True:
        time.sleep(3600)  # Attendre 1 heure (3600 secondes)
        if data_loaded:  # Ne lancer une nouvelle actualisation que si les données précédentes sont chargées
            print("🔄 Actualisation automatique des données...")
            download_and_parse_data()


def init_data():
    """Initialise les données au démarrage"""
    print("🚀 Démarrage de l'application Prix Carburants Web")
    
    # Lancer le chargement initial des données en arrière-plan
    initial_thread = threading.Thread(target=download_and_parse_data)
    initial_thread.daemon = True
    initial_thread.start()
    
    # Lancer le thread d'actualisation automatique toutes les heures
    auto_refresh_thread = threading.Thread(target=auto_refresh_data)
    auto_refresh_thread.daemon = True
    auto_refresh_thread.start()
    
    print("⏰ Actualisation automatique programmée toutes les heures")


if __name__ == '__main__':
    # Créer le dossier templates s'il n'existe pas
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Initialiser les données
    init_data()
    
    # Lancer l'application
    print("\n🌐 Application web démarrée!")
    print("📍 Ouvrez votre navigateur sur: http://localhost:5000")
    print("🔄 Appuyez sur Ctrl+C pour arrêter l'application")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
