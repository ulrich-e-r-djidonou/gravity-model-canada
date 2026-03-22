"""
Modèle gravitaire — Estimation PPML avec effets fixes.

Estimateur : Poisson Pseudo-Maximum Likelihood (Santos Silva & Tenreyro, 2006)
Effets fixes : exportateur-année × importateur-année (ou importateur + année)

Spécifications :
    1. Gravity de base : ln(dist), contig, comlang, comcol, rta
    2. Augmenté : + ln(gdp_d), ln(pop_d)
    3. Structurel : effets fixes haute dimension via pyfixest

Usage :
    python src/model.py
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_CLEAN, OUTPUTS


def load_panel() -> pd.DataFrame:
    """Charge et prépare le panel pour l'estimation."""
    path = DATA_CLEAN / "gravity_panel.parquet"
    df = pd.read_parquet(path)

    # Variables en log (ajout de 1 pour les zéros)
    df["ln_trade"] = np.log(df["trade_value"].clip(lower=1))
    df["ln_dist"] = np.log(df["dist"].clip(lower=1))
    df["ln_gdp_o"] = np.log(df["gdp_o"].clip(lower=1))
    df["ln_gdp_d"] = np.log(df["gdp_d"].clip(lower=1))
    df["ln_pop_o"] = np.log(df["pop_o"].clip(lower=1))
    df["ln_pop_d"] = np.log(df["pop_d"].clip(lower=1))

    # Identifiants pour effets fixes
    df["pair_id"] = df["iso3_o"] + "_" + df["iso3_d"]
    df["year_str"] = df["year"].astype(str)
    df["imp_year"] = df["iso3_d"] + "_" + df["year_str"]

    # Supprimer les flux manquants
    df = df.dropna(subset=["trade_value", "dist", "gdp_d"])

    print(f"Panel prêt : {len(df):,} obs, {df['iso3_d'].nunique()} partenaires, "
          f"{df['year'].nunique()} années")
    return df


# ──────────────────────────────────────────────
# Spécification 1 : OLS (baseline naïve)
# ──────────────────────────────────────────────
def estimate_ols(df: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """
    OLS sur ln(trade) — baseline pour comparaison.
    Problème connu : biais de sélection (exclut les zéros), hétéroscédasticité.
    """
    print("\n=== Spécification 1 : OLS (baseline) ===")

    # Exclure les zéros (biais de sélection — c'est le problème que PPML corrige)
    df_pos = df[df["trade_value"] > 0].copy()

    X_vars = ["ln_dist", "ln_gdp_d", "ln_pop_d", "contig", "comlang_off", "rta"]
    X = sm.add_constant(df_pos[X_vars])
    y = df_pos["ln_trade"]

    model = sm.OLS(y, X).fit(cov_type="HC1")
    print(model.summary().tables[1])
    return model


# ──────────────────────────────────────────────
# Spécification 2 : PPML (Santos Silva & Tenreyro, 2006)
# ──────────────────────────────────────────────
def estimate_ppml_basic(df: pd.DataFrame) -> sm.genmod.generalized_linear_model.GLMResultsWrapper:
    """
    PPML via GLM Poisson — inclut les flux zéro, corrige l'hétéroscédasticité.
    Variable dépendante : trade_value (en niveaux, pas en log).
    """
    print("\n=== Spécification 2 : PPML (baseline) ===")

    X_vars = ["ln_dist", "ln_gdp_d", "ln_pop_d", "contig", "comlang_off", "rta"]
    X = sm.add_constant(df[X_vars].astype(float))
    y = df["trade_value"].astype(float)

    model = sm.GLM(y, X, family=sm.families.Poisson()).fit(
        cov_type="HC1", maxiter=100
    )
    print(model.summary().tables[1])
    return model


# ──────────────────────────────────────────────
# Spécification 3 : PPML avec effets fixes (pyfixest)
# ──────────────────────────────────────────────
def estimate_ppml_fe(df: pd.DataFrame):
    """
    PPML structurel avec effets fixes haute dimension :
    - Effets fixes importateur (contrôle les résistances multilatérales)
    - Effets fixes année (contrôle les tendances globales)

    Utilise pyfixest pour une estimation rapide.
    """
    print("\n=== Spécification 3 : PPML avec effets fixes (pyfixest) ===")

    try:
        import pyfixest as pf

        # Spec 3a : EF importateur + année
        print("\n--- 3a : EF importateur + année ---")
        m3a = pf.feols(
            "trade_value ~ ln_dist + contig + comlang_off + rta + ln_gdp_d + ln_pop_d "
            "| iso3_d + year",
            data=df,
            vcov="hetero",
            fml_syntax="fixest",  # Poisson via fepois si disponible
        )
        print(m3a.summary())

        # Spec 3b : PPML (Poisson) avec EF
        print("\n--- 3b : PPML (Poisson) avec EF importateur + année ---")
        try:
            m3b = pf.fepois(
                "trade_value ~ ln_dist + contig + comlang_off + rta + ln_gdp_d + ln_pop_d "
                "| iso3_d + year",
                data=df,
                vcov="hetero",
            )
            print(m3b.summary())
            return m3b
        except Exception as e:
            print(f"  fepois non disponible ({e}), utilisation de feols comme fallback")
            return m3a

    except ImportError:
        print("  pyfixest non installé. Utilisation de statsmodels avec dummies.")
        return estimate_ppml_with_dummies(df)


def estimate_ppml_with_dummies(df: pd.DataFrame):
    """Fallback : PPML avec dummies manuelles (moins efficace mais fonctionne)."""
    # Dummies importateur (top 50 partenaires pour limiter la dimensionnalité)
    top_partners = df.groupby("iso3_d")["trade_value"].sum().nlargest(50).index
    df_sub = df[df["iso3_d"].isin(top_partners)].copy()

    partner_dummies = pd.get_dummies(df_sub["iso3_d"], prefix="d", drop_first=True)
    year_dummies = pd.get_dummies(df_sub["year"], prefix="yr", drop_first=True)

    X_vars = ["ln_dist", "ln_gdp_d", "ln_pop_d", "contig", "comlang_off", "rta"]
    X = pd.concat([df_sub[X_vars], partner_dummies, year_dummies], axis=1)
    X = sm.add_constant(X.astype(float))
    y = df_sub["trade_value"].astype(float)

    model = sm.GLM(y, X, family=sm.families.Poisson()).fit(
        cov_type="HC1", maxiter=100
    )

    # Afficher seulement les coefficients gravity (pas les dummies)
    gravity_params = model.params[: len(X_vars) + 1]
    gravity_pvalues = model.pvalues[: len(X_vars) + 1]
    print("\nCoefficients gravity :")
    for var, coef, pval in zip(
        ["const"] + X_vars, gravity_params, gravity_pvalues
    ):
        sig = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
        print(f"  {var:20s} {coef:10.4f}  (p={pval:.4f}) {sig}")

    return model


# ──────────────────────────────────────────────
# Résumé comparatif des spécifications
# ──────────────────────────────────────────────
def compare_specifications(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estime les 3 spécifications et produit un tableau comparatif.
    """
    results = {}

    # OLS
    ols = estimate_ols(df)
    results["OLS"] = {
        "ln_dist": ols.params.get("ln_dist", None),
        "rta": ols.params.get("rta", None),
        "contig": ols.params.get("contig", None),
        "comlang_off": ols.params.get("comlang_off", None),
        "ln_gdp_d": ols.params.get("ln_gdp_d", None),
        "N": int(ols.nobs),
        "R2": ols.rsquared,
    }

    # PPML basic
    ppml = estimate_ppml_basic(df)
    results["PPML"] = {
        "ln_dist": ppml.params.get("ln_dist", None),
        "rta": ppml.params.get("rta", None),
        "contig": ppml.params.get("contig", None),
        "comlang_off": ppml.params.get("comlang_off", None),
        "ln_gdp_d": ppml.params.get("ln_gdp_d", None),
        "N": int(ppml.nobs),
        "R2": 1 - ppml.deviance / ppml.null_deviance,
    }

    comparison = pd.DataFrame(results).T
    print("\n=== Tableau comparatif ===")
    print(comparison.to_string())

    # Sauvegarder
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(OUTPUTS / "model_comparison.csv")
    print(f"\nSauvegardé : {OUTPUTS / 'model_comparison.csv'}")

    return comparison


if __name__ == "__main__":
    df = load_panel()
    compare_specifications(df)
