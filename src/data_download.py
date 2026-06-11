"""
Téléchargement des données pour le modèle gravitaire.

Sources :
1. USITC Dynamic Gravity Dataset — variables gravitaires (distance, langue, ALE, etc.)
2. UN Comtrade / IMF DOTS — flux commerciaux bilatéraux du Canada
3. World Bank (wbgapi) — PIB, population (complément si nécessaire)

Usage :
    python src/data_download.py
"""
import os
import zipfile
import requests
import pandas as pd
import numpy as np
import wbgapi as wb
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_RAW, DATA_CLEAN, YEAR_START, YEAR_END, CANADA_ISO3


def download_file(url: str, dest: Path, description: str = "") -> Path:
    """Télécharge un fichier avec barre de progression simple."""
    print(f"Téléchargement : {description or url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total and downloaded % (1024 * 1024) < 65536:  # Afficher chaque ~1MB
                pct = downloaded / total * 100
                print(f"\r  {pct:.0f}%", end="", flush=True)
    print(f"\n  Sauvegardé : {dest}")
    return dest


# ──────────────────────────────────────────────
# 1. USITC Dynamic Gravity Dataset
# ──────────────────────────────────────────────
def load_usitc_gravity() -> pd.DataFrame:
    """
    Charge le Dynamic Gravity Dataset (USITC), déjà téléchargé et fusionné.
    Si non disponible, le télécharge.

    Colonnes clés (noms USITC) :
        - distance : distance bilatérale (km)
        - contiguity : frontière commune (0/1)
        - common_language : langue commune (0/1)
        - colony_ever : lien colonial (0/1)
        - agree_fta : accord de libre-échange (0/1)
        - agree_pta : accord commercial préférentiel (0/1)
        - gdp_wdi_cur_o/d : PIB courant (WDI)
        - pop_o/d : population
    """
    parquet_path = DATA_RAW / "usitc_gravity_full.parquet"

    if parquet_path.exists():
        print(f"USITC Gravity déjà disponible : {parquet_path}")
        return pd.read_parquet(parquet_path)

    # Télécharger
    zip_path = DATA_RAW / "usitc_gravity.zip"
    url = "https://www.usitc.gov/data/gravity/dgd_docs/release_2.1_2000_2019.zip"
    download_file(url, zip_path, "USITC Dynamic Gravity Dataset v2.1 (2000-2019)")

    print("  Extraction du ZIP...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(DATA_RAW)

    # Fusionner tous les CSV extraits
    extracted_csvs = sorted(DATA_RAW.glob("release_*.csv"))
    print(f"  Fusion de {len(extracted_csvs)} fichiers CSV...")
    frames = []
    for csv_file in extracted_csvs:
        print(f"    {csv_file.name}")
        frames.append(pd.read_csv(csv_file, low_memory=False))
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["year", "iso3_o", "iso3_d"]).reset_index(drop=True)

    # Sauvegarder en parquet (beaucoup plus rapide à recharger)
    df.to_parquet(parquet_path, index=False)
    print(f"  USITC Gravity : {len(df):,} lignes, {df.shape[1]} colonnes")

    # Nettoyage
    for csv_file in extracted_csvs:
        csv_file.unlink(missing_ok=True)
    zip_path.unlink(missing_ok=True)
    # Supprimer les anciens CSV individuels
    for f in DATA_RAW.glob("usitc_gravity.csv"):
        f.unlink(missing_ok=True)

    return df


# ──────────────────────────────────────────────
# 2. World Bank — PIB et Population (complément)
# ──────────────────────────────────────────────
def download_worldbank_indicators() -> pd.DataFrame:
    """Télécharge PIB et population depuis la Banque mondiale (2000-2022)."""
    parquet_path = DATA_RAW / "wb_indicators.parquet"

    if parquet_path.exists():
        print(f"World Bank déjà téléchargé : {parquet_path}")
        return pd.read_parquet(parquet_path)

    indicators = {
        "NY.GDP.MKTP.CD": "gdp",
        "NY.GDP.PCAP.CD": "gdp_per_capita",
        "SP.POP.TOTL": "population",
    }

    print("Téléchargement World Bank (PIB, population)...")
    frames = []
    for code, name in indicators.items():
        print(f"  {name} ({code})...")
        df = wb.data.DataFrame(
            code,
            time=range(YEAR_START, YEAR_END + 1),
            labels=False,
            columns="time",
        )
        df = df.stack().reset_index()
        df.columns = ["iso3", "year", name]
        df["year"] = df["year"].str.replace("YR", "").astype(int)
        if len(frames) == 0:
            frames.append(df)
        else:
            frames[0] = frames[0].merge(df, on=["iso3", "year"], how="outer")

    result = frames[0]
    result.to_parquet(parquet_path, index=False)
    print(f"  World Bank : {len(result):,} lignes sauvegardées")
    return result


# ──────────────────────────────────────────────
# 3. Flux commerciaux — IMF DOTS
# ──────────────────────────────────────────────
def download_trade_data() -> pd.DataFrame:
    """
    Télécharge les flux commerciaux bilatéraux du Canada via
    l'API publique UN Comtrade v2 (pas de clé requise pour preview).
    """
    parquet_path = DATA_RAW / "trade_canada_exports.parquet"

    if parquet_path.exists():
        print(f"Données commerciales déjà téléchargées : {parquet_path}")
        return pd.read_parquet(parquet_path)

    print("Téléchargement UN Comtrade v2 — Exportations bilatérales du Canada...")

    base_url = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
    # Mapping UN M49 code → ISO3 (principaux pays)
    un_to_iso3 = _get_un_m49_mapping()

    all_data = []
    max_year = min(YEAR_END, 2019)  # USITC gravity va jusqu'à 2019
    import time

    for year in range(YEAR_START, max_year + 1):
        print(f"  {year}...", end=" ", flush=True)
        try:
            resp = requests.get(base_url, params={
                "reporterCode": "124",
                "period": str(year),
                "flowCode": "X",
                "cmdCode": "TOTAL",
            }, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                records = data.get("data", [])
                count = 0
                for r in records:
                    partner_code = r.get("partnerCode", 0)
                    val = r.get("primaryValue")
                    if partner_code and partner_code != 0 and val:
                        iso3 = un_to_iso3.get(partner_code)
                        if iso3:
                            all_data.append({
                                "year": year,
                                "iso3_d": iso3,
                                "trade_value": float(val),
                            })
                            count += 1
                print(f"{count} pays")
            else:
                print(f"HTTP {resp.status_code}")
        except Exception as e:
            print(f"erreur: {e}")

        time.sleep(1)  # Respecter les limites API

    if not all_data:
        print("  ERREUR : Aucune donnée récupérée.")
        return pd.DataFrame()

    result = pd.DataFrame(all_data)

    # Agréger si doublons (certains pays ont plusieurs entrées par mode de transport)
    result = result.groupby(["year", "iso3_d"], as_index=False)["trade_value"].sum()

    result.to_parquet(parquet_path, index=False)
    print(f"\n  Total : {len(result):,} lignes, "
          f"{result['iso3_d'].nunique()} partenaires")
    print(f"  Sauvegardé : {parquet_path}")
    return result


def _get_un_m49_mapping() -> dict:
    """Retourne un mapping UN M49 numeric code → ISO3 alpha-3."""
    return {
        4: "AFG", 8: "ALB", 12: "DZA", 20: "AND", 24: "AGO", 28: "ATG",
        32: "ARG", 51: "ARM", 36: "AUS", 40: "AUT", 31: "AZE", 44: "BHS",
        48: "BHR", 50: "BGD", 52: "BRB", 112: "BLR", 56: "BEL", 84: "BLZ",
        204: "BEN", 64: "BTN", 68: "BOL", 70: "BIH", 72: "BWA", 76: "BRA",
        96: "BRN", 100: "BGR", 854: "BFA", 108: "BDI", 116: "KHM",
        120: "CMR", 124: "CAN", 132: "CPV", 140: "CAF", 148: "TCD",
        152: "CHL", 156: "CHN", 170: "COL", 174: "COM", 178: "COG",
        180: "COD", 188: "CRI", 384: "CIV", 191: "HRV", 192: "CUB",
        196: "CYP", 203: "CZE", 208: "DNK", 262: "DJI", 212: "DMA",
        214: "DOM", 218: "ECU", 818: "EGY", 222: "SLV", 226: "GNQ",
        232: "ERI", 233: "EST", 231: "ETH", 242: "FJI", 246: "FIN",
        250: "FRA", 266: "GAB", 270: "GMB", 268: "GEO", 276: "DEU",
        288: "GHA", 300: "GRC", 308: "GRD", 320: "GTM", 324: "GIN",
        328: "GUY", 332: "HTI", 340: "HND", 348: "HUN", 352: "ISL",
        356: "IND", 360: "IDN", 364: "IRN", 368: "IRQ", 372: "IRL",
        376: "ISR", 380: "ITA", 388: "JAM", 392: "JPN", 400: "JOR",
        398: "KAZ", 404: "KEN", 296: "KIR", 408: "PRK", 410: "KOR",
        414: "KWT", 417: "KGZ", 418: "LAO", 428: "LVA", 422: "LBN",
        426: "LSO", 430: "LBR", 434: "LBY", 440: "LTU", 442: "LUX",
        450: "MDG", 454: "MWI", 458: "MYS", 462: "MDV", 466: "MLI",
        470: "MLT", 480: "MUS", 484: "MEX", 498: "MDA", 496: "MNG",
        499: "MNE", 504: "MAR", 508: "MOZ", 104: "MMR", 516: "NAM",
        524: "NPL", 528: "NLD", 554: "NZL", 558: "NIC", 562: "NER",
        566: "NGA", 578: "NOR", 512: "OMN", 586: "PAK", 591: "PAN",
        598: "PNG", 600: "PRY", 604: "PER", 608: "PHL", 616: "POL",
        620: "PRT", 634: "QAT", 642: "ROU", 643: "RUS", 646: "RWA",
        662: "LCA", 670: "VCT", 882: "WSM", 682: "SAU", 686: "SEN",
        688: "SRB", 690: "SYC", 694: "SLE", 702: "SGP", 703: "SVK",
        705: "SVN", 90: "SLB", 706: "SOM", 710: "ZAF", 724: "ESP",
        144: "LKA", 736: "SDN", 740: "SUR", 748: "SWZ", 752: "SWE",
        756: "CHE", 760: "SYR", 158: "TWN", 762: "TJK", 834: "TZA",
        764: "THA", 626: "TLS", 768: "TGO", 776: "TON", 780: "TTO",
        788: "TUN", 792: "TUR", 795: "TKM", 800: "UGA", 804: "UKR",
        784: "ARE", 826: "GBR", 840: "USA", 858: "URY", 860: "UZB",
        548: "VUT", 862: "VEN", 704: "VNM", 887: "YEM", 894: "ZMB",
        716: "ZWE",
        # Territoires et régions spéciales
        344: "HKG", 446: "MAC", 530: "ANT", 533: "ABW",
        60: "BMU", 136: "CYM", 254: "GUF", 258: "PYF",
        304: "GRL", 312: "GLP", 474: "MTQ", 540: "NCL",
        638: "REU", 796: "TCA", 850: "VIR", 92: "VGB",
        # Variantes de codes utilisées par Comtrade
        842: "USA",  # USA (variante Comtrade)
        251: "FRA",  # France métropolitaine (variante)
        757: "CHE",  # Suisse (variante)
        699: "IND",  # Inde (variante ancienne)
        757: "CHE",
    }


# ──────────────────────────────────────────────
# 4. Mapping codes IMF → ISO3
# ──────────────────────────────────────────────

# Mapping partiel IMF country codes → ISO3 (les plus importants)
IMF_TO_ISO3 = {
    "US": "USA", "GB": "GBR", "DE": "DEU", "FR": "FRA", "JP": "JPN",
    "CN": "CHN", "IN": "IND", "BR": "BRA", "MX": "MEX", "KR": "KOR",
    "AU": "AUS", "IT": "ITA", "ES": "ESP", "NL": "NLD", "BE": "BEL",
    "CH": "CHE", "SE": "SWE", "NO": "NOR", "DK": "DNK", "FI": "FIN",
    "AT": "AUT", "IE": "IRL", "PT": "PRT", "GR": "GRC", "PL": "POL",
    "CZ": "CZE", "HU": "HUN", "RO": "ROU", "BG": "BGR", "HR": "HRV",
    "RU": "RUS", "UA": "UKR", "TR": "TUR", "SA": "SAU", "AE": "ARE",
    "IL": "ISR", "EG": "EGY", "ZA": "ZAF", "NG": "NGA", "KE": "KEN",
    "GH": "GHA", "TZ": "TZA", "ET": "ETH", "CI": "CIV", "SN": "SEN",
    "TH": "THA", "VN": "VNM", "ID": "IDN", "MY": "MYS", "SG": "SGP",
    "PH": "PHL", "PK": "PAK", "BD": "BGD", "LK": "LKA", "NZ": "NZL",
    "CL": "CHL", "CO": "COL", "PE": "PER", "AR": "ARG", "VE": "VEN",
    "EC": "ECU", "UY": "URY", "PA": "PAN", "CR": "CRI", "DO": "DOM",
    "GT": "GTM", "HN": "HND", "SV": "SLV", "NI": "NIC", "JM": "JAM",
    "TT": "TTO", "BB": "BRB", "BS": "BHS", "HT": "HTI", "CU": "CUB",
    "MA": "MAR", "TN": "TUN", "DZ": "DZA", "LY": "LBY", "IQ": "IRQ",
    "IR": "IRN", "KW": "KWT", "QA": "QAT", "BH": "BHR", "OM": "OMN",
    "JO": "JOR", "LB": "LBN", "TW": "TWN", "HK": "HKG", "MO": "MAC",
    "MM": "MMR", "KH": "KHM", "LA": "LAO", "NP": "NPL", "AF": "AFG",
    "KZ": "KAZ", "UZ": "UZB", "GE": "GEO", "AZ": "AZE", "AM": "ARM",
    "RS": "SRB", "BA": "BIH", "MK": "MKD", "AL": "ALB", "ME": "MNE",
    "SI": "SVN", "SK": "SVK", "LT": "LTU", "LV": "LVA", "EE": "EST",
    "BY": "BLR", "MD": "MDA", "IS": "ISL", "LU": "LUX", "MT": "MLT",
    "CY": "CYP",
}


# ──────────────────────────────────────────────
# 5. Assemblage du panel
# ──────────────────────────────────────────────
def build_gravity_panel() -> pd.DataFrame:
    """
    Assemble toutes les sources en un panel prêt pour l'estimation.

    Structure finale :
        - year, iso3_o (CAN), iso3_d (partenaire)
        - trade_value : exportations Canada → partenaire (USD)
        - distance, contiguity, common_language, colony_ever
        - agree_fta, agree_pta : accords commerciaux
        - gdp_o, gdp_d, pop_o, pop_d : fondamentaux économiques
    """
    parquet_path = DATA_CLEAN / "gravity_panel.parquet"

    if parquet_path.exists():
        print(f"Panel déjà construit : {parquet_path}")
        return pd.read_parquet(parquet_path)

    print("\n=== Construction du panel gravitaire ===\n")

    # 1. Variables gravitaires (USITC)
    gravity = load_usitc_gravity()

    # Filtrer : Canada comme exportateur, exclure les paires CAN-CAN
    gravity_can = gravity[
        (gravity["iso3_o"] == CANADA_ISO3) &
        (gravity["iso3_d"] != CANADA_ISO3) &
        (gravity["year"] >= YEAR_START) &
        (gravity["year"] <= min(YEAR_END, gravity["year"].max()))
    ].copy()

    print(f"  Gravity (Canada) : {len(gravity_can):,} lignes, "
          f"{gravity_can['iso3_d'].nunique()} partenaires, "
          f"années {gravity_can['year'].min()}-{gravity_can['year'].max()}")

    # Renommer les colonnes USITC vers nos noms standardisés
    gravity_can = gravity_can.rename(columns={
        "distance": "dist",
        "contiguity": "contig",
        "common_language": "comlang_off",
        "colony_ever": "comcol",
        "agree_fta": "fta",
        "agree_pta": "rta",  # RTA = Regional Trade Agreement (inclut PTA)
        "gdp_wdi_cur_o": "gdp_o",
        "gdp_wdi_cur_d": "gdp_d",
        "gdp_wdi_cap_cur_d": "gdp_pc_d",
        "gdp_wdi_cap_cur_o": "gdp_pc_o",
    })

    # 2. Flux commerciaux
    trade = download_trade_data()

    if trade.empty:
        print("ERREUR : Pas de données commerciales.")
        return pd.DataFrame()

    # Les données Comtrade v2 ont déjà iso3_d
    if "iso3_d" not in trade.columns and "partner_imf" in trade.columns:
        trade["iso3_d"] = trade["partner_imf"].map(IMF_TO_ISO3)
        trade = trade.dropna(subset=["iso3_d"])
    print(f"  Trade : {len(trade):,} lignes, {trade['iso3_d'].nunique()} partenaires")

    # 3. Fusion gravity + trade
    print("  Fusion gravity + trade...")
    panel = gravity_can.merge(
        trade[["year", "iso3_d", "trade_value"]],
        on=["year", "iso3_d"],
        how="left",
    )

    # Remplir les flux manquants par 0 (important pour PPML)
    panel["trade_value"] = panel["trade_value"].fillna(0)

    # Garder les colonnes utiles
    keep_cols = [
        "year", "iso3_o", "iso3_d", "country_o", "country_d",
        "trade_value", "dist", "contig", "comlang_off", "comcol",
        "fta", "rta",
        "gdp_o", "gdp_d", "gdp_pc_o", "gdp_pc_d",
        "pop_o", "pop_d",
        "member_wto_joint", "member_eu_joint",
    ]
    # Ne garder que les colonnes qui existent
    keep_cols = [c for c in keep_cols if c in panel.columns]
    panel = panel[keep_cols].copy()

    # Supprimer les lignes sans distance (paires invalides)
    panel = panel.dropna(subset=["dist"])

    # Sauvegarder
    DATA_CLEAN.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(parquet_path, index=False)

    n_with_trade = (panel["trade_value"] > 0).sum()
    print(f"\n  Panel final : {len(panel):,} lignes x {panel.shape[1]} colonnes")
    print(f"  Avec flux > 0 : {n_with_trade:,} ({n_with_trade/len(panel)*100:.0f}%)")
    print(f"  Années : {panel['year'].min()}-{panel['year'].max()}")
    print(f"  Partenaires : {panel['iso3_d'].nunique()}")
    print(f"  Sauvegardé : {parquet_path}")

    return panel


if __name__ == "__main__":
    panel = build_gravity_panel()
    if not panel.empty:
        print("\n=== Aperçu ===")
        print(panel.describe().to_string())
        print(f"\nTop 10 partenaires (par flux moyen) :")
        top = panel.groupby("iso3_d")["trade_value"].mean().nlargest(10)
        for iso, val in top.items():
            print(f"  {iso}: ${val/1e9:.1f}B")
