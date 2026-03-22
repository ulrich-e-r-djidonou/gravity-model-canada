"""
Script de mise a jour des donnees.

Rafraichit les donnees commerciales et reconstruit le panel
quand de nouvelles annees sont disponibles sur Comtrade.

Usage :
    python src/update_data.py              # Mise a jour complete
    python src/update_data.py --check      # Verifier si nouvelles donnees disponibles
    python src/update_data.py --year 2023  # Ajouter une annee specifique
"""
import argparse
import requests
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_RAW, DATA_CLEAN, OUTPUTS, YEAR_START
from src.data_download import _get_un_m49_mapping


def check_latest_year() -> int:
    """Verifie la derniere annee disponible sur Comtrade."""
    print("Verification des donnees disponibles sur Comtrade...")

    for year in range(2025, 2019, -1):
        try:
            resp = requests.get(
                "https://comtradeapi.un.org/public/v1/preview/C/A/HS",
                params={
                    "reporterCode": "124",
                    "period": str(year),
                    "flowCode": "X",
                    "cmdCode": "TOTAL",
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if len(data) > 10:
                    print(f"  Derniere annee disponible : {year} ({len(data)} partenaires)")
                    return year
        except Exception:
            continue

    print("  Impossible de determiner la derniere annee disponible.")
    return 0


def get_current_coverage() -> set:
    """Retourne les annees deja dans le panel."""
    parquet_path = DATA_RAW / "trade_canada_exports.parquet"
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        years = set(df["year"].unique())
        print(f"  Panel actuel : {min(years)}-{max(years)} ({len(years)} annees)")
        return years
    return set()


def download_year(year: int) -> pd.DataFrame:
    """Telecharge les exportations canadiennes pour une annee donnee."""
    print(f"  Telechargement {year}...", end=" ", flush=True)

    un_to_iso3 = _get_un_m49_mapping()
    all_data = []

    try:
        resp = requests.get(
            "https://comtradeapi.un.org/public/v1/preview/C/A/HS",
            params={
                "reporterCode": "124",
                "period": str(year),
                "flowCode": "X",
                "cmdCode": "TOTAL",
            },
            timeout=30,
        )

        if resp.status_code == 200:
            records = resp.json().get("data", [])
            for r in records:
                pc = r.get("partnerCode", 0)
                val = r.get("primaryValue")
                if pc and pc != 0 and val:
                    iso3 = un_to_iso3.get(pc)
                    if iso3:
                        all_data.append({
                            "year": year,
                            "iso3_d": iso3,
                            "trade_value": float(val),
                        })
            print(f"{len(all_data)} pays")
    except Exception as e:
        print(f"erreur: {e}")

    return pd.DataFrame(all_data)


def update_trade_data(new_years: list) -> pd.DataFrame:
    """Ajoute de nouvelles annees au dataset existant."""
    parquet_path = DATA_RAW / "trade_canada_exports.parquet"

    if parquet_path.exists():
        existing = pd.read_parquet(parquet_path)
    else:
        existing = pd.DataFrame()

    new_frames = []
    for year in new_years:
        df_year = download_year(year)
        if not df_year.empty:
            # Agreger doublons
            df_year = df_year.groupby(
                ["year", "iso3_d"], as_index=False
            )["trade_value"].sum()
            new_frames.append(df_year)
        time.sleep(1)

    if new_frames:
        new_data = pd.concat(new_frames, ignore_index=True)
        if not existing.empty:
            # Supprimer les anciennes donnees pour ces annees (au cas ou)
            existing = existing[~existing["year"].isin(new_years)]
            result = pd.concat([existing, new_data], ignore_index=True)
        else:
            result = new_data

        result = result.sort_values(["year", "iso3_d"]).reset_index(drop=True)
        result.to_parquet(parquet_path, index=False)
        print(f"\n  Dataset mis a jour : {len(result):,} lignes, "
              f"{result['year'].min()}-{result['year'].max()}")
        return result

    print("  Aucune nouvelle donnee a ajouter.")
    return existing if not existing.empty else pd.DataFrame()


def rebuild_panel():
    """Reconstruit le panel gravitaire apres mise a jour."""
    panel_path = DATA_CLEAN / "gravity_panel.parquet"
    if panel_path.exists():
        panel_path.unlink()
        print("  Panel supprime, reconstruction...")

    from src.data_download import build_gravity_panel
    return build_gravity_panel()


def rebuild_outputs():
    """Relance les analyses apres mise a jour du panel."""
    print("\n=== Reconstruction des analyses ===")

    df = pd.read_parquet(DATA_CLEAN / "gravity_panel.parquet")
    df["ln_dist"] = np.log(df["dist"].clip(lower=1))
    df["ln_gdp_d"] = np.log(df["gdp_d"].clip(lower=1))
    df["ln_pop_d"] = np.log(df["pop_d"].clip(lower=1))

    from src.potential import calculate_trade_potential, identify_edc_opportunities
    potential = calculate_trade_potential(df)
    identify_edc_opportunities(potential)

    from src.counterfactual import run_all_scenarios
    run_all_scenarios()

    print("\n  Tous les outputs ont ete regeneres.")


def main():
    parser = argparse.ArgumentParser(description="Mise a jour des donnees commerciales")
    parser.add_argument("--check", action="store_true", help="Verifier sans telecharger")
    parser.add_argument("--year", type=int, help="Ajouter une annee specifique")
    parser.add_argument("--rebuild", action="store_true", help="Reconstruire le panel et les analyses")
    args = parser.parse_args()

    print("=" * 60)
    print("  MISE A JOUR DES DONNEES COMMERCIALES")
    print("=" * 60)

    current_years = get_current_coverage()
    latest = check_latest_year()

    if args.check:
        missing = set(range(YEAR_START, latest + 1)) - current_years
        if missing:
            print(f"\n  Annees manquantes : {sorted(missing)}")
            print(f"  Lancez : python src/update_data.py")
        else:
            print("\n  Donnees a jour.")
        return

    if args.year:
        new_years = [args.year]
    else:
        new_years = sorted(set(range(YEAR_START, latest + 1)) - current_years)

    if new_years:
        print(f"\n  Annees a telecharger : {new_years}")
        update_trade_data(new_years)
        rebuild_panel()
        if args.rebuild:
            rebuild_outputs()
    else:
        print("\n  Aucune nouvelle annee a ajouter.")
        if args.rebuild:
            rebuild_outputs()


if __name__ == "__main__":
    main()
