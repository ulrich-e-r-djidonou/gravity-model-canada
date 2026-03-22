"""
Configuration du projet Gravity Model — Exportations canadiennes
"""
from pathlib import Path

# Répertoires
ROOT_DIR = Path(__file__).parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_CLEAN = ROOT_DIR / "data" / "clean"
OUTPUTS = ROOT_DIR / "outputs"

# Canada ISO
CANADA_ISO3 = "CAN"
CANADA_ISO_NUM = 124

# Période d'analyse
YEAR_START = 2000
YEAR_END = 2022

# Secteurs d'intérêt pour EDC (codes SITC Rev.3 — 1 chiffre)
SECTORS = {
    0: "Produits alimentaires",
    1: "Boissons et tabacs",
    2: "Matières brutes",
    3: "Combustibles et énergie",
    4: "Huiles et graisses",
    5: "Produits chimiques",
    6: "Produits manufacturés",
    7: "Machines et matériel de transport",
    8: "Articles manufacturés divers",
    9: "Autres",
}

# Variables gravitaires
GRAVITY_VARS = [
    "dist",           # Distance bilatérale (km)
    "contig",         # Frontière commune (0/1)
    "comlang_off",    # Langue officielle commune (0/1)
    "comcol",         # Passé colonial commun (0/1)
    "col_dep",        # Relation coloniale directe (0/1)
    "rta",            # Accord commercial régional (0/1)
    "gdp_o",          # PIB exportateur
    "gdp_d",          # PIB importateur
    "pop_o",          # Population exportateur
    "pop_d",          # Population importateur
]
