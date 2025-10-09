import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import random
import warnings
from functools import lru_cache
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Impôts - DROM-COM",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(45deg, #0055A4, #28a745, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .live-badge {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .section-header {
        color: #28a745;
        border-bottom: 2px solid #0055A4;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .category-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid #28a745;
        background-color: #f8f9fa;
    }
    .revenue-change {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .positive { background-color: #d4edda; border-left: 4px solid #28a745; color: #155724; }
    .negative { background-color: #f8d7da; border-left: 4px solid #dc3545; color: #721c24; }
    .neutral { background-color: #e2e3e5; border-left: 4px solid #6c757d; color: #383d41; }
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .territory-flag {
        padding: 0.5rem 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
        color: white;
    }
    .reunion-flag { background: linear-gradient(90deg, #0055A4 33%, #EF4135 33%, #EF4135 66%, #FFFFFF 66%); }
    .guadeloupe-flag { background: linear-gradient(90deg, #ED2939 50%, #002395 50%); }
    .martinique-flag { background: linear-gradient(90deg, #009739 33%, #002395 33%, #002395 66%, #FCD116 66%); }
    .guyane-flag { background: linear-gradient(90deg, #009739 50%, #FCD116 50%); }
    .mayotte-flag { background: linear-gradient(90deg, #FFFFFF 25%, #ED2939 25%, #ED2939 50%, #002395 50%, #002395 75%, #FCD116 75%); }
    .spierre-flag { background: linear-gradient(90deg, #002395 33%, #FFFFFF 33%, #FFFFFF 66%, #ED2939 66%); }
    .stbarth-flag { background: linear-gradient(90deg, #FFFFFF 50%, #FCD116 50%); }
    .stmartin-flag { background: linear-gradient(90deg, #ED2939 50%, #002395 50%); }
    .wallis-flag { background: linear-gradient(90deg, #ED2939 33%, #002395 33%, #002395 66%, #FCD116 66%); }
    .polynesie-flag { background: linear-gradient(90deg, #ED2939 25%, #FFFFFF 25%, #FFFFFF 50%, #FCD116 50%, #FCD116 75%, #002395 75%); }
    .caledonie-flag { background: linear-gradient(90deg, #002395 33%, #FCD116 33%, #FCD116 66%, #ED2939 66%); }
    .territory-selector {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #28a745;
        margin-bottom: 1rem;
    }
    .tax-type-indicator {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .direct-tax { background-color: #007bff; color: white; }
    .indirect-tax { background-color: #6f42c1; color: white; }
    .local-tax { background-color: #fd7e14; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialisation de l'état de session
if 'territories_data' not in st.session_state:
    st.session_state.territories_data = {}
if 'selected_territory' not in st.session_state:
    st.session_state.selected_territory = 'REUNION'
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Fonctions globales avec cache pour éviter les problèmes de hashage
@st.cache_data(ttl=3600)
def get_territories_definitions():
    """Définit les territoires DROM-COM"""
    return {
        'REUNION': {
            'nom_complet': 'La Réunion',
            'type': 'DROM',
            'population': 860000,
            'superficie': 2511,
            'pib': 19.8,
            'drapeau': 'reunion-flag',
            'monnaie': 'EUR',
            'impots_actif': True,
            'recettes_fiscales_total': 2800,
            'recettes_par_habitant': 3256,
            'taux_imposition_moyen': 28.5
        },
        'GUADELOUPE': {
            'nom_complet': 'Guadeloupe',
            'type': 'DROM',
            'population': 384000,
            'superficie': 1628,
            'pib': 9.1,
            'drapeau': 'guadeloupe-flag',
            'monnaie': 'EUR',
            'impots_actif': True,
            'recettes_fiscales_total': 1250,
            'recettes_par_habitant': 3255,
            'taux_imposition_moyen': 27.8
        },
        'MARTINIQUE': {
            'nom_complet': 'Martinique',
            'type': 'DROM',
            'population': 376000,
            'superficie': 1128,
            'pib': 8.9,
            'drapeau': 'martinique-flag',
            'monnaie': 'EUR',
            'impots_actif': True,
            'recettes_fiscales_total': 1220,
            'recettes_par_habitant': 3245,
            'taux_imposition_moyen': 27.5
        },
        'GUYANE': {
            'nom_complet': 'Guyane',
            'type': 'DROM',
            'population': 290000,
            'superficie': 83534,
            'pib': 4.8,
            'drapeau': 'guyane-flag',
            'monnaie': 'EUR',
            'impots_actif': True,
            'recettes_fiscales_total': 680,
            'recettes_par_habitant': 2345,
            'taux_imposition_moyen': 24.2
        },
        'MAYOTTE': {
            'nom_complet': 'Mayotte',
            'type': 'DROM',
            'population': 270000,
            'superficie': 374,
            'pib': 2.4,
            'drapeau': 'mayotte-flag',
            'monnaie': 'EUR',
            'impots_actif': True,
            'recettes_fiscales_total': 420,
            'recettes_par_habitant': 1556,
            'taux_imposition_moyen': 22.1
        },
        'STPIERRE': {
            'nom_complet': 'Saint-Pierre-et-Miquelon',
            'type': 'COM',
            'population': 6000,
            'superficie': 242,
            'pib': 0.2,
            'drapeau': 'spierre-flag',
            'monnaie': 'EUR',
            'impots_actif': True,
            'recettes_fiscales_total': 45,
            'recettes_par_habitant': 7500,
            'taux_imposition_moyen': 32.5
        },
        'STBARTH': {
            'nom_complet': 'Saint-Barthélemy',
            'type': 'COM',
            'population': 10000,
            'superficie': 21,
            'pib': 0.6,
            'drapeau': 'stbarth-flag',
            'monnaie': 'EUR',
            'impots_actif': True,
            'recettes_fiscales_total': 85,
            'recettes_par_habitant': 8500,
            'taux_imposition_moyen': 35.2
        },
        'STMARTIN': {
            'nom_complet': 'Saint-Martin',
            'type': 'COM',
            'population': 32000,
            'superficie': 54,
            'pib': 0.9,
            'drapeau': 'stmartin-flag',
            'monnaie': 'EUR',
            'impots_actif': True,
            'recettes_fiscales_total': 120,
            'recettes_par_habitant': 3750,
            'taux_imposition_moyen': 29.8
        },
        'WALLIS': {
            'nom_complet': 'Wallis-et-Futuna',
            'type': 'COM',
            'population': 11500,
            'superficie': 142,
            'pib': 0.2,
            'drapeau': 'wallis-flag',
            'monnaie': 'XPF',
            'impots_actif': True,
            'recettes_fiscales_total': 25,
            'recettes_par_habitant': 2174,
            'taux_imposition_moyen': 26.5
        },
        'POLYNESIE': {
            'nom_complet': 'Polynésie française',
            'type': 'COM',
            'population': 280000,
            'superficie': 4167,
            'pib': 7.2,
            'drapeau': 'polynesie-flag',
            'monnaie': 'XPF',
            'impots_actif': True,
            'recettes_fiscales_total': 980,
            'recettes_par_habitant': 3500,
            'taux_imposition_moyen': 28.9
        },
        'CALEDONIE': {
            'nom_complet': 'Nouvelle-Calédonie',
            'type': 'COM',
            'population': 271000,
            'superficie': 18575,
            'pib': 9.7,
            'drapeau': 'caledonie-flag',
            'monnaie': 'XPF',
            'impots_actif': True,
            'recettes_fiscales_total': 1100,
            'recettes_par_habitant': 4059,
            'taux_imposition_moyen': 30.2
        }
    }

@st.cache_data(ttl=3600)
def get_categories_impots(territory_code):
    """Définit les catégories d'impôts pour un territoire donné"""
    # Facteurs d'ajustement selon le territoire
    territory_factor = {
        'REUNION': 1.0,
        'GUADELOUPE': 0.85,
        'MARTINIQUE': 0.82,
        'GUYANE': 0.65,
        'MAYOTTE': 0.45,
        'STPIERRE': 1.2,
        'STBARTH': 1.5,
        'STMARTIN': 1.1,
        'WALLIS': 0.7,
        'POLYNESIE': 0.8,
        'CALEDONIE': 0.9
    }
    
    factor = territory_factor.get(territory_code, 1.0)
    
    # Catégories de base avec ajustements selon le territoire
    categories_base = {
        'IR': {
            'nom_complet': 'Impôt sur le Revenu',
            'type_impot': 'Direct',
            'sous_categorie': 'Impôt progressif',
            'montant_annuel': 850 * factor,
            'nombre_contribuables': 320000 * factor,
            'couleur': '#28a745',
            'poids_total': 30.2 * factor,
            'evolution_annuelle': 3.2,
            'description': 'Impôt progressif sur les revenus des personnes physiques',
            'taux_moyen': 14.5,
            'plafond': 150000
        },
        'IS': {
            'nom_complet': 'Impôt sur les Sociétés',
            'type_impot': 'Direct',
            'sous_categorie': 'Impôt sur les bénéfices',
            'montant_annuel': 620 * factor,
            'nombre_contribuables': 25000 * factor,
            'couleur': '#20c997',
            'poids_total': 22.8 * factor,
            'evolution_annuelle': 4.8,
            'description': 'Impôt sur les bénéfices des entreprises',
            'taux_moyen': 25.0,
            'plafond': 1000000
        },
        'TVA': {
            'nom_complet': 'Taxe sur la Valeur Ajoutée',
            'type_impot': 'Indirect',
            'sous_categorie': 'Taxe sur la consommation',
            'montant_annuel': 980 * factor,
            'nombre_contribuables': 45000 * factor,
            'couleur': '#fd7e14',
            'poids_total': 35.5 * factor,
            'evolution_annuelle': 2.9,
            'description': 'Taxe sur la consommation de biens et services',
            'taux_moyen': 8.5,
            'plafond': 0
        },
        'TFPB': {
            'nom_complet': 'Taxe Foncière sur le Bâti',
            'type_impot': 'Local',
            'sous_categorie': 'Taxe foncière',
            'montant_annuel': 280 * factor,
            'nombre_contribuables': 280000 * factor,
            'couleur': '#6f42c1',
            'poids_total': 10.3 * factor,
            'evolution_annuelle': 1.5,
            'description': 'Taxe sur les propriétés bâties',
            'taux_moyen': 1.2,
            'plafond': 50000
        },
        'TFNB': {
            'nom_complet': 'Taxe Foncière sur le Non-Bâti',
            'type_impot': 'Local',
            'sous_categorie': 'Taxe foncière',
            'montant_annuel': 45 * factor,
            'nombre_contribuables': 15000 * factor,
            'couleur': '#dc3545',
            'poids_total': 1.7 * factor,
            'evolution_annuelle': 0.8,
            'description': 'Taxe sur les propriétés non bâties',
            'taux_moyen': 0.8,
            'plafond': 20000
        },
        'TH': {
            'nom_complet': 'Taxe d\'Habitation',
            'type_impot': 'Local',
            'sous_categorie': 'Taxe d\'habitation',
            'montant_annuel': 320 * factor,
            'nombre_contribuables': 380000 * factor,
            'couleur': '#ffc107',
            'poids_total': 11.8 * factor,
            'evolution_annuelle': -2.5,
            'description': 'Taxe sur l\'occupation des logements',
            'taux_moyen': 1.5,
            'plafond': 30000
        },
        'DROITS_ENREGISTREMENT': {
            'nom_complet': 'Droits d\'enregistrement',
            'type_impot': 'Indirect',
            'sous_categorie': 'Droits de mutation',
            'montant_annuel': 180 * factor,
            'nombre_contribuables': 12000 * factor,
            'couleur': '#6610f2',
            'poids_total': 6.8 * factor,
            'evolution_annuelle': 3.8,
            'description': 'Droits sur les mutations immobilières et autres actes',
            'taux_moyen': 5.5,
            'plafond': 0
        },
        'TICPE': {
            'nom_complet': 'Taxe Intérieure sur la Consommation des Produits Énergétiques',
            'type_impot': 'Indirect',
            'sous_categorie': 'Taxe sur l\'énergie',
            'montant_annuel': 150 * factor,
            'nombre_contribuables': 5000 * factor,
            'couleur': '#e83e8c',
            'poids_total': 5.5 * factor,
            'evolution_annuelle': 1.2,
            'description': 'Taxe sur les produits pétroliers et énergétiques',
            'taux_moyen': 0.6,
            'plafond': 0
        },
        'ISF': {
            'nom_complet': 'Impôt sur la Fortune Immobilière',
            'type_impot': 'Direct',
            'sous_categorie': 'Impôt sur le patrimoine',
            'montant_annuel': 42 * factor,
            'nombre_contribuables': 2500 * factor,
            'couleur': '#0066CC',
            'poids_total': 1.5 * factor,
            'evolution_annuelle': 2.2,
            'description': 'Impôt sur les grandes fortunes immobilières',
            'taux_moyen': 1.3,
            'plafond': 1300000
        },
        'AUTRES_IMPOSITIONS': {
            'nom_complet': 'Autres impositions et taxes',
            'type_impot': 'Divers',
            'sous_categorie': 'Taxes diverses',
            'montant_annuel': 95 * factor,
            'nombre_contribuables': 80000 * factor,
            'couleur': '#17a2b8',
            'poids_total': 3.5 * factor,
            'evolution_annuelle': 1.5,
            'description': 'Autres taxes et impositions diverses',
            'taux_moyen': 0,
            'plafond': 0
        }
    }
    
    # Ajustements spécifiques selon le territoire
    if territory_code in ['POLYNESIE', 'CALEDONIE', 'WALLIS']:
        categories_base['TAXE_LOCALE'] = {
            'nom_complet': 'Taxe locale spécifique COM',
            'type_impot': 'Local',
            'sous_categorie': 'Taxe spécifique',
            'montant_annuel': 120 * factor,
            'nombre_contribuables': 180000 * factor,
            'couleur': '#8B4513',
            'poids_total': 8.0 * factor,
            'evolution_annuelle': 2.5,
            'description': 'Taxe locale spécifique aux collectivités d\'outre-mer',
            'taux_moyen': 2.0,
            'plafond': 25000
        }
    
    return categories_base

@st.cache_data(ttl=1800)
def generate_historical_data(territory_code, categories):
    """Génère les données historiques optimisées"""
    dates = pd.date_range('2015-01-01', datetime.now(), freq='M')
    data = []
    
    for date in dates:
        # Impact des réformes fiscales
        if date.year == 2018:
            reforme_impact = random.uniform(1.05, 1.15)  # Réforme fiscale
        elif date.year == 2020:
            reforme_impact = random.uniform(0.9, 1.05)   # Impact COVID
        else:
            reforme_impact = random.uniform(1.0, 1.08)
        
        # Variation saisonnière (plus marquée pour les impôts)
        seasonal_impact = random.uniform(0.95, 1.05)
        
        for categorie_code, info in categories.items():
            base_revenu = info['montant_annuel'] / 12  # Mensualisation
            revenu = base_revenu * reforme_impact * seasonal_impact * random.uniform(0.95, 1.05)
            contribuables = info['nombre_contribuables'] * random.uniform(0.98, 1.02)
            
            data.append({
                'date': date,
                'territoire': territory_code,
                'categorie': categorie_code,
                'montant_total_impots': revenu,
                'nombre_contribuables': contribuables,
                'montant_moyen': revenu / contribuables if contribuables > 0 else 0,
                'type_impot': info['type_impot'],
                'evolution_mensuelle': random.uniform(-1.0, 1.0)
            })
    
    return pd.DataFrame(data)

@st.cache_data(ttl=300)
def generate_current_data(territory_code, categories, historical_data):
    """Génère les données courantes optimisées"""
    current_data = []
    
    for categorie_code, info in categories.items():
        # Dernières données historiques
        last_data = historical_data[historical_data['categorie'] == categorie_code].iloc[-1]
        
        # Variation mensuelle simulée
        change_pct = random.uniform(-0.05, 0.05)
        change_abs = last_data['montant_total_impots'] * change_pct
        
        # CORRECTION: S'assurer que le montant mensuel est correctement calculé
        montant_mensuel = max(0.1, last_data['montant_total_impots'] + change_abs)  # Éviter les valeurs négatives ou nulles
        
        current_data.append({
            'territoire': territory_code,
            'categorie': categorie_code,
            'nom_complet': info['nom_complet'],
            'type_impot': info['type_impot'],
            'montant_mensuel': montant_mensuel,
            'variation_pct': change_pct * 100,
            'variation_abs': change_abs,
            'nombre_contribuables': max(1, last_data['nombre_contribuables'] * random.uniform(0.98, 1.02)),  # Éviter les valeurs nulles
            'montant_moyen': info['montant_annuel'] / 12 * random.uniform(0.95, 1.05),
            'poids_total': info['poids_total'],
            'montant_annee_precedente': last_data['montant_total_impots'] * 12 * random.uniform(0.92, 1.08),
            'taux_moyen': info['taux_moyen'],
            'plafond': info['plafond']
        })
    
    return pd.DataFrame(current_data)

@st.cache_data(ttl=600)
def generate_revenu_data(territory_code):
    """Génère les données par tranche de revenu optimisées"""
    revenu_ranges = [
        {'tranche_revenu': '0-10k€', 'nombre_contribuables': 80000, 'montant_moyen_impot': 0, 'taux_effectif': 0},
        {'tranche_revenu': '10-20k€', 'nombre_contribuables': 65000, 'montant_moyen_impot': 450, 'taux_effectif': 3.0},
        {'tranche_revenu': '20-30k€', 'nombre_contribuables': 45000, 'montant_moyen_impot': 1200, 'taux_effectif': 6.0},
        {'tranche_revenu': '30-50k€', 'nombre_contribuables': 30000, 'montant_moyen_impot': 2800, 'taux_effectif': 9.5},
        {'tranche_revenu': '50-70k€', 'nombre_contribuables': 15000, 'montant_moyen_impot': 5500, 'taux_effectif': 12.0},
        {'tranche_revenu': '70-100k€', 'nombre_contribuables': 8000, 'montant_moyen_impot': 9500, 'taux_effectif': 15.5},
        {'tranche_revenu': '100-150k€', 'nombre_contribuables': 4000, 'montant_moyen_impot': 18500, 'taux_effectif': 18.5},
        {'tranche_revenu': '150k€+', 'nombre_contribuables': 1500, 'montant_moyen_impot': 45000, 'taux_effectif': 25.0}
    ]
    
    # Ajustement selon le territoire
    territory_factor = {
        'REUNION': 1.0, 'GUADELOUPE': 0.9, 'MARTINIQUE': 0.88, 'GUYANE': 0.7,
        'MAYOTTE': 0.6, 'STPIERRE': 0.15, 'STBARTH': 0.2, 'STMARTIN': 0.3,
        'WALLIS': 0.12, 'POLYNESIE': 0.8, 'CALEDONIE': 0.85
    }
    
    factor = territory_factor.get(territory_code, 1.0)
    for revenu_range in revenu_ranges:
        revenu_range['nombre_contribuables'] *= factor
        revenu_range['montant_moyen_impot'] *= factor
    
    return pd.DataFrame(revenu_ranges)

@st.cache_data(ttl=3600)
def generate_comparison_data(territories):
    """Génère les données de comparaison entre territoires"""
    comparison_data = []
    
    for territory_code, territory_info in territories.items():
        if not territory_info['impots_actif']:
            continue
            
        categories = get_categories_impots(territory_code)
        total_impots = sum(
            categorie_info['montant_annuel']
            for categorie_info in categories.values()
        )
        
        comparison_data.append({
            'territoire': territory_code,
            'nom_complet': territory_info['nom_complet'],
            'type': territory_info['type'],
            'population': territory_info['population'],
            'superficie': territory_info['superficie'],
            'pib': territory_info['pib'],
            'montant_total_impots': total_impots,
            'recettes_fiscales_total': territory_info['recettes_fiscales_total'],
            'recettes_par_habitant': territory_info['recettes_par_habitant'],
            'taux_imposition_moyen': territory_info['taux_imposition_moyen'],
            'pression_fiscale': (total_impots / territory_info['pib'] / 1e6) * 100,
            'impots_actif': territory_info['impots_actif']
        })
    
    return pd.DataFrame(comparison_data)

class ImpotsDashboard:
    def __init__(self):
        self.territories = get_territories_definitions()
        
    def get_territory_data(self, territory_code):
        """Récupère les données d'un territoire avec cache"""
        if territory_code not in st.session_state.territories_data:
            with st.spinner(f"Chargement des données fiscales pour {self.territories[territory_code]['nom_complet']}..."):
                categories = get_categories_impots(territory_code)
                historical_data = generate_historical_data(territory_code, categories)
                current_data = generate_current_data(territory_code, categories, historical_data)
                revenu_data = generate_revenu_data(territory_code)
                
                st.session_state.territories_data[territory_code] = {
                    'categories': categories,
                    'historical_data': historical_data,
                    'current_data': current_data,
                    'revenu_data': revenu_data,
                    'last_update': datetime.now()
                }
        
        return st.session_state.territories_data[territory_code]
    
    def update_live_data(self, territory_code):
        """Met à jour les données en temps réel"""
        if territory_code in st.session_state.territories_data:
            data = st.session_state.territories_data[territory_code]
            current_data = data['current_data'].copy()
            
            # Mise à jour légère des données
            for idx in current_data.index:
                if random.random() < 0.4:  # 40% de chance de changement
                    variation = random.uniform(-0.02, 0.02)
                    current_data.loc[idx, 'montant_mensuel'] *= (1 + variation)
                    current_data.loc[idx, 'variation_pct'] = variation * 100
                    current_data.loc[idx, 'nombre_contribuables'] *= random.uniform(0.98, 1.02)
            
            st.session_state.territories_data[territory_code]['current_data'] = current_data
            st.session_state.territories_data[territory_code]['last_update'] = datetime.now()
    
    def display_territory_selector(self):
        """Affiche le sélecteur de territoire optimisé"""
        st.markdown('<div class="territory-selector">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            territory_options = {v['nom_complet']: k for k, v in self.territories.items() if v['impots_actif']}
            
            # Utilisation de session_state pour éviter le rerun
            current_name = self.territories[st.session_state.selected_territory]['nom_complet']
            selected_territory_name = st.selectbox(
                "🌍 SÉLECTIONNEZ UN TERRITOIRE:",
                options=list(territory_options.keys()),
                index=list(territory_options.keys()).index(current_name),
                key="territory_selector_main"
            )
            
            new_territory = territory_options[selected_territory_name]
            if new_territory != st.session_state.selected_territory:
                st.session_state.selected_territory = new_territory
                # Précharger les données en arrière-plan
                self.get_territory_data(new_territory)
                st.success(f"✅ Changement vers {selected_territory_name} effectué!")
        
        with col2:
            territory_info = self.territories[st.session_state.selected_territory]
            st.metric("Type", territory_info['type'])
        
        with col3:
            st.metric("Pression fiscale", f"{territory_info['taux_imposition_moyen']}%")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def display_header(self):
        """Affiche l'en-tête du dashboard"""
        territory_info = self.territories[st.session_state.selected_territory]
        
        st.markdown(f'<h1 class="main-header">💰 Dashboard Impôts - {territory_info["nom_complet"]}</h1>', 
                   unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="live-badge">🔴 DONNÉES FISCALES EN TEMPS RÉEL</div>', 
                       unsafe_allow_html=True)
            st.markdown(f"**Surveillance et analyse des recettes fiscales par catégorie**")
        
        # Bannière drapeau du territoire
        st.markdown(f"""
        <div class="territory-flag {territory_info['drapeau']}">
            <strong>{territory_info['nom_complet']} - Système Fiscal</strong><br>
            <small>Type: {territory_info['type']} | Population: {territory_info['population']:,} | PIB: {territory_info['pib']} M€</small>
        </div>
        """, unsafe_allow_html=True)
        
        current_time = datetime.now().strftime('%H:%M:%S')
        st.sidebar.markdown(f"**🕐 Dernière mise à jour: {current_time}**")
    
    def display_key_metrics(self):
        """Affiche les métriques clés des impôts"""
        data = self.get_territory_data(st.session_state.selected_territory)
        current_data = data['current_data']
        
        st.markdown('<h3 class="section-header">📊 INDICATEURS CLÉS FISCAUX</h3>', 
                   unsafe_allow_html=True)
        
        # CORRECTION: S'assurer que les données sont correctement calculées
        # Vérifier si les données existent et ne sont pas vides
        if current_data.empty:
            st.error("Aucune donnée disponible pour ce territoire")
            return
        
        # Calcul des métriques
        montant_total_mensuel = current_data['montant_mensuel'].sum()
        montant_total_annuel = montant_total_mensuel * 12
        variation_moyenne = current_data['variation_pct'].mean()
        contribuables_total = current_data['nombre_contribuables'].sum()
        categories_hausse = len(current_data[current_data['variation_pct'] > 0])
        
        territory_info = self.territories[st.session_state.selected_territory]
        
        # CORRECTION: Calcul correct de l'impôt par habitant
        # Les données sont en millions, donc il faut multiplier par 1e6 pour obtenir les valeurs réelles
        impot_par_habitant = (montant_total_annuel * 1e6) / territory_info['population']
        
        # CORRECTION: Calcul correct de l'impôt moyen par contribuable
        impot_moyen = (montant_total_annuel * 1e6) / contribuables_total if contribuables_total > 0 else 0
        
        # Afficher les informations de débogage
        with st.expander("Informations de débogage"):
            st.write(f"Montant total mensuel: {montant_total_mensuel}")
            st.write(f"Montant total annuel: {montant_total_annuel}")
            st.write(f"Nombre de contribuables: {contribuables_total}")
            st.write(f"Population du territoire: {territory_info['population']}")
            st.write(f"Impôt par habitant calculé: {impot_par_habitant}")
            st.write(f"Impôt moyen par contribuable calculé: {impot_moyen}")
            st.write(current_data.head())
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # CORRECTION: Conversion correcte pour l'affichage
            st.metric(
                "Recettes Mensuelles Total",
                f"{montant_total_mensuel:.1f} M€",  # Correction: pas de division par 1e6 car les données sont déjà en millions
                f"{variation_moyenne:+.2f}%",
                delta_color="normal"
            )
        
        with col2:
            # CORRECTION: Conversion correcte pour l'affichage
            st.metric(
                "Recettes Annuelles Projetées",
                f"{montant_total_annuel:.1f} M€",  # Correction: pas de division par 1e6 car les données sont déjà en millions
                f"{random.uniform(2, 6):.1f}% vs année précédente"
            )
        
        with col3:
            st.metric(
                "Nombre de Contribuables",
                f"{contribuables_total:,.0f}",
                f"{random.randint(-1, 3)}% vs mois dernier"
            )
        
        with col4:
            # CORRECTION: Utiliser la valeur calculée précédemment
            st.metric(
                "Impôt Moyen par Contribuable",
                f"{impot_moyen:.0f} €",
                f"{random.uniform(-2, 4):.1f}% vs période précédente"
            )
        
        # Métriques spécifiques au territoire
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CORRECTION: Utiliser la valeur calculée précédemment
            st.metric(
                "Impôt par Habitant",
                f"{impot_par_habitant:.0f} €",
                f"{random.uniform(-3, 3):.1f}% vs moyenne DROM-COM"
            )
        
        with col2:
            st.metric(
                "Taux de Prélèvement",
                f"{(montant_total_annuel/territory_info['pib'])*100:.1f}%",  # Correction: pas de division par 1e6
                f"{random.uniform(-1, 2):.1f}% vs objectif"
            )
        
        with col3:
            st.metric(
                "Efficacité Fiscale",
                f"{random.uniform(85, 98):.1f}%",
                f"{random.uniform(-2, 3):.1f}% vs objectif"
            )
    
    def create_impots_overview(self):
        """Crée la vue d'ensemble des impôts"""
        data = self.get_territory_data(st.session_state.selected_territory)
        
        st.markdown('<h3 class="section-header">🏛️ VUE D\'ENSEMBLE FISCALE</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["Évolution Recettes", "Répartition Catégories", "Top Impôts", "Analyse Revenus"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Évolution des recettes totales
                evolution_totale = data['historical_data'].groupby('date')['montant_total_impots'].sum().reset_index()
                evolution_totale['montant_mensuel_M'] = evolution_totale['montant_total_impots'] / 1e6
                
                fig = px.line(evolution_totale, 
                             x='date', 
                             y='montant_mensuel_M',
                             title=f'Évolution des Recettes - {self.territories[st.session_state.selected_territory]["nom_complet"]}',
                             color_discrete_sequence=['#28a745'])
                fig.update_layout(yaxis_title="Recettes (Millions €)")
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                # Performance par type d'impôt
                performance_types = data['current_data'].groupby('type_impot').agg({
                    'variation_pct': 'mean',
                    'montant_mensuel': 'sum'
                }).reset_index()
                
                fig = px.bar(performance_types, 
                            x='type_impot', 
                            y='variation_pct',
                            title='Performance Mensuelle par Type d\'Impôt (%)',
                            color='type_impot',
                            color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(yaxis_title="Variation (%)")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(data['current_data'], 
                            values='montant_mensuel', 
                            names='categorie',
                            title='Répartition des Recettes par Catégorie d\'Impôt',
                            color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                fig = px.bar(data['current_data'], 
                            x='categorie', 
                            y='nombre_contribuables',
                            title='Nombre de Contribuables par Catégorie',
                            color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(yaxis_title="Nombre de Contribuables")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                top_categories = data['current_data'].nlargest(10, 'montant_mensuel')
                fig = px.bar(top_categories, 
                            x='montant_mensuel', 
                            y='categorie',
                            orientation='h',
                            title='Top 10 des Impôts par Recettes Total',
                            color='montant_mensuel',
                            color_continuous_scale='Greens')
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                top_croissance = data['current_data'].nlargest(10, 'variation_pct')
                fig = px.bar(top_croissance, 
                            x='variation_pct', 
                            y='categorie',
                            orientation='h',
                            title='Top 10 des Croissances par Catégorie (%)',
                            color='variation_pct',
                            color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab4:
            st.subheader("Analyse par Tranche de Revenu")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(data['revenu_data'], 
                           x='tranche_revenu', 
                           y='nombre_contribuables',
                           title='Nombre de Contribuables par Tranche de Revenu',
                           color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                fig = px.line(data['revenu_data'], 
                            x='tranche_revenu', 
                            y='montant_moyen_impot',
                            title='Impôt Moyen par Tranche de Revenu',
                            color_discrete_sequence=['#28a745'])
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            fig = px.bar(data['revenu_data'], 
                       x='tranche_revenu', 
                       y='taux_effectif',
                       title='Taux Effectif d\'Imposition par Tranche de Revenu (%)',
                       color_discrete_sequence=px.colors.sequential.Viridis)
            st.plotly_chart(fig, config={'displayModeBar': False})
            
            # CORRECTION: Remplacer use_container_width par width
            st.dataframe(data['revenu_data'], width='stretch')
    
    def create_categories_live(self):
        """Affiche les catégories en temps réel"""
        data = self.get_territory_data(st.session_state.selected_territory)
        
        st.markdown('<h3 class="section-header">🏢 CATÉGORIES D\'IMPÔTS EN TEMPS RÉEL</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Tableau des Recettes", "Analyse Type d'Impôt", "Simulateur Fiscal"])
        
        with tab1:
            col1, col2, col3 = st.columns(3)
            with col1:
                type_filtre = st.selectbox("Type d'impôt:", 
                                         ['Tous'] + list(data['current_data']['type_impot'].unique()))
            with col2:
                performance_filtre = st.selectbox("Performance:", 
                                                ['Toutes', 'En croissance', 'En décroissance', 'Stable'])
            with col3:
                tri_filtre = st.selectbox("Trier par:", 
                                        ['Montant mensuel', 'Variation %', 'Nombre contribuables', 'Taux moyen'])
            
            # Application des filtres
            categories_filtrees = data['current_data'].copy()
            if type_filtre != 'Tous':
                categories_filtrees = categories_filtrees[categories_filtrees['type_impot'] == type_filtre]
            if performance_filtre == 'En croissance':
                categories_filtrees = categories_filtrees[categories_filtrees['variation_pct'] > 0]
            elif performance_filtre == 'En décroissance':
                categories_filtrees = categories_filtrees[categories_filtrees['variation_pct'] < 0]
            elif performance_filtre == 'Stable':
                categories_filtrees = categories_filtrees[categories_filtrees['variation_pct'] == 0]
            
            # Tri
            if tri_filtre == 'Montant mensuel':
                categories_filtrees = categories_filtrees.sort_values('montant_mensuel', ascending=False)
            elif tri_filtre == 'Variation %':
                categories_filtrees = categories_filtrees.sort_values('variation_pct', ascending=False)
            elif tri_filtre == 'Nombre contribuables':
                categories_filtrees = categories_filtrees.sort_values('nombre_contribuables', ascending=False)
            elif tri_filtre == 'Taux moyen':
                categories_filtrees = categories_filtrees.sort_values('taux_moyen', ascending=False)
            
            # Affichage optimisé
            for _, categorie in categories_filtrees.iterrows():
                change_class = "positive" if categorie['variation_pct'] > 0 else "negative" if categorie['variation_pct'] < 0 else "neutral"
                type_class = "direct-tax" if categorie['type_impot'] == 'Direct' else "indirect-tax" if categorie['type_impot'] == 'Indirect' else "local-tax"
                
                col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
                with col1:
                    st.markdown(f"**{categorie['categorie']}**")
                    st.markdown(f"<span class='tax-type-indicator {type_class}'>{categorie['type_impot']}</span>", 
                               unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**{categorie['nom_complet']}**")
                    st.markdown(f"Taux moyen: {categorie['taux_moyen']}% | Plafond: {categorie['plafond']:,.0f}€")
                with col3:
                    st.markdown(f"**{categorie['montant_mensuel']:.1f}M€**")  # Correction: formatage correct
                    st.markdown(f"Contribuables: {categorie['nombre_contribuables']:,.0f}")
                with col4:
                    variation_str = f"{categorie['variation_pct']:+.2f}%"
                    st.markdown(f"**{variation_str}**")
                    st.markdown(f"{categorie['variation_abs']/1e3:+.0f}K€")
                with col5:
                    st.markdown(f"<div class='revenue-change {change_class}'>{variation_str}</div>", 
                               unsafe_allow_html=True)
                    st.markdown(f"Poids: {categorie['poids_total']:.1f}%")
                
                st.markdown("---")
        
        with tab2:
            type_selectionne = st.selectbox("Sélectionnez un type d'impôt:", 
                                          data['current_data']['type_impot'].unique())
            
            if type_selectionne:
                categories_type = data['current_data'][
                    data['current_data']['type_impot'] == type_selectionne
                ]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(categories_type, 
                                x='categorie', 
                                y='variation_pct',
                                title=f'Performance des Catégories - {type_selectionne}',
                                color='variation_pct',
                                color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig, config={'displayModeBar': False})
                
                with col2:
                    fig = px.pie(categories_type, 
                                values='montant_mensuel', 
                                names='categorie',
                                title=f'Répartition des Recettes - {type_selectionne}')
                    st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            st.subheader("Simulateur de Calcul d'Impôt")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                type_revenu = st.selectbox("Type de revenu:", 
                                         ["Salaires", "BIC", "BNC", "BA", "Revenus fonciers"])
                revenu_annuel = st.number_input("Revenu annuel (€):", 
                                              min_value=0.0, value=30000.0, step=1000.0)
            with col2:
                situation_familiale = st.selectbox("Situation familiale:", 
                                                 ["Célibataire", "Marié/Pacsé", "Veuf", "Divorcé"])
                nombre_enfants = st.number_input("Nombre d'enfants:", 
                                               min_value=0, max_value=10, value=0)
            with col3:
                deductions = st.number_input("Déductions (€):", 
                                          min_value=0.0, value=1000.0)
                territoire_applicable = st.selectbox("Territoire fiscal:", 
                                                   [v['nom_complet'] for v in self.territories.values()])
                calculer = st.button("Calculer l'Impôt")
            
            if calculer:
                # Calcul simplifié de l'impôt (version simulée)
                quotient_familial = 1
                if situation_familiale in ["Marié/Pacsé", "Veuf"]:
                    quotient_familial = 2
                quotient_familial += nombre_enfants * 0.5
                
                revenu_imposable = max(0, revenu_annuel - deductions)
                revenu_par_part = revenu_imposable / quotient_familial
                
                # Barème progressif simplifié
                if revenu_par_part <= 10777:
                    impot = 0
                elif revenu_par_part <= 27478:
                    impot = (revenu_par_part - 10777) * 0.11
                elif revenu_par_part <= 78570:
                    impot = (27478 - 10777) * 0.11 + (revenu_par_part - 27478) * 0.30
                else:
                    impot = (27478 - 10777) * 0.11 + (78570 - 27478) * 0.30 + (revenu_par_part - 78570) * 0.41
                
                impot_total = impot * quotient_familial
                
                st.success(f"""
                **Résultat du calcul fiscal:**
                - Territoire: {territoire_applicable}
                - Revenu annuel: {revenu_annuel:,.2f}€
                - Revenu imposable: {revenu_imposable:,.2f}€
                - Quotient familial: {quotient_familial}
                - **Impôt annuel estimé: {impot_total:,.2f}€**
                - Taux effectif: {(impot_total/revenu_annuel)*100:.1f}%
                - Mensualité: {impot_total/12:,.2f}€
                """)
    
    def create_categorie_analysis(self):
        """Analyse par catégorie détaillée"""
        data = self.get_territory_data(st.session_state.selected_territory)
        
        st.markdown('<h3 class="section-header">📊 ANALYSE PAR TYPE D\'IMPÔT DÉTAILLÉE</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Performance par Type", "Comparaison Types", "Tendances Fiscales"])
        
        with tab1:
            type_performance = data['current_data'].groupby('type_impot').agg({
                'variation_pct': 'mean',
                'nombre_contribuables': 'sum',
                'montant_mensuel': 'sum',
                'categorie': 'count'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(type_performance, 
                            x='type_impot', 
                            y='variation_pct',
                            title='Performance Moyenne par Type d\'Impôt (%)',
                            color='variation_pct',
                            color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                fig = px.scatter(type_performance, 
                               x='montant_mensuel', 
                               y='variation_pct',
                               size='nombre_contribuables',
                               color='type_impot',
                               title='Performance vs Recettes par Type d\'Impôt',
                               hover_name='type_impot',
                               size_max=60)
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab2:
            type_evolution = data['historical_data'].groupby([
                data['historical_data']['date'].dt.to_period('M').dt.to_timestamp(),
                'type_impot'
            ])['montant_total_impots'].sum().reset_index()
            
            fig = px.line(type_evolution, 
                         x='date', 
                         y='montant_total_impots',
                         color='type_impot',
                         title=f'Évolution Comparative par Type - {self.territories[st.session_state.selected_territory]["nom_complet"]}',
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(yaxis_title="Recettes Fiscales (€)")
            st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            st.subheader("Tendances et Perspectives Fiscales")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 📈 Impôts en Croissance
                
                **🏢 Impôt sur les Sociétés:**
                - Croissance économique des entreprises
                - Amélioration de la profitabilité
                - Attractivité territoriale renforcée
                
                **💰 Droits d'enregistrement:**
                - Dynamisme du marché immobilier
                - Augmentation des transactions
                - Valorisation du patrimoine
                
                **⚡ TICPE:**
                - Augmentation de la consommation énergétique
                - Hausse des prix des carburants
                - Transition écologique
                """)
            
            with col2:
                st.markdown("""
                ### 📉 Impôts en Décroissance
                
                **🏠 Taxe d'Habitation:**
                - Réforme de suppression progressive
                - Allègements pour les ménages
                - Mesures de pouvoir d'achat
                
                **👨‍👩‍👧‍👦 Impôt sur le Revenu (certaines tranches):**
                - Baisses d'impôt ciblées
                - Réformes des tranches
                - Mesures sociales
                
                **📊 Taxes locales spécifiques:**
                - Harmonisation fiscale
                - Mesures d'allègement
                - Concurrence fiscale
                """)
    
    def create_evolution_analysis(self):
        """Analyse de l'évolution des recettes fiscales"""
        data = self.get_territory_data(st.session_state.selected_territory)
        
        st.markdown('<h3 class="section-header">📈 ÉVOLUTION DES RECETTES FISCALES</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Analyse Historique", "Projections Économiques", "Réformes Fiscales"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                cumulative_data = data['historical_data'].copy()
                cumulative_data['date_group'] = cumulative_data['date'].dt.to_period('M').dt.to_timestamp()
                
                # Create cumulative sum chart
                fig = px.line(
                    cumulative_data.groupby('date_group')['montant_total_impots'].sum().reset_index(),
                    x='date_group',
                    y='montant_total_impots',
                    title='Évolution Cumulative des Recettes Fiscales',
                    color_discrete_sequence=['#28a745']
                )
                fig.update_layout(yaxis_title="Recettes Cumulatives (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                # Year over year comparison
                yearly_data = cumulative_data.copy()
                yearly_data['year'] = yearly_data['date'].dt.year
                yearly_comparison = yearly_data.groupby(['year', 'categorie'])['montant_total_impots'].sum().reset_index()
                
                fig = px.bar(
                    yearly_comparison,
                    x='year',
                    y='montant_total_impots',
                    color='categorie',
                    title='Comparaison Annuelle par Catégorie d\'Impôt',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(yaxis_title="Recettes Annuelles (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab2:
            st.subheader("Projections Économiques")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Create projection data
                projection_years = 5
                last_date = data['historical_data']['date'].max()
                projection_dates = pd.date_range(
                    start=last_date + pd.DateOffset(months=1),
                    periods=projection_years * 12,
                    freq='M'
                )
                
                projection_data = []
                for date in projection_dates:
                    for categorie_code, categorie_info in data['categories'].items():
                        # Base projection with growth factor
                        growth_factor = 1.0 + (categorie_info['evolution_annuelle'] / 100) / 12
                        base_amount = categorie_info['montant_annuel'] / 12
                        projected_amount = base_amount * growth_factor * random.uniform(0.95, 1.05)
                        
                        projection_data.append({
                            'date': date,
                            'categorie': categorie_code,
                            'montant_total_impots': projected_amount,
                            'type': 'projection'
                        })
                
                projection_df = pd.DataFrame(projection_data)
                
                # Combine historical and projection data
                historical_for_projection = data['historical_data'].copy()
                historical_for_projection['type'] = 'historical'
                
                combined_data = pd.concat([
                    historical_for_projection[['date', 'categorie', 'montant_total_impots', 'type']],
                    projection_df
                ])
                
                # Plot projection
                fig = px.line(
                    combined_data.groupby(['date', 'type'])['montant_total_impots'].sum().reset_index(),
                    x='date',
                    y='montant_total_impots',
                    color='type',
                    title='Projection des Recettes Fiscales (5 ans)',
                    color_discrete_map={'historical': '#28a745', 'projection': '#dc3545'}
                )
                fig.update_layout(yaxis_title="Recettes (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                # Projection by category
                category_projection = projection_df.groupby('categorie')['montant_total_impots'].sum().reset_index()
                
                fig = px.bar(
                    category_projection,
                    x='categorie',
                    y='montant_total_impots',
                    title='Projection par Catégorie (5 ans)',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(yaxis_title="Recettes Projetées (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            st.subheader("Impact des Réformes Fiscales")
            
            # Create reform impact visualization
            reform_data = []
            
            # Define some reform scenarios
            reforms = [
                {'name': 'Réforme 2018', 'date': '2018-01-01', 'impact': 1.1, 'description': 'Réforme fiscale majeure'},
                {'name': 'COVID-19', 'date': '2020-03-01', 'impact': 0.9, 'description': 'Impact de la pandémie'},
                {'name': 'Plan de Relance', 'date': '2021-06-01', 'impact': 1.05, 'description': 'Mesures de relance économique'},
                {'name': 'Transition Écologique', 'date': '2022-01-01', 'impact': 1.03, 'description': 'Taxes vertes'}
            ]
            
            for reform in reforms:
                reform_date = pd.to_datetime(reform['date'])
                before_period = data['historical_data'][
                    (data['historical_data']['date'] >= reform_date - pd.DateOffset(months=6)) &
                    (data['historical_data']['date'] < reform_date)
                ]['montant_total_impots'].mean()
                
                after_period = data['historical_data'][
                    (data['historical_data']['date'] >= reform_date) &
                    (data['historical_data']['date'] < reform_date + pd.DateOffset(months=6))
                ]['montant_total_impots'].mean()
                
                if before_period > 0:
                    actual_impact = after_period / before_period
                else:
                    actual_impact = 1.0
                
                reform_data.append({
                    'reform': reform['name'],
                    'date': reform['date'],
                    'planned_impact': reform['impact'],
                    'actual_impact': actual_impact,
                    'description': reform['description']
                })
            
            reform_df = pd.DataFrame(reform_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    reform_df,
                    x='reform',
                    y=['planned_impact', 'actual_impact'],
                    title='Impact des Réformes Fiscales',
                    barmode='group',
                    color_discrete_map={
                        'planned_impact': '#28a745',
                        'actual_impact': '#dc3545'
                    }
                )
                fig.update_layout(yaxis_title="Facteur d'Impact (1.0 = pas de changement)")
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                # CORRECTION: Remplacer use_container_width par width
                st.dataframe(
                    reform_df[['reform', 'date', 'description', 'planned_impact', 'actual_impact']],
                    width='stretch'
                )
    
    def create_territory_comparison(self):
        """Crée la vue de comparaison entre territoires"""
        st.markdown('<h3 class="section-header">🌍 COMPARAISON INTER-TERRITOIRES</h3>', 
                   unsafe_allow_html=True)
        
        comparison_data = generate_comparison_data(self.territories)
        
        tab1, tab2, tab3 = st.tabs(["Vue d'Ensemble", "Comparaison Détaillée", "Classements"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    comparison_data,
                    x='nom_complet',
                    y='recettes_fiscales_total',
                    title='Recettes Fiscales Totales par Territoire',
                    color='type',
                    color_discrete_map={'DROM': '#28a745', 'COM': '#dc3545'}
                )
                fig.update_layout(yaxis_title="Recettes Fiscales (M€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                fig = px.bar(
                    comparison_data,
                    x='nom_complet',
                    y='recettes_par_habitant',
                    title='Recettes par Habitant',
                    color='type',
                    color_discrete_map={'DROM': '#28a745', 'COM': '#dc3545'}
                )
                fig.update_layout(yaxis_title="Recettes par Habitant (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab2:
            selected_territories = st.multiselect(
                "Sélectionnez les territoires à comparer:",
                options=comparison_data['nom_complet'].tolist(),
                default=[self.territories[st.session_state.selected_territory]['nom_complet']]
            )
            
            if selected_territories:
                filtered_data = comparison_data[comparison_data['nom_complet'].isin(selected_territories)]
                
                metrics = ['population', 'pib', 'recettes_fiscales_total', 'recettes_par_habitant', 'taux_imposition_moyen', 'pression_fiscale']
                selected_metric = st.selectbox("Sélectionnez une métrique:", metrics)
                
                fig = px.bar(
                    filtered_data,
                    x='nom_complet',
                    y=selected_metric,
                    title=f'Comparaison: {selected_metric}',
                    color='type',
                    color_discrete_map={'DROM': '#28a745', 'COM': '#dc3545'}
                )
                st.plotly_chart(fig, config={'displayModeBar': False})
                
                # CORRECTION: Remplacer use_container_width par width
                st.dataframe(filtered_data, width='stretch')
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Classement par Recettes Totales")
                top_recettes = comparison_data.sort_values('recettes_fiscales_total', ascending=False)
                # CORRECTION: Remplacer use_container_width par width
                st.dataframe(top_recettes[['nom_complet', 'type', 'recettes_fiscales_total']], width='stretch')
            
            with col2:
                st.subheader("Classement par Recettes par Habitant")
                top_par_habitant = comparison_data.sort_values('recettes_par_habitant', ascending=False)
                # CORRECTION: Remplacer use_container_width par width
                st.dataframe(top_par_habitant[['nom_complet', 'type', 'recettes_par_habitant']], width='stretch')
    
    def run(self):
        """Exécute le dashboard"""
        # Affichage de l'en-tête
        self.display_header()
        
        # Sélecteur de territoire
        self.display_territory_selector()
        
        # Mise à jour des données en temps réel
        if st.sidebar.button("🔄 Actualiser les données"):
            self.update_live_data(st.session_state.selected_territory)
            st.success("Données actualisées avec succès!")
        
        # Affichage des métriques clés
        self.display_key_metrics()
        
        # Vue d'ensemble des impôts
        self.create_impots_overview()
        
        # Catégories en temps réel
        self.create_categories_live()
        
        # Analyse par type d'impôt
        self.create_categorie_analysis()
        
        # Analyse de l'évolution
        self.create_evolution_analysis()
        
        # Comparaison entre territoires
        self.create_territory_comparison()
        
        # Footer
        st.markdown("---")
        st.markdown("© 2023 Dashboard Impôts DROM-COM - Données simulées à des fins de démonstration")

# Point d'entrée principal
if __name__ == "__main__":
    dashboard = ImpotsDashboard()
    dashboard.run()