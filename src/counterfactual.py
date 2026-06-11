"""
Scénarios contrefactuels — Simulation d'impacts sur les exportations canadiennes.

Permet de simuler :
    1. Nouvel ALE (accord de libre-échange) avec un pays ou une région
    2. Sanctions commerciales (réduction ou arrêt des échanges)
    3. Choc de PIB (croissance ou récession chez un partenaire)
    4. Nouveau corridor logistique (réduction de la distance effective)

Méthodologie :
    - Estimer le modèle gravitaire de base
    - Modifier les variables d'intérêt (rta, gdp_d, dist)
    - Recalculer les flux prédits sous le nouveau scénario
    - Comparer avec le scénario de base (baseline)

Usage :
    python src/counterfactual.py
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_CLEAN, OUTPUTS


def load_and_estimate_baseline():
    """Charge le panel et estime le modèle PPML de base."""
    df = pd.read_parquet(DATA_CLEAN / "gravity_panel.parquet")

    # Combler les NaN de gdp_d et pop_d avec les données World Bank si nécessaire
    from config import DATA_RAW
    wb = pd.read_parquet(DATA_RAW / "wb_indicators.parquet")
    wb = wb.rename(columns={"iso3": "iso3_d", "gdp": "gdp_wb", "population": "pop_wb"})
    df = df.merge(wb[["iso3_d", "year", "gdp_wb", "pop_wb"]], on=["iso3_d", "year"], how="left")
    df["gdp_d"] = df["gdp_d"].fillna(df["gdp_wb"])
    df["pop_d"] = df["pop_d"].fillna(df["pop_wb"])
    df = df.drop(columns=["gdp_wb", "pop_wb"], errors="ignore")

    df["ln_dist"] = np.log(df["dist"].clip(lower=1))
    df["ln_gdp_d"] = np.log(df["gdp_d"].clip(lower=1))
    df["ln_pop_d"] = np.log(df["pop_d"].clip(lower=1))

    # Utiliser la dernière année avec assez de données
    last_year = df["year"].max()
    df_base = df[df["year"] == last_year].copy()
    df_base = df_base.dropna(subset=["ln_dist", "ln_gdp_d", "ln_pop_d"])

    # Si trop peu de données, utiliser toutes les années (cross-section empilée)
    if len(df_base) < 50:
        print(f"  Année {last_year} : {len(df_base)} obs. Utilisation du panel moyen...")
        df_base = df.groupby("iso3_d").agg({
            "trade_value": "mean", "dist": "first", "contig": "first",
            "comlang_off": "first", "rta": "last", "gdp_d": "mean",
            "pop_d": "mean", "iso3_o": "first", "country_d": "first",
        }).reset_index()
        df_base["ln_dist"] = np.log(df_base["dist"].clip(lower=1))
        df_base["ln_gdp_d"] = np.log(df_base["gdp_d"].clip(lower=1))
        df_base["ln_pop_d"] = np.log(df_base["pop_d"].clip(lower=1))
        df_base = df_base.dropna(subset=["ln_dist", "ln_gdp_d", "ln_pop_d"])

    X_vars = ["ln_dist", "ln_gdp_d", "ln_pop_d", "contig", "comlang_off", "rta"]
    X = sm.add_constant(df_base[X_vars].astype(float))
    y = df_base["trade_value"].astype(float)

    model = sm.GLM(y, X, family=sm.families.Poisson()).fit(
        cov_type="HC1", maxiter=100
    )

    df_base["trade_baseline"] = model.predict(X)

    return df_base, model, X_vars


def scenario_new_fta(
    df_base: pd.DataFrame,
    model,
    X_vars: list,
    target_countries: list,
    scenario_name: str = "Nouvel ALE",
) -> pd.DataFrame:
    """
    Scénario : Signature d'un nouvel ALE avec un ou plusieurs pays.

    Effet : rta passe de 0 à 1 pour les pays ciblés.
    """
    print(f"\n=== Scénario : {scenario_name} ===")
    print(f"  Pays ciblés : {', '.join(target_countries)}")

    df_scenario = df_base.copy()

    # Modifier RTA pour les pays ciblés
    mask = df_scenario["iso3_d"].isin(target_countries)
    already_fta = df_scenario.loc[mask, "rta"].sum()
    df_scenario.loc[mask, "rta"] = 1

    # Recalculer les flux prédits
    X_new = sm.add_constant(df_scenario[X_vars].astype(float))
    df_scenario["trade_scenario"] = model.predict(X_new)
    df_scenario["impact"] = df_scenario["trade_scenario"] - df_scenario["trade_baseline"]
    df_scenario["impact_pct"] = (
        df_scenario["impact"] / df_scenario["trade_baseline"].clip(lower=1) * 100
    )

    # Résultats pour les pays ciblés
    affected = df_scenario[mask].copy()
    total_impact = affected["impact"].sum()

    print(f"  Pays déjà avec ALE : {int(already_fta)}/{len(target_countries)}")
    print(f"  Impact total estimé : +${total_impact/1e6:,.0f}M")
    print(f"\n  Détail par pays :")
    for _, row in affected.sort_values("impact", ascending=False).iterrows():
        if row["impact"] > 0:
            print(
                f"    {row['iso3_d']:5s}  "
                f"Base: ${row['trade_baseline']/1e6:8.1f}M → "
                f"Scénario: ${row['trade_scenario']/1e6:8.1f}M  "
                f"(+${row['impact']/1e6:6.1f}M, +{row['impact_pct']:.1f}%)"
            )

    return df_scenario


def scenario_sanctions(
    df_base: pd.DataFrame,
    model,
    X_vars: list,
    target_countries: list,
    reduction_pct: float = 80.0,
    scenario_name: str = "Sanctions commerciales",
) -> pd.DataFrame:
    """
    Scénario : Sanctions réduisant le commerce avec certains pays.

    Effet : Les flux prédits sont réduits du pourcentage indiqué.
    On simule ça comme un choc négatif sur le PIB du partenaire
    (car dans le modèle gravitaire, les sanctions agissent via
    les résistances multilatérales, qu'on approxime par le PIB).
    """
    print(f"\n=== Scénario : {scenario_name} ===")
    print(f"  Pays sanctionnés : {', '.join(target_countries)}")
    print(f"  Réduction estimée : {reduction_pct}%")

    df_scenario = df_base.copy()

    mask = df_scenario["iso3_d"].isin(target_countries)

    # Simuler les sanctions comme un choc négatif sur ln_gdp_d
    # reduction_pct% de réduction du commerce ≈ ln(1-reduction/100) sur le GDP
    shock_factor = np.log(1 - reduction_pct / 100)
    df_scenario.loc[mask, "ln_gdp_d"] = (
        df_scenario.loc[mask, "ln_gdp_d"] + shock_factor
    )

    # Aussi retirer l'ALE si existant
    df_scenario.loc[mask, "rta"] = 0

    # Recalculer
    X_new = sm.add_constant(df_scenario[X_vars].astype(float))
    df_scenario["trade_scenario"] = model.predict(X_new)
    df_scenario["impact"] = df_scenario["trade_scenario"] - df_scenario["trade_baseline"]
    df_scenario["impact_pct"] = (
        df_scenario["impact"] / df_scenario["trade_baseline"].clip(lower=1) * 100
    )

    # Résultats
    affected = df_scenario[mask].copy()
    total_loss = affected["impact"].sum()

    print(f"  Perte totale estimée : ${total_loss/1e6:,.0f}M")
    print(f"\n  Détail :")
    for _, row in affected.sort_values("impact").iterrows():
        print(
            f"    {row['iso3_d']:5s}  "
            f"Base: ${row['trade_baseline']/1e6:8.1f}M → "
            f"Scénario: ${row['trade_scenario']/1e6:8.1f}M  "
            f"(${row['impact']/1e6:7.1f}M, {row['impact_pct']:+.1f}%)"
        )

    # Effet de diversion : quels pays en bénéficient ?
    non_affected = df_scenario[~mask & (df_scenario["trade_baseline"] > 0)].copy()
    print(f"\n  Marchés de substitution potentiels :")
    substitutes = non_affected.nlargest(10, "trade_baseline")
    for _, row in substitutes.iterrows():
        print(f"    {row['iso3_d']:5s}  Flux actuel: ${row['trade_baseline']/1e6:8.1f}M")

    return df_scenario


def scenario_gdp_shock(
    df_base: pd.DataFrame,
    model,
    X_vars: list,
    target_countries: list,
    gdp_change_pct: float = 10.0,
    scenario_name: str = "Choc de PIB",
) -> pd.DataFrame:
    """
    Scénario : Croissance/récession chez un partenaire commercial.

    Effet : Le PIB du partenaire augmente/diminue de X%.
    """
    print(f"\n=== Scénario : {scenario_name} ===")
    print(f"  Pays : {', '.join(target_countries)}")
    print(f"  Variation PIB : {gdp_change_pct:+.1f}%")

    df_scenario = df_base.copy()

    mask = df_scenario["iso3_d"].isin(target_countries)
    df_scenario.loc[mask, "ln_gdp_d"] = (
        df_scenario.loc[mask, "ln_gdp_d"] + np.log(1 + gdp_change_pct / 100)
    )

    X_new = sm.add_constant(df_scenario[X_vars].astype(float))
    df_scenario["trade_scenario"] = model.predict(X_new)
    df_scenario["impact"] = df_scenario["trade_scenario"] - df_scenario["trade_baseline"]
    df_scenario["impact_pct"] = (
        df_scenario["impact"] / df_scenario["trade_baseline"].clip(lower=1) * 100
    )

    affected = df_scenario[mask].copy()
    total_impact = affected["impact"].sum()
    direction = "gain" if gdp_change_pct > 0 else "perte"

    print(f"  Impact total : {'+' if total_impact > 0 else ''}${total_impact/1e6:,.0f}M ({direction})")
    for _, row in affected.sort_values("impact", ascending=False).iterrows():
        print(
            f"    {row['iso3_d']:5s}  "
            f"Base: ${row['trade_baseline']/1e6:8.1f}M → "
            f"Scénario: ${row['trade_scenario']/1e6:8.1f}M  "
            f"({'+' if row['impact'] > 0 else ''}${row['impact']/1e6:6.1f}M)"
        )

    return df_scenario


def run_all_scenarios() -> dict:
    """
    Exécute une batterie de scénarios pertinents pour EDC.
    """
    print("=" * 70)
    print("  SCÉNARIOS CONTREFACTUELS — EXPORTATIONS CANADIENNES")
    print("=" * 70)

    df_base, model, X_vars = load_and_estimate_baseline()

    scenarios = {}

    # 1. ALE Canada-ASEAN
    scenarios["ALE Canada-ASEAN"] = scenario_new_fta(
        df_base, model, X_vars,
        target_countries=["IDN", "THA", "VNM", "MYS", "PHL", "SGP", "MMR", "KHM", "LAO", "BRN"],
        scenario_name="ALE Canada-ASEAN",
    )

    # 2. ALE Canada-Mercosur
    scenarios["ALE Canada-Mercosur"] = scenario_new_fta(
        df_base, model, X_vars,
        target_countries=["BRA", "ARG", "URY", "PRY"],
        scenario_name="ALE Canada-Mercosur",
    )

    # 3. ALE Canada-Inde
    scenarios["ALE Canada-Inde"] = scenario_new_fta(
        df_base, model, X_vars,
        target_countries=["IND"],
        scenario_name="ALE Canada-Inde",
    )

    # 4. Sanctions contre la Russie (scénario post-2022)
    scenarios["Sanctions Russie"] = scenario_sanctions(
        df_base, model, X_vars,
        target_countries=["RUS", "BLR"],
        reduction_pct=90,
        scenario_name="Sanctions Canada-Russie/Bélarus",
    )

    # 5. Récession en Chine (-5% PIB)
    scenarios["Récession Chine"] = scenario_gdp_shock(
        df_base, model, X_vars,
        target_countries=["CHN"],
        gdp_change_pct=-5.0,
        scenario_name="Récession en Chine (-5% PIB)",
    )

    # 6. Boom en Afrique (+15% PIB)
    scenarios["Boom Afrique"] = scenario_gdp_shock(
        df_base, model, X_vars,
        target_countries=[
            "NGA", "ZAF", "KEN", "GHA", "TZA", "ETH", "CIV",
            "SEN", "CMR", "MOZ",
        ],
        gdp_change_pct=15.0,
        scenario_name="Boom économique en Afrique (+15% PIB)",
    )

    # Résumé comparatif
    print("\n\n" + "=" * 70)
    print("  RÉSUMÉ DES SCÉNARIOS")
    print("=" * 70)
    print(f"\n{'Scénario':<35s} {'Impact total':>15s}")
    print("-" * 55)

    summary_data = []
    for name, df_s in scenarios.items():
        total = df_s["impact"].sum()
        sign = "+" if total > 0 else ""
        print(f"  {name:<33s} {sign}${total/1e6:>12,.0f}M")
        summary_data.append({"scenario": name, "impact_total_usd": total})

    summary = pd.DataFrame(summary_data)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUTS / "counterfactual_summary.csv", index=False)
    print(f"\nSauvegardé : {OUTPUTS / 'counterfactual_summary.csv'}")

    return scenarios


if __name__ == "__main__":
    run_all_scenarios()
