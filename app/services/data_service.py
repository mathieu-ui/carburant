#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de téléchargement et parsing des données carburant
"""

import requests
import xml.etree.ElementTree as ET
import zipfile
import io
import threading
import time
import logging
from typing import List, Optional
from datetime import datetime

from ..models import Station, Prix, Horaire, JourHoraires
from ..utils import BrandExtractor
from config.config import get_config

logger = logging.getLogger(__name__)


class DataDownloader:
    """Service de téléchargement des données"""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT
        })
    
    def download_data(self) -> bytes:
        """Télécharge les données ZIP depuis l'API gouvernementale"""
        logger.info("Téléchargement des données...")
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                logger.debug(f"Tentative {attempt + 1}/{self.config.MAX_RETRIES}...")
                
                response = self.session.get(
                    self.config.DATA_URL,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                if not response.content.startswith(b'PK'):
                    raise ValueError("Le fichier téléchargé n'est pas un ZIP valide")
                
                logger.info(f"Téléchargement réussi ({len(response.content)} bytes)")
                return response.content
                
            except (requests.RequestException, ValueError) as e:
                logger.warning(f"Tentative {attempt + 1} échouée: {e}")
                if attempt == self.config.MAX_RETRIES - 1:
                    raise Exception(f"Impossible de télécharger après {self.config.MAX_RETRIES} tentatives: {e}")
                time.sleep(2)  # Attendre 2 secondes avant de réessayer
    
    def extract_xml(self, zip_data: bytes) -> str:
        """Extrait le fichier XML du ZIP"""
        logger.info("Extraction du fichier XML...")
        
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            files_in_zip = zip_file.namelist()
            logger.debug(f"Fichiers dans l'archive: {files_in_zip}")
            
            # Trouver le fichier XML
            xml_filename = None
            for filename in files_in_zip:
                if filename.endswith('.xml'):
                    xml_filename = filename
                    break
            
            if not xml_filename:
                raise Exception(f"Aucun fichier XML trouvé. Fichiers: {files_in_zip}")
            
            logger.debug(f"Fichier XML trouvé: {xml_filename}")
            
            with zip_file.open(xml_filename) as xml_file:
                xml_bytes = xml_file.read()
                # Essayer différents encodages
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        xml_content = xml_bytes.decode(encoding)
                        logger.debug(f"Fichier XML decodé avec l'encodage: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise Exception("Impossible de décoder le fichier XML avec les encodages supportés")
        
        if len(xml_content) == 0:
            raise Exception("Le fichier XML est vide")
            
        logger.info(f"Taille du fichier XML: {len(xml_content)} caractères")
        return xml_content


class DataParser:
    """Service de parsing des données XML"""
    
    def __init__(self):
        self.brand_extractor = BrandExtractor()
    
    def parse_xml(self, xml_content: str) -> List[Station]:
        """Parse le contenu XML et retourne une liste de stations"""
        logger.info("Analyse du fichier XML...")
        
        try:
            root = ET.fromstring(xml_content)
            logger.debug(f"XML parsé avec succès. Élément racine: {root.tag}")
        except ET.ParseError as e:
            logger.error(f"Erreur de parsing XML: {e}")
            logger.debug(f"Aperçu du contenu: {xml_content[:500]}")
            raise Exception(f"Erreur de parsing XML: {e}")
        
        stations = []
        pdv_elements = root.findall('pdv')
        logger.info(f"{len(pdv_elements)} stations trouvées dans le XML")
        
        for i, pdv in enumerate(pdv_elements):
            if i > 0 and i % 1000 == 0:
                logger.debug(f"Traitement... {i}/{len(pdv_elements)} ({i*100//len(pdv_elements)}%)")
            
            try:
                station = self._parse_station(pdv)
                if station and station.ville:  # Ajouter seulement si elle a une ville
                    stations.append(station)
            except Exception as e:
                logger.warning(f"Erreur lors du parsing de la station {pdv.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"{len(stations)} stations parsées avec succès!")
        return stations
    
    def _parse_station(self, pdv) -> Optional[Station]:
        """Parse un élément station XML"""
        station = Station(
            id=pdv.get('id', ''),
            latitude=pdv.get('latitude', ''),
            longitude=pdv.get('longitude', ''),
            cp=pdv.get('cp', ''),
            pop=pdv.get('pop', '')
        )
        
        # Adresse et ville
        adresse_elem = pdv.find('adresse')
        if adresse_elem is not None:
            station.adresse = adresse_elem.text or ''
        
        ville_elem = pdv.find('ville')
        if ville_elem is not None:
            station.ville = ville_elem.text or ''
        
        # Marque
        station.marque = self.brand_extractor.extract_brand(station.adresse)
        
        # Prix
        self._parse_prix(pdv, station)
        
        # Services
        self._parse_services(pdv, station)
        
        # Horaires
        self._parse_horaires(pdv, station)
        
        return station
    
    def _parse_prix(self, pdv, station: Station) -> None:
        """Parse les prix d'une station"""
        for prix_elem in pdv.findall('prix'):
            nom = prix_elem.get('nom', '')
            valeur = prix_elem.get('valeur', '')
            maj = prix_elem.get('maj', '')
            
            if nom and valeur:
                try:
                    prix = Prix(
                        nom=nom,
                        valeur=float(valeur),
                        maj=maj
                    )
                    station.prix[nom] = prix
                except ValueError:
                    continue
    
    def _parse_services(self, pdv, station: Station) -> None:
        """Parse les services d'une station"""
        services_elem = pdv.find('services')
        if services_elem is not None:
            for service in services_elem.findall('service'):
                if service.text:
                    station.services.append(service.text.strip())
    
    def _parse_horaires(self, pdv, station: Station) -> None:
        """Parse les horaires d'une station"""
        horaires_elem = pdv.find('horaires')
        if horaires_elem is not None:
            station.automate_24h = horaires_elem.get('automate-24-24') == '1'
            
            for jour in horaires_elem.findall('jour'):
                jour_nom = jour.get('nom', '')
                ferme = jour.get('ferme', '') == '1'
                
                if jour_nom:
                    jour_horaires = JourHoraires(ferme=ferme)
                    
                    # Horaires détaillés
                    for horaire in jour.findall('horaire'):
                        ouverture = horaire.get('ouverture', '')
                        fermeture = horaire.get('fermeture', '')
                        if ouverture and fermeture:
                            jour_horaires.horaires_detail.append(
                                Horaire(ouverture=ouverture, fermeture=fermeture)
                            )
                    
                    station.horaires[jour_nom] = jour_horaires


class DataService:
    """Service principal de gestion des données"""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.downloader = DataDownloader(config)
        self.parser = DataParser()
        
        self.stations_data: List[Station] = []
        self.data_loaded = False
        self.last_update: Optional[datetime] = None
        self._lock = threading.RLock()
    
    def load_data(self) -> bool:
        """Charge les données depuis l'API"""
        try:
            # Télécharger les données
            zip_data = self.downloader.download_data()
            
            # Extraire le XML
            xml_content = self.downloader.extract_xml(zip_data)
            
            # Parser les données
            stations = self.parser.parse_xml(xml_content)
            
            # Mettre à jour les données de manière thread-safe
            with self._lock:
                self.stations_data = stations
                self.data_loaded = True
                self.last_update = datetime.now()
            
            logger.info(f"Données chargées: {len(stations)} stations")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            with self._lock:
                self.data_loaded = False
            return False
    
    def get_stations(self) -> List[Station]:
        """Retourne la liste des stations (thread-safe)"""
        with self._lock:
            return self.stations_data.copy()
    
    def is_data_loaded(self) -> bool:
        """Vérifie si les données sont chargées"""
        with self._lock:
            return self.data_loaded
    
    def get_last_update(self) -> Optional[datetime]:
        """Retourne la date de dernière mise à jour"""
        with self._lock:
            return self.last_update
    
    def start_auto_refresh(self) -> None:
        """Démarre l'actualisation automatique des données"""
        def refresh_worker():
            while True:
                interval_seconds = int(self.config.DATA_REFRESH_INTERVAL.total_seconds())
                time.sleep(interval_seconds)
                
                if self.is_data_loaded():  # Ne lancer qu'if les données précédentes sont chargées
                    logger.info("Actualisation automatique des données...")
                    self.load_data()
        
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
        logger.info(f"Actualisation automatique programmée toutes les {self.config.DATA_REFRESH_INTERVAL}")


# Instance globale du service
data_service = DataService()