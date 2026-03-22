# Gravity Model — Canadian Export Potential

Identification des marches sous-exploites pour les exportateurs canadiens a l'aide d'un modele gravitaire estime par PPML.

## Objectif

Utiliser le modele gravitaire du commerce international pour :
1. Estimer les flux commerciaux "naturels" du Canada avec ses partenaires
2. Identifier les marches ou le Canada exporte **moins** que ce que les fondamentaux predisent (opportunites)
3. Prioriser les marches emergents pour les exportateurs canadiens

## Methodologie

- **Estimateur** : Poisson Pseudo-Maximum Likelihood (Santos Silva & Tenreyro, 2006)
- **Variables gravitaires** : distance bilaterale, frontiere commune, langue commune, passe colonial, accords commerciaux regionaux (ALE/RTA)
- **Controles** : PIB, population, effets fixes importateur et annee
- **Specifications** : OLS (baseline) → PPML → PPML avec effets fixes haute dimension

## Sources de donnees

| Source | Contenu |
|--------|---------|
| USITC Dynamic Gravity Dataset | Variables gravitaires, toutes paires de pays |
| UN Comtrade / IMF DOTS | Flux commerciaux bilateraux du Canada |
| Banque mondiale WDI | PIB, population |

## Structure

```
gravity_model_canada/
├── main.py                 # Pipeline principal
├── config.py               # Configuration
├── requirements.txt
├── src/
│   ├── data_download.py    # Telechargement et preparation des donnees
│   ├── model.py            # Estimation PPML
│   ├── potential.py        # Calcul du potentiel commercial
│   └── dashboard.py        # Dashboard Streamlit
├── data/
│   ├── raw/                # Donnees brutes
│   └── clean/              # Panel assemble
├── outputs/                # Resultats (CSV, graphiques)
├── notebooks/              # Analyses exploratoires
└── docs/                   # Documentation methodologique
```

## Utilisation

```bash
# Installer les dependances
pip install -r requirements.txt

# Executer le pipeline complet
python main.py

# Lancer le dashboard interactif
streamlit run src/dashboard.py
```

## References

- Santos Silva, J.M.C. & Tenreyro, S. (2006). "The Log of Gravity." *Review of Economics and Statistics*, 88(4), 641-658.
- Anderson, J.E. & van Wincoop, E. (2003). "Gravity with Gravitas: A Solution to the Border Puzzle." *American Economic Review*, 93(1), 170-192.
- Yotov, Y.V. et al. (2016). *An Advanced Guide to Trade Policy Analysis: The Structural Gravity Model.* WTO/UNCTAD.
