#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de cache pour l'application
"""

import threading
import time
from typing import Any, Optional, Dict
from datetime import datetime, timedelta


class CacheEntry:
    """Entrée de cache avec TTL"""
    
    def __init__(self, data: Any, ttl: timedelta):
        self.data = data
        self.created_at = datetime.now()
        self.expires_at = self.created_at + ttl
    
    @property
    def is_expired(self) -> bool:
        """Vérifie si l'entrée a expiré"""
        return datetime.now() > self.expires_at
    
    @property
    def age(self) -> timedelta:
        """Retourne l'âge de l'entrée"""
        return datetime.now() - self.created_at


class MemoryCache:
    """Cache en mémoire thread-safe avec TTL"""
    
    def __init__(self, default_ttl: timedelta = timedelta(minutes=30)):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self._start_cleanup_thread()
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired:
                del self._cache[key]
                return None
            
            return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """Stocke une valeur dans le cache"""
        ttl = ttl or self.default_ttl
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> bool:
        """Supprime une entrée du cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Vide le cache"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Retourne la taille du cache"""
        with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> dict:
        """Retourne les statistiques du cache"""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired)
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'keys': list(self._cache.keys())
            }
    
    def _cleanup_expired(self) -> int:
        """Nettoie les entrées expirées"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def _start_cleanup_thread(self) -> None:
        """Démarre le thread de nettoyage automatique"""
        def cleanup_worker():
            while True:
                time.sleep(300)  # Nettoyage toutes les 5 minutes
                try:
                    cleaned = self._cleanup_expired()
                    if cleaned > 0:
                        print(f"Cache: {cleaned} entrées expirées supprimées")
                except Exception as e:
                    print(f"Erreur lors du nettoyage du cache: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()


# Instance globale du cache
cache = MemoryCache()