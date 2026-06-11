"""
Calcul du potentiel commercial — Marchés sous-exploités pour le Canada.

Logique :
    1. Estimer le modèle gravitaire (flux prédit par la gravité)
    2. Comparer flux réel vs flux prédit
    3. Si réel < prédit → marché sous-exploité (opportunité)
    4. Si réel > prédit → marché sur-exploité (dépendance)

Indicateur clé :
    Trade Potential Ratio = Prédit / Réel
    > 1 → opportunité inexploitée
    < 1 → commerce supérieur aux fondamentaux

Usage :
    python src/potential.py
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_CLEAN, OUTPUTS


def calculate_trade_potential(
    df: pd.DataFrame,
    model_results=None,
) -> pd.DataFrame:
    """
    Calcule le potentiel commercial pour chaque partenaire du Canada.

    Returns:
        DataFrame avec colonnes :
        - iso3_d : code pays partenaire
        - country_name : nom du pays
        - trade_actual : exportations réelles (moyenne sur la période)
        - trade_predicted : exportations prédites par le modèle
        - potential_ratio : prédit / réel
        - gap_usd : prédit - réel (en USD)
        - classification : sous-exploité / équilibre / sur-exploité
    """
    print("=== Calcul du potentiel commercial ===\n")

    # Si pas de modèle fourni, estimer un PPML de base
    if model_results is None:
        X_vars = ["ln_dist", "ln_gdp_d", "ln_pop_d", "contig", "comlang_off", "rta"]

        df_est = df.dropna(subset=X_vars + ["trade_value"]).copy()
        X = sm.add_constant(df_est[X_vars].astype(float))
        y = df_est["trade_value"].astype(float)

        model_results = sm.GLM(y, X, family=sm.families.Poisson()).fit(
            cov_type="HC1", maxiter=100
        )
        df_est["trade_predicted"] = model_results.predict(X)
    else:
        df_est = df.copy()
        df_est["trade_predicted"] = model_results.predict()

    # Agrégation par partenaire (moyenne sur toutes les années)
    potential = df_est.groupby("iso3_d").agg(
        trade_actual=("trade_value", "mean"),
        trade_predicted=("trade_predicted", "mean"),
        n_years=("year", "nunique"),
        gdp_d_last=("gdp_d", "last"),
    ).reset_index()

    # Calcul des indicateurs
    potential["potential_ratio"] = potential["trade_predicted"] / potential["trade_actual"].clip(lower=1)
    potential["gap_usd"] = potential["trade_predicted"] - potential["trade_actual"]
    potential["gap_pct"] = (potential["gap_usd"] / potential["trade_actual"].clip(lower=1)) * 100

    # Classification
    potential["classification"] = pd.cut(
        potential["potential_ratio"],
        bins=[0, 0.75, 1.25, float("inf")],
        labels=["Sur-exploité", "Équilibre", "Sous-exploité"],
    )

    # Tri par potentiel inexploité (gap_usd décroissant)
    potential = potential.sort_values("gap_usd", ascending=False)

    # Affichage
    print("TOP 20 — Marchés sous-exploités (opportunités) :")
    print("-" * 80)
    top = potential[potential["gap_usd"] > 0].head(20)
    for _, row in top.iterrows():
        gap_m = row["gap_usd"] / 1e6
        print(
            f"  {row['iso3_d']:5s}  "
            f"Réel: ${row['trade_actual']/1e6:8.1f}M  "
            f"Prédit: ${row['trade_predicted']/1e6:8.1f}M  "
            f"Gap: +${gap_m:8.1f}M  "
            f"Ratio: {row['potential_ratio']:.2f}"
        )

    print(f"\n\nTOP 10 — Marchés sur-exploités (dépendance) :")
    print("-" * 80)
    bottom = potential[potential["gap_usd"] < 0].tail(10)
    for _, row in bottom.iterrows():
        gap_m = row["gap_usd"] / 1e6
        print(
            f"  {row['iso3_d']:5s}  "
            f"Réel: ${row['trade_actual']/1e6:8.1f}M  "
            f"Prédit: ${row['trade_predicted']/1e6:8.1f}M  "
            f"Gap: ${gap_m:8.1f}M  "
            f"Ratio: {row['potential_ratio']:.2f}"
        )

    # Résumé
    n_under = (potential["classification"] == "Sous-exploité").sum()
    n_over = (potential["classification"] == "Sur-exploité").sum()
    n_eq = (potential["classification"] == "Équilibre").sum()
    print(f"\nRésumé : {n_under} sous-exploités | {n_eq} en équilibre | {n_over} sur-exploités")

    # Sauvegarder
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    potential.to_csv(OUTPUTS / "trade_potential.csv", index=False)
    print(f"Sauvegardé : {OUTPUTS / 'trade_potential.csv'}")

    return potential


def identify_edc_opportunities(potential: pd.DataFrame) -> pd.DataFrame:
    """
    Filtre les opportunités pertinentes pour EDC :
    - Marchés émergents (pas OCDE classique)
    - Gap positif significatif
    - PIB suffisant pour justifier l'intérêt commercial

    C'est exactement ce que l'équipe DREAM fait pour identifier
    les marchés prioritaires pour les exportateurs canadiens.
    """
    # Pays OCDE (à exclure pour focus marchés émergents)
    oecd_core = {
        "USA", "GBR", "FRA", "DEU", "JPN", "ITA", "AUS", "NZL",
        "NLD", "BEL", "CHE", "AUT", "SWE", "NOR", "DNK", "FIN",
        "IRL", "ISL", "LUX", "ESP", "PRT",
    }

    opportunities = potential[
        (~potential["iso3_d"].isin(oecd_core)) &
        (potential["gap_usd"] > 0) &
        (potential["gdp_d_last"] > 1e10)  # PIB > 10 milliards USD
    ].copy()

    opportunities["priority_score"] = (
        opportunities["gap_usd"].rank(ascending=False, pct=True) * 0.5 +
        opportunities["gdp_d_last"].rank(ascending=False, pct=True) * 0.3 +
        opportunities["potential_ratio"].rank(ascending=False, pct=True) * 0.2
    )
    opportunities = opportunities.sort_values("priority_score", ascending=False)

    print("\n=== Opportunités EDC — Marchés émergents prioritaires ===")
    print("-" * 80)
    for i, (_, row) in enumerate(opportunities.head(15).iterrows(), 1):
        print(
            f"  {i:2d}. {row['iso3_d']:5s}  "
            f"Gap: +${row['gap_usd']/1e6:.0f}M  "
            f"PIB: ${row['gdp_d_last']/1e9:.0f}B  "
            f"Score: {row['priority_score']:.2f}"
        )

    opportunities.to_csv(OUTPUTS / "edc_opportunities.csv", index=False)
    print(f"\nSauvegardé : {OUTPUTS / 'edc_opportunities.csv'}")

    return opportunities


if __name__ == "__main__":
    df = pd.read_parquet(DATA_CLEAN / "gravity_panel.parquet")

    # Préparer les variables
    df["ln_dist"] = np.log(df["dist"].clip(lower=1))
    df["ln_gdp_d"] = np.log(df["gdp_d"].clip(lower=1))
    df["ln_pop_d"] = np.log(df["pop_d"].clip(lower=1))

    potential = calculate_trade_potential(df)
    opportunities = identify_edc_opportunities(potential)
