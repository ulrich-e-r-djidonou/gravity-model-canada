"""
Dashboard interactif — Potentiel commercial des exportations canadiennes.

Visualisations :
    1. Carte mondiale : potentiel commercial par pays (choropleth)
    2. Top marches sous-exploites (bar chart)
    3. Scatter : flux reel vs predit
    4. Analyse sectorielle (treemap + bar par secteur)
    5. Scenarios contrefactuels (bar comparatif)
    6. Tableau des opportunites EDC
    7. Resume

Usage :
    streamlit run src/dashboard.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OUTPUTS, DATA_CLEAN


st.set_page_config(
    page_title="Canada Trade Potential \u2014 Gravity Model",
    page_icon="\U0001f341",
    layout="wide",
)

st.title("Potentiel commercial des exportations canadiennes")
st.markdown("*Mod\u00e8le gravitaire PPML \u2014 Identification des march\u00e9s sous-exploit\u00e9s*")

# ──────────────────────────────────────────────
# Navigation par onglets
# ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Potentiel commercial",
    "Analyse sectorielle",
    "Sc\u00e9narios contrefactuels",
    "Opportunit\u00e9s EDC",
])


@st.cache_data
def load_data():
    potential = pd.read_csv(OUTPUTS / "trade_potential.csv")
    try:
        opportunities = pd.read_csv(OUTPUTS / "edc_opportunities.csv")
    except FileNotFoundError:
        opportunities = pd.DataFrame()
    try:
        sectoral = pd.read_csv(OUTPUTS / "sectoral_potential.csv")
    except FileNotFoundError:
        sectoral = pd.DataFrame()
    try:
        counterfactual = pd.read_csv(OUTPUTS / "counterfactual_summary.csv")
    except FileNotFoundError:
        counterfactual = pd.DataFrame()
    return potential, opportunities, sectoral, counterfactual


potential, opportunities, sectoral, counterfactual = load_data()

if potential.empty:
    st.error("Aucune donn\u00e9e trouv\u00e9e. Ex\u00e9cutez d'abord `python main.py`.")
    st.stop()


# ══════════════════════════════════════════════
# TAB 1 : Potentiel commercial
# ══════════════════════════════════════════════
with tab1:
    st.header("Carte du potentiel commercial")

    col1, col2 = st.columns([3, 1])

    with col2:
        metric = st.radio(
            "M\u00e9trique affich\u00e9e :",
            ["gap_usd", "potential_ratio", "trade_actual"],
            format_func=lambda x: {
                "gap_usd": "Gap commercial (USD)",
                "potential_ratio": "Ratio potentiel (pr\u00e9dit/r\u00e9el)",
                "trade_actual": "Exportations r\u00e9elles",
            }[x],
        )

    with col1:
        fig_map = px.choropleth(
            potential,
            locations="iso3_d",
            color=metric,
            hover_name="iso3_d",
            hover_data={
                "trade_actual": ":,.0f",
                "trade_predicted": ":,.0f",
                "gap_usd": ":,.0f",
                "potential_ratio": ":.2f",
                "classification": True,
            },
            color_continuous_scale="RdYlGn" if metric == "gap_usd" else "Viridis",
            title=f"Exportations canadiennes \u2014 {metric}",
        )
        fig_map.update_layout(
            geo=dict(showframe=False, projection_type="natural earth"),
            height=500,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # Top 20 sous-exploites
    st.header("Top 20 \u2014 March\u00e9s sous-exploit\u00e9s (opportunit\u00e9s)")

    top_under = potential[potential["gap_usd"] > 0].nlargest(20, "gap_usd")

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=top_under["iso3_d"],
        y=top_under["trade_actual"] / 1e6,
        name="Exportations r\u00e9elles",
        marker_color="#2196F3",
    ))
    fig_bar.add_trace(go.Bar(
        x=top_under["iso3_d"],
        y=top_under["trade_predicted"] / 1e6,
        name="Exportations pr\u00e9dites (gravit\u00e9)",
        marker_color="#4CAF50",
        opacity=0.7,
    ))
    fig_bar.update_layout(
        barmode="group",
        yaxis_title="Millions USD",
        xaxis_title="Pays partenaire",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Scatter reel vs predit
    st.header("Flux r\u00e9el vs pr\u00e9dit")

    fig_scatter = px.scatter(
        potential,
        x="trade_actual",
        y="trade_predicted",
        color="classification",
        hover_name="iso3_d",
        log_x=True,
        log_y=True,
        color_discrete_map={
            "Sous-exploit\u00e9": "#4CAF50",
            "\u00c9quilibre": "#FFC107",
            "Sur-exploit\u00e9": "#F44336",
        },
        title="Exportations r\u00e9elles vs pr\u00e9dites par le mod\u00e8le gravitaire",
    )
    max_val = max(potential["trade_actual"].max(), potential["trade_predicted"].max())
    fig_scatter.add_trace(go.Scatter(
        x=[1, max_val], y=[1, max_val],
        mode="lines", line=dict(dash="dash", color="gray"),
        name="Ligne 45\u00b0 (r\u00e9el = pr\u00e9dit)", showlegend=True,
    ))
    fig_scatter.update_layout(
        xaxis_title="Exportations r\u00e9elles (USD, log)",
        yaxis_title="Exportations pr\u00e9dites (USD, log)",
        height=500,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.caption(
        "**Au-dessus de la ligne** : le Canada exporte moins que ce que la gravit\u00e9 pr\u00e9dit "
        "(opportunit\u00e9). **En dessous** : le Canada exporte plus que pr\u00e9dit (d\u00e9pendance)."
    )


# ══════════════════════════════════════════════
# TAB 2 : Analyse sectorielle
# ══════════════════════════════════════════════
with tab2:
    st.header("Analyse sectorielle")

    if sectoral.empty:
        st.info("Ex\u00e9cutez `python src/sectors.py` pour g\u00e9n\u00e9rer l'analyse sectorielle.")
    else:
        # Résumé par secteur
        sec_summary = sectoral.groupby("sector").agg(
            gap_total=("gap", lambda x: x[x > 0].sum()),
            n_opportunities=("gap", lambda x: (x > 0).sum()),
            trade_total=("trade_value", "sum"),
        ).sort_values("gap_total", ascending=False).reset_index()

        # Treemap du potentiel par secteur
        st.subheader("Potentiel inexploit\u00e9 par secteur")

        fig_treemap = px.treemap(
            sec_summary,
            path=["sector"],
            values="gap_total",
            color="gap_total",
            color_continuous_scale="Greens",
            title="Gap commercial par secteur (USD)",
        )
        fig_treemap.update_layout(height=450, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_treemap, use_container_width=True)

        # Bar chart comparatif
        st.subheader("Comparaison des secteurs")

        fig_sec = go.Figure()
        fig_sec.add_trace(go.Bar(
            x=sec_summary["sector"],
            y=sec_summary["trade_total"] / 1e6,
            name="Exportations r\u00e9elles",
            marker_color="#2196F3",
        ))
        fig_sec.add_trace(go.Bar(
            x=sec_summary["sector"],
            y=(sec_summary["trade_total"] + sec_summary["gap_total"]) / 1e6,
            name="Potentiel (r\u00e9el + gap)",
            marker_color="#4CAF50",
            opacity=0.7,
        ))
        fig_sec.update_layout(
            barmode="group",
            yaxis_title="Millions USD",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_sec, use_container_width=True)

        # Detail par secteur
        st.subheader("D\u00e9tail par secteur")

        selected_sector = st.selectbox(
            "Choisir un secteur :",
            sec_summary["sector"].tolist(),
        )

        sec_detail = sectoral[
            (sectoral["sector"] == selected_sector) & (sectoral["gap"] > 0)
        ].nlargest(15, "gap")

        if not sec_detail.empty:
            fig_detail = go.Figure()
            fig_detail.add_trace(go.Bar(
                x=sec_detail["iso3_d"],
                y=sec_detail["trade_value"] / 1e6,
                name="R\u00e9el",
                marker_color="#2196F3",
            ))
            fig_detail.add_trace(go.Bar(
                x=sec_detail["iso3_d"],
                y=sec_detail["predicted"] / 1e6,
                name="Pr\u00e9dit",
                marker_color="#4CAF50",
                opacity=0.7,
            ))
            fig_detail.update_layout(
                barmode="group",
                title=f"Top 15 opportunit\u00e9s \u2014 {selected_sector}",
                yaxis_title="Millions USD",
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_detail, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 3 : Scenarios contrefactuels
# ══════════════════════════════════════════════
with tab3:
    st.header("Sc\u00e9narios contrefactuels")

    if counterfactual.empty:
        st.info("Ex\u00e9cutez `python src/counterfactual.py` pour g\u00e9n\u00e9rer les sc\u00e9narios.")
    else:
        st.markdown(
            "Simulation de l'impact de changements de politique commerciale "
            "sur les exportations canadiennes (mod\u00e8le gravitaire PPML, \u00e9quilibre partiel)."
        )

        # Bar chart des impacts
        cf = counterfactual.copy()
        cf["impact_B"] = cf["impact_total_usd"] / 1e9
        cf["color"] = cf["impact_B"].apply(lambda x: "#4CAF50" if x > 0 else "#F44336")

        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(
            x=cf["scenario"],
            y=cf["impact_B"],
            marker_color=cf["color"],
            text=cf["impact_B"].apply(lambda x: f"{'+'if x>0 else ''}{x:.1f}B"),
            textposition="outside",
        ))
        fig_cf.update_layout(
            title="Impact estim\u00e9 par sc\u00e9nario (milliards USD)",
            yaxis_title="Impact (milliards USD)",
            xaxis_title="",
            height=500,
            showlegend=False,
        )
        fig_cf.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_cf, use_container_width=True)

        # Tableau detaille
        st.subheader("D\u00e9tail des sc\u00e9narios")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Sc\u00e9narios d'ouverture (ALE)**")
            ale_scenarios = cf[cf["impact_B"] > 0]
            for _, row in ale_scenarios.iterrows():
                st.metric(
                    row["scenario"],
                    f"+${row['impact_B']:.1f}B",
                )

        with col2:
            st.markdown("**Sc\u00e9narios de choc**")
            choc_scenarios = cf[cf["impact_B"] <= 0]
            for _, row in choc_scenarios.iterrows():
                st.metric(
                    row["scenario"],
                    f"${row['impact_B']:.1f}B",
                    delta_color="inverse",
                )

        st.caption(
            "Ces simulations sont en \u00e9quilibre partiel et ne tiennent pas compte "
            "des effets d'\u00e9quilibre g\u00e9n\u00e9ral ni de la diversion commerciale."
        )


# ══════════════════════════════════════════════
# TAB 4 : Opportunites EDC
# ══════════════════════════════════════════════
with tab4:
    st.header("Opportunit\u00e9s EDC \u2014 March\u00e9s \u00e9mergents")

    if not opportunities.empty:
        display_cols = [
            "iso3_d", "trade_actual", "trade_predicted",
            "gap_usd", "potential_ratio", "gdp_d_last", "priority_score",
        ]
        col_names = {
            "iso3_d": "Pays",
            "trade_actual": "Export. r\u00e9elles ($)",
            "trade_predicted": "Export. pr\u00e9dites ($)",
            "gap_usd": "Gap ($)",
            "potential_ratio": "Ratio",
            "gdp_d_last": "PIB partenaire ($)",
            "priority_score": "Score",
        }
        df_display = opportunities[display_cols].head(20).rename(columns=col_names)
        st.dataframe(
            df_display.style.format({
                "Export. r\u00e9elles ($)": "${:,.0f}",
                "Export. pr\u00e9dites ($)": "${:,.0f}",
                "Gap ($)": "${:,.0f}",
                "Ratio": "{:.2f}",
                "PIB partenaire ($)": "${:,.0f}",
                "Score": "{:.2f}",
            }),
            use_container_width=True,
            height=600,
        )
    else:
        st.info("Ex\u00e9cutez `python src/potential.py` pour g\u00e9n\u00e9rer les opportunit\u00e9s EDC.")

    # Resume
    st.header("R\u00e9sum\u00e9")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pays analys\u00e9s", f"{len(potential)}")
    col2.metric("Sous-exploit\u00e9s", f"{(potential['classification'] == 'Sous-exploit\u00e9').sum()}")
    col3.metric("En \u00e9quilibre", f"{(potential['classification'] == '\u00c9quilibre').sum()}")
    col4.metric("Sur-exploit\u00e9s", f"{(potential['classification'] == 'Sur-exploit\u00e9').sum()}")

    total_gap = potential[potential["gap_usd"] > 0]["gap_usd"].sum()
    st.metric("Potentiel inexploit\u00e9 total", f"${total_gap/1e9:.1f} milliards USD")


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.divider()
st.markdown(
    """
    **M\u00e9thodologie** : Mod\u00e8le gravitaire estim\u00e9 par PPML (Santos Silva & Tenreyro, 2006).
    Variables : distance bilat\u00e9rale, fronti\u00e8re commune, langue commune, pass\u00e9 colonial,
    accords commerciaux r\u00e9gionaux, PIB et population du partenaire.

    **Sources** : USITC Dynamic Gravity Dataset, UN Comtrade, Banque mondiale WDI.

    *Projet portfolio \u2014 Quantitative Analyst-Economist, EDC*
    """
)
