#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de recherche de stations-service
"""

import logging
from typing import List, Callable
from datetime import datetime

from ..models import Station, SearchResult
from ..utils import cache
from .data_service import data_service

logger = logging.getLogger(__name__)


class SearchService:
    """Service de recherche et filtrage des stations"""
    
    def __init__(self):
        self.data_service = data_service
    
    def search_by_city(self, ville: str) -> SearchResult:
        """Recherche des stations par ville"""
        if not ville or not ville.strip():
            raise ValueError("Nom de ville requis")
        
        if not self.data_service.is_data_loaded():
            raise RuntimeError("Données non chargées")
        
        # Vérifier le cache
        cache_key = f"search_city_{ville.lower().strip()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Résultat trouvé en cache pour '{ville}'")
            return cached_result
        
        # Recherche des stations
        ville_lower = ville.lower().strip()
        stations = self.data_service.get_stations()
        results = []
        
        for station in stations:
            if ville_lower in station.ville.lower():
                results.append(station)
        
        # Trier par date de mise à jour (plus récent en premier)
        results.sort(key=self._get_sort_key_by_date)
        
        # Créer le résultat
        search_result = SearchResult(
            stations=results,
            count=len(results),
            ville=ville
        )
        
        # Mettre en cache
        cache.set(cache_key, search_result)
        
        logger.info(f"Recherche '{ville}': {len(results)} stations trouvées")
        return search_result
    
    def filter_stations(self, 
                       stations: List[Station],
                       type_station: str = "",
                       horaires: str = "",
                       carburants: List[str] = None,
                       tri: str = "date-maj") -> List[Station]:
        """Filtre et trie une liste de stations"""
        
        filtered = stations.copy()
        carburants = carburants or []
        
        # Filtrer par type de station
        if type_station:
            if type_station == "autoroute":
                filtered = [s for s in filtered if s.pop == 'A']
            elif type_station == "route":
                filtered = [s for s in filtered if s.pop == 'R']
        
        # Filtrer par horaires
        if horaires == "24h":
            filtered = [s for s in filtered if s.automate_24h]
        elif horaires == "ouvert":
            # Simplification: considérer comme ouvert si pas fermé explicitement
            # Une implémentation plus complexe vérifierait l'heure actuelle
            filtered = [s for s in filtered if s.horaires or s.automate_24h]
        
        # Filtrer par carburants
        if carburants:
            filtered = [
                s for s in filtered 
                if any(carburant in s.prix for carburant in carburants)
            ]
        
        # Appliquer le tri
        if tri == "date-maj" or tri == "":
            filtered.sort(key=self._get_sort_key_by_date)
        elif tri == "prix-croissant":
            filtered.sort(key=self._get_average_price)
        elif tri == "prix-decroissant":
            filtered.sort(key=self._get_average_price, reverse=True)
        elif tri == "ville-az":
            filtered.sort(key=lambda s: s.ville.lower())
        elif tri == "marque-az":
            filtered.sort(key=lambda s: s.marque.lower())
        
        return filtered
    
    def _get_sort_key_by_date(self, station: Station) -> tuple:
        """Clé de tri par date de mise à jour"""
        if not station.prix:
            return (float('inf'), station.ville, station.adresse)
        
        dates = []
        for prix in station.prix.values():
            if prix.maj:
                try:
                    date = datetime.strptime(prix.maj, '%Y-%m-%d %H:%M:%S')
                    dates.append(date)
                except ValueError:
                    continue
        
        if dates:
            latest = max(dates)
            # Timestamp négatif pour avoir les plus récents en premier
            return (-latest.timestamp(), station.ville, station.adresse)
        
        return (float('inf'), station.ville, station.adresse)
    
    def _get_average_price(self, station: Station) -> float:
        """Calcule le prix moyen d'une station"""
        if not station.prix:
            return float('inf')
        
        prices = [prix.valeur for prix in station.prix.values()]
        return sum(prices) / len(prices)
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Retourne des suggestions de villes basées sur la requête partielle"""
        if not query or len(query) < 2:
            return []
        
        # Vérifier le cache
        cache_key = f"suggestions_{query.lower()}"
        cached_suggestions = cache.get(cache_key)
        if cached_suggestions:
            return cached_suggestions
        
        stations = self.data_service.get_stations()
        villes = set()
        query_lower = query.lower()
        
        for station in stations:
            if query_lower in station.ville.lower():
                villes.add(station.ville)
                if len(villes) >= limit:
                    break
        
        suggestions = sorted(list(villes))[:limit]
        
        # Mettre en cache les suggestions
        cache.set(cache_key, suggestions)
        
        return suggestions


# Instance globale du service
search_service = SearchService()