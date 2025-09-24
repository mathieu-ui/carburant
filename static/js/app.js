/* JavaScript pour l'application Prix Carburants */

class CarburantApp {
    constructor() {
        this.stationsData = [];
        this.filteredStations = [];
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeSearchInput();
    }
    
    bindEvents() {
        // Événement de recherche
        const searchBtn = document.getElementById('rechercherBtn');
        const searchInput = document.getElementById('villeInput');
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.rechercherStations());
        }
        
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.rechercherStations();
                }
            });
        }
        
        // Événements des filtres
        this.bindFilterEvents();
        
        // Événement de toggle recherche avancée
        const advancedToggle = document.querySelector('.advanced-toggle');
        if (advancedToggle) {
            advancedToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleAdvancedSearch();
            });
        }
    }
    
    bindFilterEvents() {
        const filterSelects = ['triSelect', 'typeStationSelect', 'horairesSelect'];
        
        filterSelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.addEventListener('change', () => this.appliquerFiltres());
            }
        });
        
        // Événements des checkboxes carburants
        const fuelCheckboxes = document.querySelectorAll('.fuel-checkbox input[type="checkbox"]');
        fuelCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.appliquerFiltres());
        });
        
        // Bouton réinitialiser
        const resetBtn = document.getElementById('reinitialiserBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.reinitialiserFiltres());
        }
    }
    
    initializeSearchInput() {
        const searchInput = document.getElementById('villeInput');
        if (searchInput) {
            // Optionnel: ajouter l'autocomplétion plus tard
            searchInput.setAttribute('placeholder', 'Entrez le nom d\'une ville...');
        }
    }
    
    toggleAdvancedSearch() {
        const advanced = document.getElementById('advancedSearch');
        const toggle = document.querySelector('.advanced-toggle');
        
        if (!advanced || !toggle) return;
        
        const isVisible = advanced.style.display !== 'none';
        advanced.style.display = isVisible ? 'none' : 'block';
        
        toggle.innerHTML = isVisible ? 
            '<i class="fas fa-cog"></i> Recherche avancée' : 
            '<i class="fas fa-cog"></i> Masquer la recherche avancée';
    }
    
    async rechercherStations() {
        const ville = document.getElementById('villeInput').value.trim();
        if (!ville) {
            this.showAlert('Veuillez saisir le nom d\'une ville', 'warning');
            return;
        }
        
        if (this.isLoading) return;
        
        this.showLoading();
        this.isLoading = true;
        
        try {
            const response = await fetch(`/api/search?ville=${encodeURIComponent(ville)}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Erreur lors de la recherche');
            }
            
            this.stationsData = data.stations || [];
            this.filteredStations = [...this.stationsData];
            
            this.appliquerFiltres();
            
        } catch (error) {
            console.error('Erreur de recherche:', error);
            this.showError(`Erreur lors de la recherche: ${error.message}`);
            
        } finally {
            this.isLoading = false;
        }
    }
    
    showLoading() {
        const resultatsDiv = document.getElementById('resultats');
        if (resultatsDiv) {
            resultatsDiv.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner"></i>
                    <p>Recherche en cours...</p>
                </div>
            `;
        }
    }
    
    showError(message) {
        const resultatsDiv = document.getElementById('resultats');
        if (resultatsDiv) {
            resultatsDiv.innerHTML = `
                <div class="error">
                    <i class="fas fa-exclamation-triangle"></i>
                    ${message}
                </div>
            `;
        }
    }
    
    showAlert(message, type = 'info') {
        // Créer une alerte Bootstrap ou une notification simple
        alert(message); // Version simple, peut être améliorée
    }
    
    afficherResultats(stations) {
        const resultatsDiv = document.getElementById('resultats');
        if (!resultatsDiv) return;
        
        if (stations.length === 0) {
            resultatsDiv.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>Aucune station trouvée pour cette recherche.</p>
                </div>
            `;
            return;
        }
        
        const ville = document.getElementById('villeInput').value.trim();
        
        let html = `
            <div class="results-info">
                <i class="fas fa-info-circle"></i>
                <strong>${stations.length}</strong> station${stations.length > 1 ? 's' : ''} trouvée${stations.length > 1 ? 's' : ''} à <strong>${ville}</strong>
            </div>
            
            <div class="legend">
                <h6><i class="fas fa-palette"></i> Légende des prix</h6>
                <div class="legend-item">
                    <div class="legend-color legend-fresh"></div>
                    <span>Données récentes (moins de 7 jours)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-old"></div>
                    <span>Données moyennes (7-30 jours)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-stale"></div>
                    <span>Données anciennes (plus de 30 jours)</span>
                </div>
            </div>
        `;
        
        stations.forEach(station => {
            html += this.creerCarteStation(station);
        });
        
        resultatsDiv.innerHTML = html;
    }
    
    creerCarteStation(station) {
        const nomStation = this.formatNomStation(station.marque, station.adresse);
        const stationId = `station_${station.id || Math.random().toString(36).substr(2, 9)}`;
        
        let prixHtml = '';
        if (station.prix && station.prix.length > 0) {
            prixHtml = '<div class="prix-grid">';
            station.prix.forEach(prix => {
                const ageClass = this.getDataAge(prix.maj);
                prixHtml += `
                    <div class="prix-card ${ageClass}">
                        <div class="prix-type">${prix.nom}</div>
                        <div class="prix-value">${prix.valeur.toFixed(3)}</div>
                        <div class="text-muted" style="font-size: 0.7rem;">
                            Maj: ${prix.maj}
                        </div>
                    </div>
                `;
            });
            prixHtml += '</div>';
        } else {
            prixHtml = '<p class="text-muted">Aucun prix disponible</p>';
        }
        
        let servicesHtml = '';
        if (station.services && station.services.length > 0) {
            servicesHtml = `
                <div class="services">
                    <div class="services-title"><i class="fas fa-tools"></i> Services</div>
                    ${station.services.map(service => `<span class="service-tag">${service}</span>`).join('')}
                </div>
            `;
        }
        
        const horaires = station.horaires || 'Horaires non disponibles';
        
        return `
            <div class="station-card" id="${stationId}">
                <div class="station-header">
                    <h3 class="station-title">
                        <a href="#" class="station-title-link" onclick="carburantApp.openGoogleMaps(${JSON.stringify(station).replace(/"/g, '&quot;')})">
                            ${nomStation}
                            <i class="fas fa-map-marker-alt maps-icon"></i>
                        </a>
                    </h3>
                    <div class="station-subtitle">
                        <i class="fas fa-map-pin"></i>
                        <a href="#" class="address-link" onclick="carburantApp.openGoogleMaps(${JSON.stringify(station).replace(/"/g, '&quot;')})">
                            ${station.adresse}, ${station.cp} ${station.ville}
                        </a>
                        <span class="badge bg-${station.type === 'Autoroute' ? 'primary' : 'secondary'} ms-2">
                            ${station.type}
                        </span>
                    </div>
                </div>
                <div class="station-body">
                    ${prixHtml}
                    ${servicesHtml}
                    <div class="horaires">
                        ${horaires}
                    </div>
                </div>
            </div>
        `;
    }
    
    appliquerFiltres() {
        if (this.stationsData.length === 0) return;
        
        let stations = [...this.stationsData];
        
        // Filtrer par type de station
        const typeStation = document.getElementById('typeStationSelect')?.value || '';
        if (typeStation) {
            if (typeStation === 'autoroute') {
                stations = stations.filter(s => s.type === 'Autoroute');
            } else if (typeStation === 'route') {
                stations = stations.filter(s => s.type === 'Route');
            }
        }
        
        // Filtrer par horaires
        const horaires = document.getElementById('horairesSelect')?.value || '';
        if (horaires === '24h') {
            stations = stations.filter(s => s.automate_24h);
        } else if (horaires === 'ouvert') {
            // Simplification: considérer comme ouvert si pas explicitement fermé
            stations = stations.filter(s => s.horaires !== 'Horaires non disponibles' || s.automate_24h);
        }
        
        // Filtrer par carburants
        const selectedFuels = [];
        document.querySelectorAll('.fuel-checkbox input[type="checkbox"]:checked').forEach(checkbox => {
            selectedFuels.push(checkbox.value);
        });
        
        if (selectedFuels.length > 0) {
            stations = stations.filter(station => {
                return selectedFuels.some(fuel => 
                    station.prix.some(prix => prix.nom === fuel)
                );
            });
        }
        
        // Appliquer le tri
        const tri = document.getElementById('triSelect')?.value || 'date-maj';
        this.trierStations(stations, tri);
        
        this.filteredStations = stations;
        this.afficherResultats(stations);
    }
    
    trierStations(stations, tri) {
        switch (tri) {
            case 'date-maj':
            case '':
                stations.sort((a, b) => {
                    const dateA = this.getLatestUpdateTimestamp(a);
                    const dateB = this.getLatestUpdateTimestamp(b);
                    return dateB - dateA; // Plus récent en premier
                });
                break;
                
            case 'prix-croissant':
                stations.sort((a, b) => this.getPrixMoyen(a) - this.getPrixMoyen(b));
                break;
                
            case 'prix-decroissant':
                stations.sort((a, b) => this.getPrixMoyen(b) - this.getPrixMoyen(a));
                break;
                
            case 'ville-az':
                stations.sort((a, b) => (a.ville || '').localeCompare(b.ville || ''));
                break;
                
            case 'marque-az':
                stations.sort((a, b) => (a.marque || '').localeCompare(b.marque || ''));
                break;
        }
    }
    
    getLatestUpdateTimestamp(station) {
        if (!station.prix || station.prix.length === 0) return 0;
        
        let latestTimestamp = 0;
        station.prix.forEach(prix => {
            const timestamp = this.parseDisplayDate(prix.maj);
            if (timestamp > latestTimestamp) {
                latestTimestamp = timestamp;
            }
        });
        
        return latestTimestamp;
    }
    
    parseDisplayDate(dateStr) {
        if (!dateStr || dateStr === "Non renseigné") return 0;
        
        try {
            const match = dateStr.match(/(\d{2})\/(\d{2})\/(\d{4}) à (\d{2}):(\d{2})/);
            if (!match) return 0;
            
            const [, day, month, year, hour, minute] = match;
            const date = new Date(year, month - 1, day, hour, minute);
            return date.getTime();
        } catch (e) {
            return 0;
        }
    }
    
    getPrixMoyen(station) {
        if (!station.prix || station.prix.length === 0) return Infinity;
        const total = station.prix.reduce((sum, prix) => sum + parseFloat(prix.valeur || 0), 0);
        return total / station.prix.length;
    }
    
    getDataAge(dateString) {
        if (!dateString || dateString === "Non renseigné") return 'stale';
        
        try {
            const match = dateString.match(/(\d{2})\/(\d{2})\/(\d{4}) à (\d{2}):(\d{2})/);
            if (!match) return 'stale';
            
            const [, day, month, year, hour, minute] = match;
            const updateDate = new Date(year, month - 1, day, hour, minute);
            const now = new Date();
            const diffDays = (now - updateDate) / (1000 * 60 * 60 * 24);
            
            if (diffDays <= 7) return 'fresh';
            if (diffDays <= 30) return 'old';
            return 'stale';
        } catch (e) {
            return 'stale';
        }
    }
    
    formatNomStation(marque, adresse) {
        if (!marque || marque === 'Station-service') {
            if (adresse) {
                const words = adresse.split(' ');
                return words.length > 0 ? words[0] : 'Station-service';
            }
            return 'Station-service';
        }
        
        if (marque.includes(' ')) {
            return marque.split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                .join(' ');
        }
        
        return marque.charAt(0).toUpperCase() + marque.slice(1).toLowerCase();
    }
    
    generateGoogleMapsUrl(station) {
        const marque = station.marque || 'Station-service';
        const adresse = station.adresse || '';
        const ville = station.ville || '';
        const cp = station.cp || '';
        
        const adresseComplete = `${adresse}, ${cp} ${ville}, France`.replace(/,\s*,/g, ',').trim();
        
        let searchQuery = '';
        
        // Si on a des coordonnées, les utiliser
        if (station.latitude && station.longitude) {
            try {
                const lat = parseFloat(station.latitude) / 100000;
                const lon = parseFloat(station.longitude) / 100000;
                
                if (!isNaN(lat) && !isNaN(lon) && lat !== 0 && lon !== 0) {
                    return `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
                }
            } catch (e) {
                console.warn('Erreur de conversion des coordonnées:', e);
            }
        }
        
        // Fallback : recherche textuelle
        if (marque && marque !== 'Station-service' && marque.trim() !== '') {
            searchQuery = `${marque} ${adresseComplete}`;
        } else {
            searchQuery = `Station-service ${adresseComplete}`;
        }
        
        const encodedQuery = encodeURIComponent(searchQuery);
        return `https://www.google.com/maps/search/${encodedQuery}`;
    }
    
    openGoogleMaps(station) {
        const url = this.generateGoogleMapsUrl(station);
        console.log('Opening Google Maps with URL:', url);
        console.log('Station data:', station);
        
        const newWindow = window.open(url, '_blank');
        
        if (!newWindow) {
            this.showAlert(
                'Impossible d\'ouvrir Google Maps. Veuillez autoriser les popups ou copier l\'URL : ' + url,
                'warning'
            );
        }
    }
    
    reinitialiserFiltres() {
        // Réinitialiser les selects
        const selects = ['triSelect', 'typeStationSelect', 'horairesSelect'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.value = selectId === 'triSelect' ? 'date-maj' : '';
            }
        });
        
        // Décocher toutes les cases carburants
        document.querySelectorAll('.fuel-checkbox input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Réappliquer les filtres
        this.appliquerFiltres();
    }
}

// Initialiser l'application quand le DOM est chargé
let carburantApp;
document.addEventListener('DOMContentLoaded', function() {
    carburantApp = new CarburantApp();
});

// Fonctions globales pour compatibilité avec l'HTML existant (si nécessaire)
function rechercherStations() {
    if (carburantApp) {
        carburantApp.rechercherStations();
    }
}

function toggleAdvancedSearch() {
    if (carburantApp) {
        carburantApp.toggleAdvancedSearch();
    }
}

function appliquerFiltres() {
    if (carburantApp) {
        carburantApp.appliquerFiltres();
    }
}

function reinitialiserFiltres() {
    if (carburantApp) {
        carburantApp.reinitialiserFiltres();
    }
}

function openGoogleMaps(station) {
    if (carburantApp) {
        carburantApp.openGoogleMaps(station);
    }
}