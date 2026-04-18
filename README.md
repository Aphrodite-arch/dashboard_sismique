# Dashboard Risque Sismique — Guide d'installation

Outil de pilotage du risque sismique du portefeuille. Ce document explique comment lancer le dashboard sur un PC, même sans expérience technique.

---

## Contenu du dossier

```
dashboard_sismique/
├── dashboard.py          fichier d'accueil
├── theme.py              thème visuel dark mode
├── utils.py              chargement des données et helpers
├── requirements.txt      bibliothèques requises
├── pages/                les 8 modules
├── data/                 fichiers Excel sources
├── models/               modèle de scoring CatBoost pré-entraîné
└── .streamlit/           configuration
```

## Les 9 modules disponibles

| Module | Usage |
|---|---|
| Accueil | Vue d'ensemble, KPIs, état de surveillance |
| Portefeuille | Exploration filtrable des polices actives |
| Structure de Risque | Vulnérabilité et matrice Zone × Classe |
| Cartographie | Top wilayas, communes, carte interactive |
| Scénarios de Perte | Courbes de perte par période de retour |
| Moteur de Tarification | Calcul de prime et trajectoire de rattrapage |
| Réassurance | Programme Cat XL par-dessus le quota-share 30/70 |
| Alertes & Limites | Surveillance des accumulations vs seuils |
| Scoring Automatique | Classement instantané d'une police (CatBoost) |

## Deux modes de vision — basculer dans la sidebar

Un commutateur **Brute / Nette GAM** est présent en haut de la sidebar sur toutes les pages. Il pilote la totalité des indicateurs monétaires du dashboard :

- **Vision brute** : 100% du risque souscrit, seuils de criticité de référence Phase 2 (300 / 150 / 50 M DA commune)
- **Vision nette GAM** : projection × 30% (part conservée après quota-share 30/70), seuils recalibrés 200 / 100 / 50 M DA, rétention nette par événement de 500 M DA

La bascule reclasse automatiquement les communes et wilayas. Passer de brut à net fait passer le nombre de communes critiques de 14 à 3 (Alger, Oran, Sétif).

Les grilles tarifaires et plafonds de souscription restent exprimés en brut car la compagnie reste engagée pour 100% du capital face à l'assuré.

---

# INSTALLATION — 3 ÉTAPES

## WINDOWS

### 1. Installer Python (une seule fois)

1. Aller sur **https://www.python.org/downloads/**
2. Cliquer sur le bouton **Download Python 3.12**
3. Lancer le fichier téléchargé
4. **Cocher la case** "Add Python to PATH" en bas de la fenêtre. Étape critique.
5. Cliquer sur "Install Now"
6. Vérifier : appuyer sur la touche Windows, taper `cmd`, Entrée. Dans la fenêtre noire, taper :
   ```
   python --version
   ```
   Doit afficher `Python 3.12.x`. Sinon, réinstaller en cochant bien la case PATH.

### 2. Installer les bibliothèques

1. Ouvrir l'Explorateur de fichiers, aller dans le dossier `dashboard_sismique`
2. Cliquer dans la barre d'adresse en haut (là où le chemin est affiché)
3. Effacer le contenu, taper `cmd` et appuyer sur Entrée
4. Une fenêtre noire s'ouvre, positionnée dans le bon dossier
5. Taper :
   ```
   pip install -r requirements.txt
   ```
6. Attendre 5 à 10 minutes — l'installation comprend catboost qui est plus lourd

### 3. Lancer le dashboard

Dans la même fenêtre noire :
```
streamlit run dashboard.py
```

Le navigateur s'ouvre automatiquement sur `http://localhost:8501`.

Au premier lancement, Streamlit peut demander un email. Appuyer sur Entrée pour passer sans en fournir.

### Arrêter le dashboard

Dans la fenêtre noire, appuyer sur **Ctrl + C**.

### Relancer plus tard

Répéter seulement :
1. Ouvrir le dossier `dashboard_sismique`
2. Barre d'adresse → taper `cmd` → Entrée
3. Taper `streamlit run dashboard.py`

---

## MAC

### 1. Installer Python

1. Télécharger depuis **https://www.python.org/downloads/macos/**
2. Choisir la dernière version 3.12.x, télécharger le fichier `.pkg`
3. Lancer l'installation (cliquer Continuer, Installer)
4. Vérifier : ouvrir le Terminal (Cmd + Espace → Terminal → Entrée) et taper :
   ```
   python3 --version
   ```

### 2. Installer les bibliothèques

1. Ouvrir le Terminal
2. Taper `cd ` (avec un espace après), puis glisser-déposer le dossier `dashboard_sismique` depuis le Finder dans la fenêtre du Terminal
3. Appuyer sur Entrée
4. Taper :
   ```
   pip3 install -r requirements.txt
   ```

### 3. Lancer le dashboard

```
streamlit run dashboard.py
```

Arrêt : **Ctrl + C**.

---

## LINUX

```bash
sudo apt update
sudo apt install python3 python3-pip
cd /chemin/vers/dashboard_sismique
pip3 install -r requirements.txt
streamlit run dashboard.py
```

---

# PROBLÈMES FRÉQUENTS

### "python n'est pas reconnu" sur Windows
La case "Add to PATH" n'a pas été cochée. Désinstaller Python depuis Paramètres → Applications, puis réinstaller en cochant la case.

### "pip n'est pas reconnu"
- Windows : `python -m pip install -r requirements.txt`
- Mac : `python3 -m pip install -r requirements.txt`

### Permission denied
- Windows : fermer la fenêtre, rouvrir en clic droit → "Exécuter en tant qu'administrateur"
- Mac/Linux : ajouter `--user` : `pip3 install -r requirements.txt --user`

### Le navigateur ne s'ouvre pas
Ouvrir manuellement et aller sur `http://localhost:8501`.

### "ModuleNotFoundError: No module named 'streamlit'" ou 'catboost'
L'installation des bibliothèques a échoué. Commande de secours :
```
pip install streamlit pandas numpy openpyxl plotly catboost
```

### "FileNotFoundError" sur un fichier Excel ou le modèle
Vérifier que tous les fichiers sources sont présents :
- Dans `data/` : les 5 fichiers Excel (Phase1_Complet, Phase2_Cumuls, Phase2_PML, Phase3_Diagnostic, Phase2_3_Complements_Net_GAM)
- Dans `models/` : le fichier `modele_catboost_scoring.cbm`

### Le dashboard est lent au premier chargement
Normal. Streamlit met en cache les 113 000 polices et charge le modèle CatBoost (une dizaine de secondes la première fois). Les navigations suivantes sont instantanées.

### Installation de catboost longue ou qui échoue
Sur Windows en particulier, catboost peut être lourd à installer. Commande alternative en forçant une version plus légère :
```
pip install "catboost>=1.2.0,<1.3.0"
```

---

# PERSONNALISATION

### Modifier les seuils de criticité
Dans `utils.py`, les deux jeux de seuils sont en haut du fichier : `SEUIL_CEP_COMMUNE_BRUT` et `SEUIL_CEP_COMMUNE_NET`. Modifier les valeurs. Streamlit recharge automatiquement.

### Modifier le ratio de cession du quota-share
Dans `utils.py`, ajuster `QS_RATIO_CONSERVE` (30% par défaut) et `RETENTION_NETTE_EVENT` (500 M DA par défaut). Les seuils nets et les projections Cat XL suivront.

### Modifier la grille tarifaire
Dans `utils.py`, chercher `GRILLE_TARIFAIRE`. Modifier les taux en ‰. Le moteur de tarification et la projection portefeuille se recalculent en direct.

### Modifier les couleurs du thème
Dans `theme.py`, les couleurs d'accent sont définies en haut du fichier. Les codes hexadécimaux peuvent être ajustés sans toucher au reste.

### Réentraîner le modèle de scoring
Le script `catboost_scoring_standalone.py` (fourni à part) permet de ré-entraîner le modèle sur un portefeuille mis à jour. Remplacer ensuite le fichier `models/modele_catboost_scoring.cbm` par le nouveau modèle généré.

---

Configuration testée : Python 3.10 à 3.12 · Streamlit ≥ 1.30 · Plotly ≥ 5.18 · CatBoost ≥ 1.2
