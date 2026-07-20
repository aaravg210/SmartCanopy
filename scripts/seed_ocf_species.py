"""
Seed OCF VTA-Approved Tree Species
Source: "Approved Tree Species List for VTA-supported Programs"
        Our City Forest — East Side Trees, 680 Soundwall, Sunnyvale
        Last updated: 2/5/2026

Run:  python scripts/seed_ocf_species.py

Existing species with the same species_id are updated (upserted) so this
script is safe to run multiple times.

For existing databases that predate this script, run the migration first:
    ALTER TABLE plant_species
        ADD COLUMN IF NOT EXISTS vta_approved  BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS csj_street_tree BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS fall_color    BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS flowers       BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS ocf_notes     TEXT;
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.services.plant_database import DatabaseManager, PlantSpecies
from agent.config import settings
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _benefits(h_max: int, evergreen: bool = False) -> dict:
    """
    Estimate i-Tree annual environmental benefits by mature height class.
    Evergreen trees receive a 30% stormwater boost (year-round leaf area).
    Values are consistent with i-Tree Eco published averages for California.
    """
    if h_max <= 10:
        co2, storm, air = 5.0, 800, 0.05
    elif h_max <= 25:
        co2, storm, air = 12.0, 1500, 0.20
    elif h_max <= 35:
        co2, storm, air = 20.0, 2800, 0.38
    elif h_max <= 50:
        co2, storm, air = 35.0, 5000, 0.65
    elif h_max <= 65:
        co2, storm, air = 60.0, 9000, 1.10
    elif h_max <= 75:
        co2, storm, air = 90.0, 14000, 1.80
    else:
        co2, storm, air = 125.0, 20000, 2.50
    if evergreen:
        storm = round(storm * 1.3)
    return {
        'co2_sequestration_kg_year': co2,
        'stormwater_gallons_year': float(storm),
        'air_pollution_removal_kg_year': air,
    }


def _sp(
    h_min: int, h_max: int, sp_min: int, sp_max: int,
    deciduous: bool = True, conifer: bool = False,
) -> dict:
    """Build size + tree_type + benefits sub-dict."""
    is_ev = not deciduous
    tt = 'conifer' if conifer else ('evergreen' if is_ev else 'deciduous')
    return {
        'mature_height_ft_min': h_min,
        'mature_height_ft_max': h_max,
        'mature_spread_ft_min': sp_min,
        'mature_spread_ft_max': sp_max,
        'tree_type': tt,
        **_benefits(h_max, evergreen=is_ev or conifer),
    }


BAY_AREA_ZONES = {'hardiness_zone_min': 7, 'hardiness_zone_max': 10}
FULL_SUN = {'sunlight': 'full_sun'}
LOW_MAINT = {'maintenance_level': 'low', 'pest_resistance': 'high', 'disease_resistance': 'high'}
DRY_SOIL = {'soil_types': ['clay', 'loam', 'sandy'], 'moisture_tolerance': 'dry'}
MED_SOIL = {'soil_types': ['clay', 'loam'], 'moisture_tolerance': 'medium'}


def _base(drought: bool = True) -> dict:
    return {
        **BAY_AREA_ZONES,
        **FULL_SUN,
        **LOW_MAINT,
        **(DRY_SOIL if drought else MED_SOIL),
        'drought_tolerant': drought,
        'energy_savings_kwh_year': None,
        'price_sapling': None,
        'price_6ft': None,
        'price_8ft': None,
        'price_10ft': None,
        'vta_approved': True,
        'growth_rate': 'medium',
    }


# ---------------------------------------------------------------------------
# Species data — all 55 species from the OCF VTA list
# ---------------------------------------------------------------------------

OCF_SPECIES = [
    # ── California Natives ──────────────────────────────────────────────────
    {
        **_base(), **_sp(20, 25, 20, 30),
        'species_id': 'AESCA',
        'scientific_name': 'Aesculus californica',
        'common_name': 'California Buckeye',
        'family': 'Sapindaceae',
        'native_regions': ['california'],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Drops leaves in summer (drought deciduous) to conserve water. '
                       'Fragrant white flower spikes in spring; large chestnuts in fall.',
        'ocf_notes': 'Drought deciduous — summer leaf drop is normal, not die-off.',
    },
    {
        **_base(), **_sp(20, 25, 10, 20),
        'species_id': 'CEOCC',
        'scientific_name': 'Cercis occidentalis',
        'common_name': 'Western Redbud',
        'family': 'Fabaceae',
        'native_regions': ['california'],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Multi-stemmed native with vivid magenta flowers before leaves emerge. '
                       'Heart-shaped foliage; good wildlife value.',
        'ocf_notes': 'Great for pollinators and birds.',
    },
    {
        **_base(), **_sp(20, 30, 10, 20),
        'species_id': 'CHLIN',
        'scientific_name': 'Chilopsis linearis',
        'common_name': 'Desert Willow',
        'family': 'Bignoniaceae',
        'native_regions': ['california'],
        'csj_street_tree': False,
        'fall_color': True,
        'flowers': True,
        'description': 'Willow-like narrow leaves; orchid-like flowers attract hummingbirds. '
                       'Fast-growing, heat-loving desert native.',
    },
    {
        **_base(), **_sp(20, 30, 10, 30, deciduous=False),
        'species_id': 'MYCAL',
        'scientific_name': 'Myrica californica',
        'common_name': 'Pacific Wax Myrtle',
        'family': 'Myricaceae',
        'native_regions': ['california'],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': True,
        'description': 'Dense evergreen screen; aromatic foliage; salt and wind tolerant. '
                       'Small catkins; waxy berries attract birds.',
    },
    {
        **_base(), **_sp(30, 70, 30, 70, deciduous=False),
        'species_id': 'QUAGR',
        'scientific_name': 'Quercus agrifolia',
        'common_name': 'Coast Live Oak',
        'family': 'Fagaceae',
        'native_regions': ['california'],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': False,
        'growth_rate': 'slow',
        'description': 'Iconic Bay Area evergreen oak with dense rounded canopy. '
                       'Excellent wildlife habitat; supports hundreds of insect species.',
        'ocf_notes': 'Long-lived Bay Area native; do not irrigate near trunk once established.',
    },
    {
        **_base(), **_sp(40, 70, 40, 50),
        'species_id': 'QUDOU',
        'scientific_name': 'Quercus douglasii',
        'common_name': 'Blue Oak',
        'family': 'Fagaceae',
        'native_regions': ['california'],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': False,
        'growth_rate': 'slow',
        'description': 'Blue-gray foliage; highly drought tolerant once established. '
                       'Common in California foothills.',
    },
    {
        **_base(), **_sp(40, 70, 75, 80, deciduous=False),
        'species_id': 'QUENG',
        'scientific_name': 'Quercus engelmannii',
        'common_name': 'Engelmann Oak',
        'family': 'Fagaceae',
        'native_regions': ['california'],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': False,
        'growth_rate': 'slow',
        'description': 'Rare semi-evergreen oak; blue-green leaves; very wide canopy spread. '
                       'Occurs naturally in Southern California foothills.',
    },
    {
        **_base(), **_sp(40, 70, 50, 50),
        'species_id': 'QULOB',
        'scientific_name': 'Quercus lobata',
        'common_name': 'Valley Oak',
        'family': 'Fagaceae',
        'native_regions': ['california'],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': False,
        'growth_rate': 'slow',
        'description': 'Largest North American oak; massive spreading canopy; deeply lobed leaves. '
                       'Iconic California valley tree with great wildlife value.',
        'ocf_notes': 'Semi-deciduous — may retain some leaves through winter.',
    },
    {
        **_base(drought=False), **_sp(40, 80, 30, 50),
        'species_id': 'POFRE',
        'scientific_name': 'Populus fremontii',
        'common_name': 'Fremont Cottonwood',
        'family': 'Salicaceae',
        'native_regions': ['california'],
        'csj_street_tree': False,
        'fall_color': True,
        'flowers': False,
        'growth_rate': 'fast',
        'description': 'Riparian native; brilliant golden fall color. '
                       'Best planted near water sources; important wildlife tree.',
        'ocf_notes': 'Not drought tolerant — requires supplemental summer water.',
    },

    # ── Non-Native, Drought Tolerant ────────────────────────────────────────
    {
        **_base(), **_sp(5, 7, 7, 8),
        'species_id': 'CECOV',
        'scientific_name': "Cercis canadensis 'Covey'",
        'common_name': 'Lavender Twist Redbud',
        'family': 'Fabaceae',
        'native_regions': [],
        'csj_street_tree': False,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Weeping mounding habit; magenta flowers on pendulous branches. '
                       'Ideal for small residential yards.',
        'hardiness_zone_min': 5,
    },
    {
        **_base(), **_sp(15, 20, 20, 25),
        'species_id': 'CEOKL',
        'scientific_name': "Cercis canadensis var. texensis 'Oklahoma'",
        'common_name': 'Oklahoma Redbud',
        'family': 'Fabaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'description': 'Texas variety with glossy heat-tolerant leaves; wine-red buds open to rose-purple.',
    },
    {
        **_base(), **_sp(15, 20, 8, 10),
        'species_id': 'CHTKY',
        'scientific_name': "Chionanthus retusus 'Tokyo Tower'",
        'common_name': 'Columnar Chinese Fringe Tree',
        'family': 'Oleaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Very narrow columnar form; fragrant white fringe flowers; ideal for tight spaces.',
    },
    {
        **_base(), **_sp(15, 20, 15, 20),
        'species_id': 'CHRET',
        'scientific_name': 'Chionanthus retusus',
        'common_name': 'Chinese Fringe Tree',
        'family': 'Oleaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Outstanding white fringe-like flower display in spring. '
                       'Blue-black drupes attract birds; bright yellow fall color.',
    },
    {
        **_base(), **_sp(20, 25, 15, 18),
        'species_id': 'ZEJK1',
        'scientific_name': "Zelkova serrata 'JFS-KW1'",
        'common_name': 'City Sprite Zelkova',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Compact vase form; great for narrow parkways and small spaces. '
                       'Elm-like texture; yellow fall color.',
    },
    {
        **_base(), **_sp(20, 25, 30, 36),
        'species_id': 'ZESCM',
        'scientific_name': "Zelkova serrata 'Schmidtlow'",
        'common_name': 'Wireless Zelkova',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Low-branching spreading form; good option under power lines. '
                       'Red fall color; tough urban performer.',
    },
    {
        **_base(), **_sp(25, 30, 35, 40),
        'species_id': 'CLKEN',
        'scientific_name': 'Cladrastis kentuckea',
        'common_name': 'American Yellowwood',
        'family': 'Fabaceae',
        'native_regions': [],
        'csj_street_tree': False,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Fragrant drooping white flower clusters in late spring. '
                       'Smooth gray beech-like bark; brilliant yellow fall color.',
    },
    {
        **_base(), **_sp(25, 30, 25, 30),
        'species_id': 'KOPAN',
        'scientific_name': 'Koelreuteria paniculata',
        'common_name': 'Golden Rain Tree',
        'family': 'Sapindaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'description': 'Yellow flower panicles in summer (rare for trees); papery pink seed capsules. '
                       'Very heat and drought tolerant once established.',
    },
    {
        **_base(), **_sp(20, 35, 20, 35, deciduous=False),
        'species_id': 'ARUUN',
        'scientific_name': 'Arbutus unedo',
        'common_name': 'Strawberry Tree',
        'family': 'Ericaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Evergreen with white urn-shaped flowers and red fruit simultaneously. '
                       'Peeling reddish bark; very drought tolerant.',
    },
    {
        **_base(), **_sp(25, 35, 15, 20),
        'species_id': 'NYHAY',
        'scientific_name': "Nyssa sylvatica 'Haymanred'",
        'common_name': 'Red Rage Tupelo',
        'family': 'Nyssaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Outstanding hot coppery-red fall color; one of the best fall color trees for the Bay Area. '
                       'Upright form; adaptable to clay soils.',
    },
    {
        **_base(), **_sp(25, 35, 20, 25),
        'species_id': 'ULJB1',
        'scientific_name': "Ulmus propinqua 'JFS-Bieberich'",
        'common_name': 'Emerald Sunshine Elm',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Compact vase-shaped elm with lustrous dark green leaves. '
                       'Excellent disease resistance; yellow fall color.',
    },
    {
        **_base(), **_sp(25, 40, 25, 30, deciduous=False),
        'species_id': 'ARMAR',
        'scientific_name': "Arbutus 'Marina'",
        'common_name': 'Marina Strawberry Tree',
        'family': 'Ericaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Reliable Bay Area performer with rosy-pink flowers nearly year-round. '
                       'Exfoliating cinnamon bark; evergreen.',
    },
    {
        **_base(), **_sp(30, 40, 20, 28),
        'species_id': 'CAJKW',
        'scientific_name': "Carpinus betulus 'JFS-KW1CB'",
        'common_name': 'Emerald Avenue Hornbeam',
        'family': 'Betulaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'growth_rate': 'slow',
        'description': 'Narrow upright habit; muscular fluted gray bark; retains tan leaves through winter '
                       'providing winter interest.',
    },
    {
        **_base(), **_sp(20, 40, 25, 35),
        'species_id': 'CECAN',
        'scientific_name': 'Cercis canadensis',
        'common_name': 'Eastern Redbud',
        'family': 'Fabaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'description': 'Spectacular magenta spring flowers before leaf-out. '
                       'Heart-shaped leaves; adapts well to Bay Area conditions.',
    },
    {
        **_base(), **_sp(25, 40, 30, 35),
        'species_id': 'CHTTS',
        'scientific_name': "Chitalpa tashkentensis 'Strawberry Moon'",
        'common_name': 'Strawberry Moon Chitalpa',
        'family': 'Bignoniaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'fast',
        'description': 'Hybrid of Catalpa and Desert Willow. '
                       'Large showy pink flowers from summer through fall; very heat tolerant.',
    },
    {
        **_base(), **_sp(25, 40, 15, 30, deciduous=False),
        'species_id': 'LASAR',
        'scientific_name': "Laurus nobilis 'Saratoga'",
        'common_name': 'Saratoga Sweet Bay Laurel',
        'family': 'Lauraceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Culinary bay laurel; dense evergreen canopy; aromatic foliage. '
                       'Good for screening; very adaptable to Bay Area soils.',
    },
    {
        **_base(), **_sp(25, 40, 35, 40),
        'species_id': 'QUBCK',
        'scientific_name': 'Quercus buckleyi',
        'common_name': 'Texas Red Oak',
        'family': 'Fagaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Deeply lobed leaves; outstanding orange-red to red fall color. '
                       'Adapts well to Bay Area summer drought after establishment.',
    },
    {
        **_base(), **_sp(30, 40, 25, 30),
        'species_id': 'TICGR',
        'scientific_name': "Tilia cordata 'Greenspire'",
        'common_name': 'Greenspire Littleleaf Linden',
        'family': 'Malvaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Pyramidal symmetrical habit; fragrant late-spring flowers attract pollinators. '
                       'Yellow fall color; excellent urban tolerance.',
    },
    {
        **_base(), **_sp(25, 40, 25, 30, deciduous=False),
        'species_id': 'TRLAW',
        'scientific_name': 'Tristania laurina',
        'common_name': 'Water Gum',
        'family': 'Myrtaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Narrow upright evergreen; reddish exfoliating bark; small yellow flowers in summer.',
    },
    {
        **_base(), **_sp(25, 40, 25, 30),
        'species_id': 'ULFRO',
        'scientific_name': "Ulmus 'Frontier'",
        'common_name': 'Frontier Elm',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Burgundy-red fall color; disease resistant hybrid elm. '
                       'Vase-shaped; tough urban performer.',
    },
    {
        **_base(), **_sp(35, 45, 25, 30),
        'species_id': 'COCOL',
        'scientific_name': 'Corylus colurna',
        'common_name': 'Turkish Hazel',
        'family': 'Betulaceae',
        'native_regions': [],
        'csj_street_tree': False,
        'fall_color': True,
        'flowers': False,
        'growth_rate': 'slow',
        'description': 'Strongly pyramidal form; interesting corky bark; heat and drought tolerant. '
                       'Yellow fall color; small edible hazelnuts.',
    },
    {
        **_base(), **_sp(30, 45, 25, 35),
        'species_id': 'GIAG1',
        'scientific_name': "Ginkgo biloba 'Autumn Gold'",
        'common_name': "Ginkgo 'Autumn Gold'",
        'family': 'Ginkgoaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'growth_rate': 'slow',
        'description': "Male clone (no messy fruit); brilliant golden fall color. "
                       "Pest- and disease-free; one of the oldest tree species on Earth.",
    },
    {
        **_base(), **_sp(30, 45, 30, 40),
        'species_id': 'GIHA1',
        'scientific_name': "Ginkgo biloba 'Halka'",
        'common_name': "Ginkgo 'Halka'",
        'family': 'Ginkgoaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': "Male clone; faster-growing than Autumn Gold; bright yellow fall color. "
                       "Good symmetrical form for street planting.",
    },
    {
        **_base(), **_sp(30, 45, 10, 14),
        'species_id': 'QUSSP',
        'scientific_name': "Quercus 'Streetspire'",
        'common_name': 'Streetspire Oak',
        'family': 'Fagaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Very narrow columnar oak; ideal for tight urban spaces and narrow parkways. '
                       'Rusty red fall color.',
    },
    {
        **_base(), **_sp(30, 45, 25, 35),
        'species_id': 'TIGMT',
        'scientific_name': "Tilia tomentosa 'Green Mountain'",
        'common_name': 'Green Mountain Linden',
        'family': 'Malvaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Dense pyramidal form; silver-white leaf undersides; heat and drought tolerant. '
                       'Fragrant flowers in early summer.',
    },
    {
        **_base(), **_sp(30, 45, 25, 35),
        'species_id': 'TISTL',
        'scientific_name': "Tilia tomentosa 'Sterling'",
        'common_name': 'Silver Linden',
        'family': 'Malvaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Striking silver leaf undersides flutter in the breeze. '
                       'Fragrant flowers; pyramidal form; excellent urban tolerance.',
    },
    {
        **_base(), **_sp(30, 45, 25, 30),
        'species_id': 'ZEGVS',
        'scientific_name': "Zelkova serrata 'Green Vase'",
        'common_name': 'Green Vase Zelkova',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'growth_rate': 'fast',
        'description': 'Classic vase-shaped zelkova; faster growing than most; orange fall color. '
                       'Excellent disease resistance and urban tolerance.',
    },
    {
        **_base(), **_sp(30, 45, 12, 15),
        'species_id': 'ZEMUS',
        'scientific_name': "Zelkova serrata 'Musashino'",
        'common_name': 'Columnar Zelkova',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Very narrow columnar form; ideal for tight parkways. '
                       'Yellow fall color; excellent branch structure.',
    },
    {
        **_base(), **_sp(30, 50, 35, 50),
        'species_id': 'AECBR',
        'scientific_name': "Aesculus x carnea 'Briotii'",
        'common_name': 'Ruby Red Horsechestnut',
        'family': 'Sapindaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'slow',
        'description': 'Spectacular deep red flower candles in spring. '
                       'Large palmate leaves; dense shade canopy; orange-brown fall color.',
    },
    {
        **_base(), **_sp(30, 50, 30, 50, deciduous=False, conifer=True),
        'species_id': 'AFGRA',
        'scientific_name': 'Afrocarpus gracilior',
        'common_name': 'African Fern Pine',
        'family': 'Podocarpaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': False,
        'growth_rate': 'slow',
        'description': 'Graceful weeping evergreen conifer with fine feathery foliage. '
                       'Very adaptable to Bay Area soils and conditions.',
    },
    {
        **_base(), **_sp(35, 50, 30, 40),
        'species_id': 'CELMA',
        'scientific_name': "Celtis 'Magnifica'",
        'common_name': 'Magnifica Hackberry',
        'family': 'Cannabaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Very tough urban tree tolerating compaction, drought, and poor soils. '
                       'Small berries attract birds; yellow fall color.',
    },
    {
        **_base(), **_sp(25, 50, 15, 30),
        'species_id': 'JACMI',
        'scientific_name': 'Jacaranda mimosifolia',
        'common_name': 'Jacaranda',
        'family': 'Bignoniaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'fast',
        'hardiness_zone_min': 9,
        'description': 'Iconic lavender-blue flower canopy in late spring/summer. '
                       'Delicate fern-like foliage; best in frost-free Bay Area microclimates.',
        'ocf_notes': 'Frost sensitive — plant in sheltered locations away from frost pockets.',
    },
    {
        **_base(), **_sp(35, 50, 30, 40),
        'species_id': 'QUBCO',
        'scientific_name': "Quercus bicolor 'JFS-KW12'",
        'common_name': 'American Dream Oak',
        'family': 'Fagaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Exfoliating shaggy bark for winter interest; yellow fall color. '
                       'Adapts to both wet and dry soils; good urban tolerance.',
    },
    {
        **_base(), **_sp(35, 50, 20, 30),
        'species_id': 'QUFRS',
        'scientific_name': "Quercus frainetto 'Schmidt'",
        'common_name': 'Forest Green Oak',
        'family': 'Fagaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'growth_rate': 'fast',
        'description': 'Fast-growing for an oak; deeply lobed large leaves. '
                       'Yellow-brown fall color; retains some leaves in winter.',
    },
    {
        **_base(), **_sp(35, 50, 35, 45),
        'species_id': 'QURUB',
        'scientific_name': 'Quercus rubra',
        'common_name': 'Red Oak',
        'family': 'Fagaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Outstanding red fall color; fastest-growing oak species. '
                       'Good urban tolerance; broadly oval crown.',
    },
    {
        **_base(), **_sp(40, 60, 20, 40),
        'species_id': 'CASPE',
        'scientific_name': 'Catalpa speciosa',
        'common_name': 'Northern Catalpa',
        'family': 'Bignoniaceae',
        'native_regions': [],
        'csj_street_tree': False,
        'fall_color': True,
        'flowers': True,
        'growth_rate': 'fast',
        'description': 'Showy white orchid-like flowers in June; large tropical-looking leaves. '
                       'Long seed pods; very tough urban tree.',
    },
    {
        **_base(), **_sp(40, 60, 20, 30, deciduous=False, conifer=True),
        'species_id': 'CEDED',
        'scientific_name': 'Cedrus deodara',
        'common_name': 'Deodar Cedar',
        'family': 'Pinaceae',
        'native_regions': [],
        'csj_street_tree': False,
        'fall_color': False,
        'flowers': False,
        'description': 'Graceful weeping conifer with blue-green needles; Himalayan native. '
                       'Requires ample space; very drought tolerant once established.',
    },
    {
        **_base(), **_sp(40, 60, 50, 70),
        'species_id': 'QUMUE',
        'scientific_name': 'Quercus muehlenbergii',
        'common_name': 'Chinquapin Oak',
        'family': 'Fagaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Toothed leaves resembling chestnut; orange to red fall color. '
                       'Adapts to alkaline soils; wide spreading canopy at maturity.',
    },
    {
        **_base(), **_sp(40, 60, 45, 50),
        'species_id': 'ZEVGL',
        'scientific_name': "Zelkova serrata 'Village Green'",
        'common_name': 'Village Green Zelkova',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'growth_rate': 'fast',
        'description': 'Vase-shaped form; rusty red fall color; good branch structure. '
                       'Fast growing; tough urban performer.',
    },
    {
        **_base(), **_sp(50, 70, 35, 40),
        'species_id': 'QUSHU',
        'scientific_name': 'Quercus shumardii',
        'common_name': 'Shumard Oak',
        'family': 'Fagaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Brilliant red fall color; broadly pyramidal form at maturity. '
                       'Adapts to clay and alkaline soils; good urban tolerance.',
    },
    {
        **_base(), **_sp(40, 70, 40, 75, deciduous=False),
        'species_id': 'QUWIS',
        'scientific_name': 'Quercus wislizeni',
        'common_name': 'Interior Live Oak',
        'family': 'Fagaceae',
        'native_regions': ['california'],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': False,
        'growth_rate': 'slow',
        'description': 'Dense evergreen canopy; very drought tolerant once established. '
                       'Spiny holly-like leaves; common in Bay Area foothills.',
        'ocf_notes': 'CA native — found naturally in Santa Clara County.',
    },
    {
        **_base(), **_sp(50, 70, 50, 60),
        'species_id': 'ULACO',
        'scientific_name': "Ulmus davidiana 'Morton'",
        'common_name': 'Accolade Elm',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'growth_rate': 'fast',
        'description': 'Excellent Dutch Elm Disease resistance; graceful broad vase form. '
                       'Yellow fall color; fast growing; excellent urban tree.',
    },
    {
        **_base(), **_sp(50, 70, 50, 65),
        'species_id': 'ZESER',
        'scientific_name': 'Zelkova serrata',
        'common_name': 'Japanese Zelkova',
        'family': 'Ulmaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Classic vase-shaped street tree; graceful arching branches. '
                       'Yellow to orange fall color; disease resistant.',
    },
    {
        **_base(), **_sp(60, 80, 60, 75, deciduous=False),
        'species_id': 'QUVIR',
        'scientific_name': 'Quercus virginiana',
        'common_name': 'Southern Live Oak',
        'family': 'Fagaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': True,
        'flowers': False,
        'description': 'Massive spreading evergreen oak; iconic in Southern landscapes. '
                       'Extremely long-lived; excellent shade and wildlife value.',
    },
    {
        **_base(), **_sp(50, 80, 25, 35, deciduous=True, conifer=True),
        'species_id': 'TADIS',
        'scientific_name': 'Taxodium distichum',
        'common_name': 'Bald Cypress',
        'family': 'Cupressaceae',
        'native_regions': [],
        'csj_street_tree': False,
        'fall_color': True,
        'flowers': False,
        'description': 'Deciduous conifer with feathery soft needles; reddish-brown fall color. '
                       'Thrives in moist soils; tolerates periodic flooding.',
    },
    {
        **_base(), **_sp(25, 45, 30, 35, deciduous=False),
        'species_id': 'MEEXC',
        'scientific_name': 'Metrosideros excelsa',
        'common_name': 'New Zealand Christmas Tree',
        'family': 'Myrtaceae',
        'native_regions': [],
        'csj_street_tree': True,
        'fall_color': False,
        'flowers': True,
        'growth_rate': 'slow',
        'hardiness_zone_min': 9,
        'description': 'Brilliant red bottle-brush flowers in summer. '
                       'Excellent coastal and wind tolerance; striking evergreen street tree.',
    },
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

async def seed_ocf_species():
    logger.info("Starting OCF species seed (%d species)...", len(OCF_SPECIES))

    db_manager = DatabaseManager(settings.database_url)

    try:
        await db_manager.create_tables()
        logger.info("Tables verified.")
    except Exception as e:
        logger.error("Error creating tables: %s", e)
        return

    inserted = updated = skipped = 0

    async with db_manager.get_session() as session:
        try:
            for data in OCF_SPECIES:
                sid = data['species_id']
                existing = (await session.execute(
                    select(PlantSpecies).where(PlantSpecies.species_id == sid)
                )).scalar_one_or_none()

                if existing:
                    # Update all fields
                    for key, value in data.items():
                        if key != 'species_id' and hasattr(existing, key):
                            setattr(existing, key, value)
                    logger.info("Updated:  %s (%s)", sid, data['common_name'])
                    updated += 1
                else:
                    session.add(PlantSpecies(**data))
                    logger.info("Inserted: %s (%s)", sid, data['common_name'])
                    inserted += 1

            await session.commit()
            logger.info(
                "Done — inserted %d, updated %d, skipped %d",
                inserted, updated, skipped,
            )

        except Exception as e:
            logger.error("Seed failed: %s", e)
            await session.rollback()
            raise

    logger.info("OCF species seed complete.")


if __name__ == '__main__':
    asyncio.run(seed_ocf_species())
