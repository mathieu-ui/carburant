#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles de données pour l'application Prix Carburants
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Prix:
    """Modèle pour un prix de carburant"""
    nom: str
    valeur: float
    maj: str
    maj_formatted: str = field(default="")
    
    def __post_init__(self):
        if not self.maj_formatted and self.maj:
            self.maj_formatted = self._format_date(self.maj)
    
    @staticmethod
    def _format_date(date_str: str) -> str:
        """Formate une date pour l'affichage"""
        if not date_str:
            return "Non renseigné"
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return date.strftime('%d/%m/%Y à %H:%M')
        except ValueError:
            return date_str


@dataclass
class Horaire:
    """Modèle pour les horaires d'une station"""
    ouverture: str
    fermeture: str


@dataclass
class JourHoraires:
    """Modèle pour les horaires d'un jour"""
    ferme: bool = False
    horaires_detail: List[Horaire] = field(default_factory=list)


@dataclass
class Station:
    """Modèle pour une station-service"""
    id: str
    latitude: str
    longitude: str
    cp: str
    pop: str  # R = Route, A = Autoroute
    adresse: str = ""
    ville: str = ""
    marque: str = ""
    automate_24h: bool = False
    prix: Dict[str, Prix] = field(default_factory=dict)
    services: List[str] = field(default_factory=list)
    horaires: Dict[str, JourHoraires] = field(default_factory=dict)
    
    @property
    def type_station(self) -> str:
        """Retourne le type de station"""
        return 'Autoroute' if self.pop == 'A' else 'Route'
    
    @property
    def derniere_maj(self) -> str:
        """Retourne la date de mise à jour la plus récente"""
        if not self.prix:
            return "Non renseigné"
        
        dates = []
        for prix_info in self.prix.values():
            if prix_info.maj:
                try:
                    date = datetime.strptime(prix_info.maj, '%Y-%m-%d %H:%M:%S')
                    dates.append(date)
                except ValueError:
                    continue
        
        if dates:
            latest = max(dates)
            return latest.strftime('%d/%m/%Y à %H:%M')
        
        return "Non renseigné"
    
    @property
    def horaires_text(self) -> str:
        """Retourne les horaires formatés en texte"""
        if self.automate_24h:
            return "Automate 24h/24"
        
        if not self.horaires:
            return "Horaires non disponibles"
        
        jours_ouverts = []
        for jour, info in self.horaires.items():
            if not info.ferme and info.horaires_detail:
                premier_horaire = info.horaires_detail[0]
                jours_ouverts.append(f"{jour}: {premier_horaire.ouverture}-{premier_horaire.fermeture}")
        
        if jours_ouverts:
            horaires_text = "; ".join(jours_ouverts[:3])
            if len(jours_ouverts) > 3:
                horaires_text += "..."
            return horaires_text
        
        return "Horaires non disponibles"
    
    def to_api_dict(self) -> dict:
        """Convertit la station en dictionnaire pour l'API"""
        prix_list = []
        for prix in self.prix.values():
            prix_list.append({
                'nom': prix.nom,
                'valeur': prix.valeur,
                'maj': prix.maj_formatted
            })
        
        return {
            'id': self.id,
            'adresse': self.adresse,
            'ville': self.ville,
            'cp': self.cp,
            'marque': self.marque,
            'type': self.type_station,
            'automate_24h': self.automate_24h,
            'prix': prix_list,
            'services': self.services,
            'horaires': self.horaires_text,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'derniere_maj': self.derniere_maj
        }


@dataclass
class SearchResult:
    """Résultat de recherche"""
    stations: List[Station]
    count: int
    ville: str
    
    def to_api_dict(self) -> dict:
        """Convertit le résultat en dictionnaire pour l'API"""
        return {
            'stations': [station.to_api_dict() for station in self.stations],
            'count': self.count,
            'ville': self.ville
        }