"""
Pipeline principal — Gravity Model des exportations canadiennes.

Ce projet identifie les marchés sous-exploités pour les exportateurs
canadiens en utilisant un modèle gravitaire estimé par PPML.

Étapes :
    1. Téléchargement et préparation des données
    2. Estimation du modèle gravitaire (OLS, PPML, PPML+FE)
    3. Calcul du potentiel commercial
    4. Identification des opportunités EDC

Usage :
    python main.py              # Pipeline complet
    streamlit run src/dashboard.py  # Dashboard interactif
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.data_download import build_gravity_panel
from src.model import load_panel, compare_specifications, estimate_ppml_basic
from src.potential import calculate_trade_potential, identify_edc_opportunities
from config import OUTPUTS

import numpy as np


def main():
    print("=" * 70)
    print("  GRAVITY MODEL — EXPORTATIONS CANADIENNES")
    print("  Identification des marchés sous-exploités")
    print("=" * 70)

    # ── Étape 1 : Données ──
    print("\n\n[1/4] TÉLÉCHARGEMENT ET PRÉPARATION DES DONNÉES")
    print("-" * 50)
    panel = build_gravity_panel()
    if panel.empty:
        print("ERREUR : Impossible de construire le panel. Arrêt.")
        sys.exit(1)

    # ── Étape 2 : Estimation ──
    print("\n\n[2/4] ESTIMATION DU MODÈLE GRAVITAIRE")
    print("-" * 50)
    df = load_panel()
    comparison = compare_specifications(df)

    # ── Étape 3 : Potentiel commercial ──
    print("\n\n[3/4] CALCUL DU POTENTIEL COMMERCIAL")
    print("-" * 50)
    potential = calculate_trade_potential(df)

    # ── Étape 4 : Opportunités EDC ──
    print("\n\n[4/4] IDENTIFICATION DES OPPORTUNITÉS EDC")
    print("-" * 50)
    opportunities = identify_edc_opportunities(potential)

    # ── Résumé ──
    print("\n\n" + "=" * 70)
    print("  PIPELINE TERMINÉ")
    print("=" * 70)
    print(f"\n  Outputs générés dans : {OUTPUTS}/")
    print(f"    - model_comparison.csv   : comparaison OLS vs PPML")
    print(f"    - trade_potential.csv     : potentiel par pays")
    print(f"    - edc_opportunities.csv   : marchés prioritaires EDC")
    print(f"\n  Dashboard :")
    print(f"    streamlit run src/dashboard.py")


if __name__ == "__main__":
    main()
