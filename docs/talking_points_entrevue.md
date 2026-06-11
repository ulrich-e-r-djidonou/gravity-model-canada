# Talking Points - Entrevue EDC (Quantitative Analyst-Economist)

## 1. Presentation du projet (2 min)

> "J'ai construit un modele gravitaire des exportations canadiennes qui identifie les marches sous-exploites pour les exportateurs canadiens. C'est exactement le type d'analyse que l'equipe DREAM fait au quotidien."

**Chiffres cles a retenir :**
- 254 pays partenaires, 20 annees (2000-2019)
- $24.4 milliards de potentiel commercial inexploite
- 116 marches sous-exploites identifies
- 7 secteurs analyses (manufacturier, agriculture, energie...)

---

## 2. Questions techniques anticipees

### "Pourquoi avoir choisi le PPML plutot que l'OLS ?"

> "Deux raisons. Premierement, l'OLS en log-lineaire exclut les paires de pays sans commerce bilateral — c'est un biais de selection. Le PPML estime en niveaux et inclut les zeros. Deuxiemement, Santos Silva et Tenreyro (2006) ont demontre que l'OLS log-lineaire est inconsistant en presence d'heteroscedasticite, un probleme quasi universel dans les donnees de commerce. Le PPML est l'estimateur de reference dans la litterature depuis."

### "Comment gerez-vous l'endogeneite dans le modele ?"

> "Les effets fixes annee controlent les chocs communs. Dans une specification plus structurelle, on utiliserait des effets fixes importateur-annee pour controler les resistances multilaterales a la Anderson-van Wincoop (2003). Mon modele est unilateral — le Canada est le seul exportateur — ce qui limite le probleme mais c'est une limitation reconnue. Pour un modele de production, j'utiliserais des variables instrumentales ou des effets fixes haute dimension via pyfixest."

### "Comment interpretez-vous un marche 'sous-exploite' ?"

> "Un marche ou le Canada exporte significativement moins que ce que les fondamentaux predisent — taille de l'economie, distance, langue, accords commerciaux. Le gap peut s'expliquer par des barrieres non-tarifaires, un manque de connaissance du marche, ou simplement un potentiel non explore. C'est exactement le signal qu'EDC utiliserait pour orienter ses efforts de facilitation."

### "Comment validez-vous les resultats du modele ?"

> "Trois niveaux. (1) Les coefficients sont coherents avec la theorie — l'elasticite du PIB est proche de 1, la distance a un effet negatif significatif. (2) Le pseudo-R2 du PPML est eleve (0.96), ce qui indique un bon ajustement. (3) Les resultats sont robustes a differentes specifications (OLS vs PPML, avec/sans effets fixes). Les marches identifies comme sous-exploites (Russie, Allemagne, Espagne) sont aussi ceux que la litterature identifie."

---

## 3. Questions sur le lien avec le poste DREAM

### "Comment ce projet se relie-t-il au travail de l'equipe DREAM ?"

> "DREAM developpe des modeles de risque souverain et de prevision macroeconomique. Mon modele gravitaire utilise les memes fondamentaux — PIB, population, indicateurs institutionnels — pour evaluer le potentiel commercial. La logique est la meme : utiliser les fondamentaux pour identifier les ecarts par rapport aux benchmarks. Un modele de probabilite de defaut souverain compare les fondamentaux d'un pays a son spread de credit ; mon modele compare les fondamentaux a ses flux commerciaux."

### "Comment aborderiez-vous le modele de probabilite de defaut souverain ?"

> "Je suivrais une approche similaire : panel de pays, indicateurs macro (dette/PIB, balance courante, reserves, inflation), variable cible binaire (defaut ou non). L'estimation serait un logit panel ou un probit avec effets aleatoires. Le scoring final mapperait les probabilites estimees vers des categories de risque. La validation se ferait out-of-sample avec des metriques comme l'AUC-ROC et le score de Brier."

### "Comment gerez-vous les 80,000 series macroeconomiques mentionnees dans la description ?"

> "L'experience avec les API de donnees est cle. Mon projet telecharge et assemble automatiquement des donnees de trois sources (USITC, Comtrade, Banque mondiale) via API. La logique est la meme pour 80,000 series : pipelines automatises, controles de qualite, stockage en parquet pour la performance. J'ai aussi de l'experience avec la documentation de ces processus, ce qui est essentiel pour l'audit IFRS9."

---

## 4. Questions sur les competences techniques

### "Quels outils Python utilisez-vous ?"

> "Pour l'econometrie : statsmodels, pyfixest (effets fixes haute dimension), scikit-learn. Pour les donnees : pandas, numpy, pyarrow. Pour la visualisation : plotly, streamlit. Pour les API : requests, wbgapi. Je suis aussi a l'aise avec Power BI, ce qui est mentionne dans la description du poste."

### "Avez-vous de l'experience avec IFRS9 / Bale ?"

> "J'ai une comprehension solide des principes — provisions pour pertes attendues, modeles de PD/LGD/EAD, scenarios prospectifs. Mon experience academique et professionnelle m'a forme a la rigueur documentaire requise : notes methodologiques, rapports de validation, documentation d'audit. Je n'ai pas travaille directement dans une institution financiere regulee, mais la competence modelisation + documentation est directement transferable."

---

## 5. Conclusion et questions a poser

### Questions a poser au panel :

1. "Quels sont les modeles principaux que l'equipe DREAM maintient actuellement ?"
2. "Comment l'equipe integre-t-elle les scenarios geopolitiques dans ses previsions ?"
3. "Quel est le processus de validation des modeles chez EDC ?"
4. "Comment l'equipe utilise-t-elle l'IA et le machine learning dans ses analyses ?"
5. "Quels sont les defis principaux en matiere de donnees que l'equipe rencontre ?"
