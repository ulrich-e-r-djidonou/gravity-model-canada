"""
Analyse sectorielle — Potentiel commercial par secteur.

Décompose les exportations canadiennes en grandes catégories sectorielles
et identifie les opportunités par secteur × marché.

Secteurs (basés sur les sections HS) :
    - Énergie & ressources : HS 25-27 (minéraux, combustibles)
    - Agriculture & alimentation : HS 01-24
    - Produits chimiques : HS 28-38
    - Manufacturier de base : HS 39-83 (plastiques, métaux, textiles)
    - Machines & équipements : HS 84-85
    - Transport : HS 86-89
    - Haute technologie : HS 90-97 (instruments, optique, armes)

Usage :
    python src/sectors.py
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import requests
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_RAW, DATA_CLEAN, OUTPUTS, YEAR_START, YEAR_END
from src.data_download import _get_un_m49_mapping


# ──────────────────────────────────────────────
# Définition des secteurs
# ──────────────────────────────────────────────
SECTOR_MAP = {
    "Agriculture & alimentation": list(range(1, 25)),    # HS 01-24
    "Énergie & ressources": list(range(25, 28)),          # HS 25-27
    "Produits chimiques": list(range(28, 39)),             # HS 28-38
    "Manufacturier de base": list(range(39, 84)),          # HS 39-83
    "Machines & équipements": [84, 85],                    # HS 84-85
    "Transport": list(range(86, 90)),                      # HS 86-89
    "Haute technologie": list(range(90, 98)),              # HS 90-97
}

# Inverse : HS code → secteur
HS_TO_SECTOR = {}
for sector, codes in SECTOR_MAP.items():
    for code in codes:
        HS_TO_SECTOR[code] = sector


def download_sectoral_trade() -> pd.DataFrame:
    """
    Télécharge les exportations canadiennes par section HS (2 chiffres)
    via l'API Comtrade v2.

    Pour limiter les appels API, on télécharge seulement quelques années clés.
    """
    parquet_path = DATA_RAW / "trade_canada_sectoral.parquet"

    if parquet_path.exists():
        print(f"Données sectorielles déjà téléchargées : {parquet_path}")
        return pd.read_parquet(parquet_path)

    print("Téléchargement données sectorielles (Comtrade v2)...")

    base_url = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
    un_to_iso3 = _get_un_m49_mapping()

    # Années clés (limiter les appels — API preview = 500 records max)
    key_years = [2005, 2010, 2015, 2019]
    # Sections HS à 2 chiffres — on récupère les plus importants
    hs_sections = [
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "15", "17", "20", "22", "25", "26", "27",
        "28", "29", "30", "31", "32", "38", "39", "40", "44", "47", "48",
        "71", "72", "73", "74", "76", "84", "85", "86", "87", "88", "89",
        "90", "94",
    ]

    all_data = []
    for year in key_years:
        for hs in hs_sections:
            print(f"  {year} / HS{hs}...", end=" ", flush=True)
            try:
                resp = requests.get(base_url, params={
                    "reporterCode": "124",
                    "period": str(year),
                    "flowCode": "X",
                    "cmdCode": hs,
                }, timeout=30)

                if resp.status_code == 200:
                    records = resp.json().get("data", [])
                    count = 0
                    for r in records:
                        pc = r.get("partnerCode", 0)
                        val = r.get("primaryValue")
                        if pc and pc != 0 and val:
                            iso3 = un_to_iso3.get(pc)
                            if iso3:
                                all_data.append({
                                    "year": year,
                                    "iso3_d": iso3,
                                    "hs2": int(hs),
                                    "trade_value": float(val),
                                })
                                count += 1
                    print(f"{count}")
                else:
                    print(f"HTTP {resp.status_code}")
            except Exception as e:
                print(f"erreur: {e}")

            time.sleep(0.5)

    if not all_data:
        print("  Aucune donnée sectorielle récupérée.")
        return pd.DataFrame()

    result = pd.DataFrame(all_data)

    # Mapper HS2 → secteur
    result["sector"] = result["hs2"].map(HS_TO_SECTOR).fillna("Autre")

    # Agréger par secteur
    result_agg = result.groupby(
        ["year", "iso3_d", "sector"], as_index=False
    )["trade_value"].sum()

    result_agg.to_parquet(parquet_path, index=False)
    print(f"\n  Total : {len(result_agg):,} lignes")
    print(f"  Secteurs : {result_agg['sector'].nunique()}")
    return result_agg


def sectoral_analysis() -> pd.DataFrame:
    """
    Analyse sectorielle : potentiel par secteur × partenaire.

    Pour chaque secteur, estime un mini-modèle gravitaire et calcule
    le potentiel inexploité par pays.
    """
    print("\n=== Analyse sectorielle ===\n")

    # Charger les données
    trade_sec = download_sectoral_trade()
    if trade_sec.empty:
        return pd.DataFrame()

    gravity = pd.read_parquet(DATA_CLEAN / "gravity_panel.parquet")

    # Variables gravitaires (moyennes sur la période pour simplifier)
    grav_vars = gravity.groupby("iso3_d").agg({
        "dist": "first",
        "contig": "first",
        "comlang_off": "first",
        "rta": "first",
        "gdp_d": "mean",
        "pop_d": "mean",
    }).reset_index()

    grav_vars["ln_dist"] = np.log(grav_vars["dist"].clip(lower=1))
    grav_vars["ln_gdp_d"] = np.log(grav_vars["gdp_d"].clip(lower=1))
    grav_vars["ln_pop_d"] = np.log(grav_vars["pop_d"].clip(lower=1))

    # Résultats par secteur
    results = []

    for sector in trade_sec["sector"].unique():
        if sector == "Autre":
            continue

        sec_data = trade_sec[trade_sec["sector"] == sector].copy()

        # Flux moyen par partenaire
        sec_avg = sec_data.groupby("iso3_d", as_index=False)["trade_value"].mean()

        # Fusionner avec variables gravitaires
        sec_panel = sec_avg.merge(grav_vars, on="iso3_d", how="inner")
        sec_panel = sec_panel.dropna(subset=["ln_dist", "ln_gdp_d", "ln_pop_d"])

        if len(sec_panel) < 20:
            continue

        # PPML sectoriel
        X_vars = ["ln_dist", "ln_gdp_d", "ln_pop_d", "contig", "comlang_off", "rta"]
        X = sm.add_constant(sec_panel[X_vars].astype(float))
        y = sec_panel["trade_value"].astype(float)

        try:
            model = sm.GLM(y, X, family=sm.families.Poisson()).fit(
                cov_type="HC1", maxiter=100
            )
            sec_panel["predicted"] = model.predict(X)
            sec_panel["gap"] = sec_panel["predicted"] - sec_panel["trade_value"]
            sec_panel["ratio"] = sec_panel["predicted"] / sec_panel["trade_value"].clip(lower=1)
            sec_panel["sector"] = sector

            results.append(sec_panel[
                ["iso3_d", "sector", "trade_value", "predicted", "gap", "ratio", "gdp_d"]
            ])

            # Top 5 opportunités par secteur
            top5 = sec_panel.nlargest(5, "gap")
            print(f"\n{sector}:")
            print(f"  Modèle : N={int(model.nobs)}, "
                  f"Pseudo-R2={1-model.deviance/model.null_deviance:.3f}")
            for _, row in top5.iterrows():
                print(f"    {row['iso3_d']:5s}  "
                      f"Réel: ${row['trade_value']/1e6:8.1f}M  "
                      f"Prédit: ${row['predicted']/1e6:8.1f}M  "
                      f"Gap: +${row['gap']/1e6:6.1f}M")
        except Exception as e:
            print(f"  {sector}: Erreur d'estimation — {e}")
            continue

    if results:
        all_results = pd.concat(results, ignore_index=True)
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        all_results.to_csv(OUTPUTS / "sectoral_potential.csv", index=False)
        print(f"\nSauvegardé : {OUTPUTS / 'sectoral_potential.csv'}")

        # Résumé par secteur
        summary = all_results.groupby("sector").agg(
            total_gap=("gap", lambda x: x[x > 0].sum()),
            n_opportunities=("gap", lambda x: (x > 0).sum()),
            top_market=("gap", lambda x: x.idxmax()),
        ).sort_values("total_gap", ascending=False)

        print("\n=== Résumé sectoriel ===")
        print(f"{'Secteur':<30s} {'Gap total':>15s} {'N opportunités':>15s}")
        print("-" * 60)
        for sector, row in summary.iterrows():
            print(f"{sector:<30s} ${row['total_gap']/1e6:>12.0f}M {int(row['n_opportunities']):>13d}")

        return all_results

    return pd.DataFrame()


if __name__ == "__main__":
    sectoral_analysis()
