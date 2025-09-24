#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaires pour l'extraction et le formatage des données
"""

import re
from typing import Optional
from datetime import datetime


class BrandExtractor:
    """Extracteur de marques de stations-service"""
    
    MARQUES_PRINCIPALES = {
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
    
    @classmethod
    def extract_brand(cls, adresse: str) -> str:
        """Extrait la marque depuis l'adresse"""
        if not adresse:
            return 'Station-service'
        
        adresse_upper = adresse.upper()
        
        # Recherche de marque dans l'adresse
        for marque_affichee, variantes in cls.MARQUES_PRINCIPALES.items():
            for variante in variantes:
                if variante in adresse_upper:
                    return marque_affichee
        
        # Si aucune marque trouvée, essayer d'extraire un nom depuis l'adresse
        nom_station = cls._extract_from_patterns(adresse)
        if nom_station:
            return nom_station
        
        # Dernière tentative : prendre le premier mot s'il semble être un nom
        return cls._extract_first_word(adresse)
    
    @classmethod
    def _extract_from_patterns(cls, adresse: str) -> Optional[str]:
        """Extrait un nom basé sur des patterns courants"""
        mots = adresse.split()
        for i, mot in enumerate(mots):
            mot_upper = mot.upper()
            if any(pattern in mot_upper for pattern in ['STATION', 'GARAGE', 'RELAIS', 'SHOP', 'MARKET']):
                # Prendre le mot précédent s'il existe
                if i > 0 and len(mots[i-1]) > 2:
                    return mots[i-1].title()
                else:
                    return mot.title()
        return None
    
    @classmethod
    def _extract_first_word(cls, adresse: str) -> str:
        """Extrait le premier mot s'il semble être un nom de marque"""
        if not adresse:
            return 'Station-service'
        
        premier_mot = adresse.split()[0] if adresse.split() else ''
        if (len(premier_mot) > 3 and 
            premier_mot.upper() not in ['ROUTE', 'RUE', 'AVENUE', 'PLACE', 'BOULEVARD']):
            return premier_mot.title()
        
        return 'Station-service'


class DateFormatter:
    """Formateur de dates"""
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """Formate une date pour l'affichage"""
        if not date_str:
            return "Non renseigné"
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return date.strftime('%d/%m/%Y à %H:%M')
        except ValueError:
            return date_str
    
    @staticmethod
    def parse_display_date(date_str: str) -> Optional[datetime]:
        """Parse une date au format d'affichage"""
        if not date_str or date_str == "Non renseigné":
            return None
        
        try:
            # Parse la date depuis le format "09/09/2025 à 19:43"
            match = re.match(r'(\d{2})/(\d{2})/(\d{4}) à (\d{2}):(\d{2})', date_str)
            if match:
                day, month, year, hour, minute = match.groups()
                return datetime(int(year), int(month), int(day), int(hour), int(minute))
        except (ValueError, AttributeError):
            pass
        
        return None


class CoordinateConverter:
    """Convertisseur de coordonnées"""
    
    @staticmethod
    def convert_coordinates(lat_str: str, lon_str: str) -> tuple[Optional[float], Optional[float]]:
        """Convertit les coordonnées du format gouvernemental au format décimal"""
        try:
            # Les coordonnées sont déjà en format décimal dans l'API
            lat = float(lat_str) / 100000 if lat_str else None
            lon = float(lon_str) / 100000 if lon_str else None
            return lat, lon
        except (ValueError, TypeError):
            return None, None


class AddressFormatter:
    """Formateur d'adresses"""
    
    @staticmethod
    def format_full_address(adresse: str, cp: str, ville: str) -> str:
        """Formate une adresse complète"""
        parts = [part.strip() for part in [adresse, cp, ville] if part and part.strip()]
        return ", ".join(parts) + ", France" if parts else "Adresse non disponible"
    
    @staticmethod
    def clean_address(adresse: str) -> str:
        """Nettoie une adresse en supprimant les doublons et espaces"""
        if not adresse:
            return ""
        
        # Supprimer les espaces multiples et nettoyer
        cleaned = re.sub(r'\s+', ' ', adresse.strip())
        # Supprimer les virgules multiples
        cleaned = re.sub(r',\s*,', ',', cleaned)
        
        return cleaned