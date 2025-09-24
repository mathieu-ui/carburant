#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour l'application Prix Carburants
"""

import logging
from flask import Blueprint, request, jsonify
from typing import List

from ..services import search_service
from ..utils import cache

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/search')
def search_stations():
    """Recherche des stations par ville"""
    try:
        ville = request.args.get('ville', '').strip()
        
        if not ville:
            return jsonify({'error': 'Nom de ville requis'}), 400
        
        # Recherche de base
        result = search_service.search_by_city(ville)
        
        # Paramètres de filtrage optionnels
        type_station = request.args.get('type', '').strip()
        horaires = request.args.get('horaires', '').strip()
        carburants_param = request.args.get('carburants', '').strip()
        tri = request.args.get('tri', 'date-maj').strip()
        
        # Parser les carburants (format: "carburant1,carburant2")
        carburants = []
        if carburants_param:
            carburants = [c.strip() for c in carburants_param.split(',') if c.strip()]
        
        # Appliquer les filtres si nécessaire
        stations = result.stations
        if type_station or horaires or carburants or tri != 'date-maj':
            stations = search_service.filter_stations(
                stations, type_station, horaires, carburants, tri
            )
        
        # Retourner les résultats
        return jsonify({
            'stations': [station.to_api_dict() for station in stations],
            'count': len(stations),
            'ville': ville,
            'filters_applied': {
                'type_station': type_station,
                'horaires': horaires,
                'carburants': carburants,
                'tri': tri
            }
        })
        
    except ValueError as e:
        logger.warning(f"Erreur de validation: {e}")
        return jsonify({'error': str(e)}), 400
    
    except RuntimeError as e:
        logger.error(f"Erreur du service: {e}")
        return jsonify({'error': 'Service temporairement indisponible'}), 503
    
    except Exception as e:
        logger.error(f"Erreur inattendue dans la recherche: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@api_bp.route('/suggestions')
def get_suggestions():
    """Obtenir des suggestions de villes"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query or len(query) < 2:
            return jsonify({'suggestions': []})
        
        if limit < 1 or limit > 50:
            limit = 10
        
        suggestions = search_service.get_search_suggestions(query, limit)
        
        return jsonify({
            'suggestions': suggestions,
            'query': query,
            'count': len(suggestions)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des suggestions: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@api_bp.route('/status')
def get_status():
    """Obtenir le statut de l'application"""
    try:
        from ..services import data_service
        
        is_loaded = data_service.is_data_loaded()
        last_update = data_service.get_last_update()
        stations_count = len(data_service.get_stations()) if is_loaded else 0
        
        # Statistiques du cache
        cache_stats = cache.get_stats()
        
        return jsonify({
            'status': 'healthy' if is_loaded else 'loading',
            'data_loaded': is_loaded,
            'stations_count': stations_count,
            'last_update': last_update.isoformat() if last_update else None,
            'cache_stats': cache_stats
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@api_bp.route('/station/<station_id>')
def get_station_detail(station_id: str):
    """Obtenir le détail d'une station spécifique"""
    try:
        from ..services import data_service
        stations = data_service.get_stations()
        
        # Chercher la station par ID
        station = next((s for s in stations if s.id == station_id), None)
        
        if not station:
            return jsonify({'error': 'Station non trouvée'}), 404
        
        return jsonify({
            'station': station.to_api_dict()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la station {station_id}: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@api_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Vider le cache (endpoint d'administration)"""
    try:
        cache.clear()
        return jsonify({
            'message': 'Cache vidé avec succès',
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du vidage du cache: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@api_bp.route('/reload', methods=['POST']) 
def reload_data():
    """Recharger les données (endpoint d'administration)"""
    try:
        from ..services import data_service
        
        success = data_service.load_data()
        
        if success:
            # Vider le cache après rechargement
            cache.clear()
            return jsonify({
                'message': 'Données rechargées avec succès',
                'status': 'success',
                'stations_count': len(data_service.get_stations())
            })
        else:
            return jsonify({
                'message': 'Échec du rechargement des données',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur lors du rechargement des données: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


# Gestionnaire d'erreur pour toutes les routes API
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'Endpoint non trouvé'}), 404


@api_bp.errorhandler(405)
def api_method_not_allowed(error):
    return jsonify({'error': 'Méthode non autorisée'}), 405


@api_bp.errorhandler(500)
def api_internal_error(error):
    logger.error(f"Erreur interne de l'API: {error}")
    return jsonify({'error': 'Erreur interne du serveur'}), 500