"""
utils.py — Chargement des données, constantes et helpers partagés.

Gère :
- le chargement des fichiers Excel sources (avec cache)
- la grille tarifaire et les seuils de criticité
- le switch VUE BRUTE vs VUE NETTE GAM (quota-share 30/70)
- les projections nettes des indicateurs monétaires
- les centroïdes wilayas pour la cartographie
- le chargement du modèle CatBoost de scoring
"""

from pathlib import Path
import pandas as pd
import streamlit as st

# =============================================================================
# CHEMINS
# =============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

FILE_PORTEFEUILLE = DATA_DIR / "Phase1_Complet_avec_Vulnerabilite.xlsx"
FILE_CUMULS = DATA_DIR / "Phase2_Cumuls_et_Points_Chauds.xlsx"
FILE_SCENARIOS = DATA_DIR / "Phase2_PML_MonteCarlo.xlsx"
FILE_DIAGNOSTIC = DATA_DIR / "Phase3_Diagnostic_Recommandations.xlsx"
FILE_COMPLEMENT_NET = DATA_DIR / "Phase2_3_Complements_Net_GAM.xlsx"
FILE_CATBOOST = DATA_DIR / "Phase4_CatBoost_Scoring.xlsx"
FILE_MODELE = MODEL_DIR / "modele_catboost_scoring.cbm"


# =============================================================================
# STRUCTURE DE CESSION — QUOTA-SHARE 30/70
# =============================================================================
QS_RATIO_CONSERVE = 0.30      # part conservée par la compagnie
QS_RATIO_CEDE     = 0.70      # part cédée au pool de réassureurs
RETENTION_NETTE_EVENT = 500   # M DA — rétention nette par événement
RETENTION_BRUTE_IMPLICITE = RETENTION_NETTE_EVENT / QS_RATIO_CONSERVE  # ≈ 1 667 M DA


# =============================================================================
# COULEURS (dark-mode optimisées)
# =============================================================================
COLOR_ZONE = {
    "0":   "#5b6374",
    "I":   "#4fa9e3",
    "IIa": "#ffa502",
    "IIb": "#ff7f50",
    "III": "#ff4757",
}

COLOR_CLASSE = {
    "B": "#ff4757",
    "C": "#ffa502",
    "D": "#2ed573",
}

COLOR_CRITICITE = {
    "Critique":     "#ff4757",
    "Attention":    "#ff7f50",
    "Surveillance": "#ffd32a",
    "Normal":       "#2ed573",
}

COLOR_SCORING = {
    "ROUGE":  "#ff4757",
    "ORANGE": "#ffa502",
    "VERT":   "#2ed573",
}

COLOR_TYPE = {
    "Immobilier":    "#4fa9e3",
    "Commerciale":   "#1abc9c",
    "Industrielle":  "#9b59b6",
}

ACCENT = "#ff4757"
NEUTRAL = "#5b6374"


# =============================================================================
# GRILLE TARIFAIRE — taux en ‰ du capital (inchangée en net/brut)
# =============================================================================
GRILLE_TARIFAIRE = {
    "0":   {"B": 1.0,  "C": 1.0,  "D": 1.0},
    "I":   {"B": 7.0,  "C": 5.4,  "D": 3.8},
    "IIa": {"B": 10.0, "C": 7.6,  "D": 5.2},
    "IIb": {"B": 13.0, "C": 9.8,  "D": 6.6},
    "III": {"B": 16.0, "C": 12.0, "D": 8.0},
}

TAUX_ACTUEL_UNIFORME = 0.68


# =============================================================================
# SEUILS DE CRITICITÉ — deux jeux (brut Phase 2, et net recalibré)
# =============================================================================
# Brut : seuils historiques Phase 2 (Capital Exposé Pondéré cumulé)
SEUIL_CEP_COMMUNE_BRUT = {
    "Critique":     300,    # M DA
    "Attention":    150,
    "Surveillance": 50,
}

SEUIL_CEP_WILAYA_BRUT = {
    "Critique":     1500,
    "Attention":    750,
    "Surveillance": 300,
}

# Net : recalibrés sur rétention brute implicite (40% / 20% / 10%)
# Avec rétention brute implicite ≈ 1 667 M DA, les seuils net sont 200 / 100 / 50 M DA
SEUIL_CEP_COMMUNE_NET = {
    "Critique":     200,
    "Attention":    100,
    "Surveillance": 50,
}

SEUIL_CEP_WILAYA_NET = {
    "Critique":     450,
    "Attention":    225,
    "Surveillance": 90,
}


# =============================================================================
# VIEW MODE — toggle brut vs net (stocké en session_state)
# =============================================================================
def init_view_mode():
    """Initialise le mode de vision dans session_state."""
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "brut"


def get_view_mode():
    """Retourne le mode courant : 'brut' ou 'net'."""
    init_view_mode()
    return st.session_state.view_mode


def is_net_view():
    """True si la vision nette GAM est active."""
    return get_view_mode() == "net"


def project_value(v):
    """Projette une valeur monétaire en net (× 0.30) si mode net actif."""
    if is_net_view():
        return v * QS_RATIO_CONSERVE
    return v


def view_label(short=False):
    """Retourne le label textuel de la vue actuelle."""
    if is_net_view():
        return "Net GAM" if short else "Vision nette GAM (30% conservé)"
    return "Brut" if short else "Vision brute (100% souscrit)"


def get_seuils_commune():
    """Retourne les seuils de criticité commune selon le mode."""
    return SEUIL_CEP_COMMUNE_NET if is_net_view() else SEUIL_CEP_COMMUNE_BRUT


def get_seuils_wilaya():
    """Retourne les seuils de criticité wilaya selon le mode."""
    return SEUIL_CEP_WILAYA_NET if is_net_view() else SEUIL_CEP_WILAYA_BRUT


def render_view_toggle():
    """
    Affiche le toggle brut/net en haut de la sidebar.
    À appeler en premier dans chaque page, avant d'utiliser les données.
    """
    init_view_mode()

    st.sidebar.markdown("""
    <div style="background: rgba(255,71,87,0.08);
                border: 1px solid rgba(255,71,87,0.3);
                border-radius: 10px;
                padding: 0.7rem 0.9rem;
                margin-bottom: 1rem;">
      <p style="margin:0; font-size:0.72rem; text-transform:uppercase;
                letter-spacing:1.2px; color:#8a94a8; font-weight:600">
        Vision du risque
      </p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.sidebar.radio(
        "Mode d'affichage",
        options=["brut", "net"],
        format_func=lambda x: "Brute — 100% souscrit" if x == "brut" else "Nette GAM — 30% conservé",
        index=0 if st.session_state.view_mode == "brut" else 1,
        label_visibility="collapsed",
        key="view_mode_radio",
    )
    st.session_state.view_mode = mode

    if mode == "net":
        st.sidebar.markdown("""
        <div style="font-size:0.78rem; color:#8a94a8; line-height:1.5;
                    padding:0.4rem 0.2rem;">
          Quota-share 30/70<br>
          Rétention nette 500 M DA<br>
          Seuils recalibrés
        </div>
        """, unsafe_allow_html=True)

    st.sidebar.markdown("<hr style='margin:0.6rem 0; border-color:rgba(255,255,255,0.08)'>",
                        unsafe_allow_html=True)

    return mode


# =============================================================================
# CHARGEMENT DONNÉES (cache Streamlit)
# =============================================================================
@st.cache_data(show_spinner="Chargement du portefeuille...")
def load_portefeuille():
    df = pd.read_excel(FILE_PORTEFEUILLE, sheet_name="Portefeuille raffiné")
    df["CAPITAL_M"] = df["CAPITAL_ASSURE"] / 1_000_000
    df["CEP_M"] = df["CAPITAL_EXPOSE_PONDERE"] / 1_000_000
    df["PRIME_M"] = df["PRIME_NETTE_TOTALE"] / 1_000_000
    df["TYPE_COURT"] = df["TYPE"].replace({
        "2 - Installation Commerciale": "Commerciale",
        "3 - Installation Industrielle": "Industrielle",
        "Bien immobilier": "Immobilier",
    })
    return df


@st.cache_data(show_spinner=False)
def load_cumuls_wilaya():
    df = pd.read_excel(FILE_CUMULS, sheet_name="Cumuls wilaya", header=0)
    df.columns = [str(c).strip() for c in df.columns]
    return df.dropna(how="all")


@st.cache_data(show_spinner=False)
def load_points_chauds_wilaya():
    df = pd.read_excel(FILE_CUMULS, sheet_name="Points chauds wilaya", header=2)
    df = df.dropna(subset=["Wilaya"]).reset_index(drop=True)
    df["Niveau_clean"] = df["Niveau"].str.replace(r"[^\w\s]", "", regex=True).str.strip()
    df["CEP_M_num"] = pd.to_numeric(df["CEP (M DA)"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_points_chauds_commune():
    df = pd.read_excel(FILE_CUMULS, sheet_name="Points chauds commune", header=2)
    df = df.dropna(subset=["Commune"]).reset_index(drop=True)
    df["Niveau_clean"] = df["Niveau"].str.replace(r"[^\w\s]", "", regex=True).str.strip()
    df["CEP_M_num"] = pd.to_numeric(df["CEP (M DA)"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_pareto():
    df = pd.read_excel(FILE_CUMULS, sheet_name="Pareto concentration", header=3)
    df = df.dropna(subset=["Commune"]).reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False)
def load_aep():
    df = pd.read_excel(FILE_SCENARIOS, sheet_name="Courbe AEP (PML)", header=3)
    df = df.dropna(subset=["Période retour (ans)"]).reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False)
def load_oep():
    df = pd.read_excel(FILE_SCENARIOS, sheet_name="Courbe OEP", header=3)
    df = df.dropna(subset=["Période retour (ans)"]).reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False)
def load_sources_scenarios():
    df = pd.read_excel(FILE_SCENARIOS, sheet_name="Contribution sources", header=0)
    return df


@st.cache_data(show_spinner=False)
def load_wilayas_scenarios():
    df = pd.read_excel(FILE_SCENARIOS, sheet_name="Contribution wilayas", header=0)
    return df


@st.cache_data(show_spinner=False)
def load_events_scenarios():
    df = pd.read_excel(FILE_SCENARIOS, sheet_name="Événements majeurs", header=0)
    return df


@st.cache_data(show_spinner=False)
def load_distribution():
    df = pd.read_excel(FILE_SCENARIOS, sheet_name="Distribution pertes", header=2)
    df = df.dropna(subset=["Statistique"]).reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False)
def load_indicateurs_wilaya():
    df = pd.read_excel(FILE_DIAGNOSTIC, sheet_name="Indicateurs wilaya", header=3)
    df = df.dropna(subset=["Wilaya"]).reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False)
def load_matrice_zone_classe():
    df = pd.read_excel(FILE_DIAGNOSTIC, sheet_name="Matrice Zone × Classe", header=3)
    df = df.dropna(subset=["Zone RPA"]).reset_index(drop=True)
    return df


# =============================================================================
# RE-CLASSIFICATION DES POINTS CHAUDS EN NET (applique seuils recalibrés)
# =============================================================================
def niveau_from_cep(cep_m, seuils):
    """Retourne le niveau de criticité pour un CEP (M DA) et un dict de seuils."""
    if pd.isna(cep_m):
        return "Normal"
    if cep_m >= seuils["Critique"]:
        return "Critique"
    if cep_m >= seuils["Attention"]:
        return "Attention"
    if cep_m >= seuils["Surveillance"]:
        return "Surveillance"
    return "Normal"


def points_chauds_commune_view():
    """
    Retourne les points chauds commune en tenant compte du mode brut/net.
    En mode net, on projette le CEP × 0.30 et on applique les seuils nets.
    """
    df = load_points_chauds_commune().copy()
    if is_net_view():
        df["CEP_M_num"] = df["CEP_M_num"] * QS_RATIO_CONSERVE
        seuils = SEUIL_CEP_COMMUNE_NET
        df["Niveau_clean"] = df["CEP_M_num"].apply(lambda v: niveau_from_cep(v, seuils))
        df["CEP (M DA)"] = df["CEP_M_num"]
    return df


def points_chauds_wilaya_view():
    """
    Retourne les points chauds wilaya en tenant compte du mode brut/net.
    """
    df = load_points_chauds_wilaya().copy()
    if is_net_view():
        df["CEP_M_num"] = df["CEP_M_num"] * QS_RATIO_CONSERVE
        seuils = SEUIL_CEP_WILAYA_NET
        df["Niveau_clean"] = df["CEP_M_num"].apply(lambda v: niveau_from_cep(v, seuils))
        df["CEP (M DA)"] = df["CEP_M_num"]
    return df


# =============================================================================
# MODÈLE CATBOOST DE SCORING
# =============================================================================
@st.cache_resource(show_spinner="Chargement du modèle de scoring...")
def load_catboost_model():
    """Charge le modèle CatBoost entraîné (cache en mémoire)."""
    from catboost import CatBoostClassifier
    m = CatBoostClassifier()
    m.load_model(str(FILE_MODELE))
    return m


def score_police(zone, classe, type_risque, capital_da, coef_v=None, coef_a=None):
    """
    Score une police via le modèle CatBoost.
    Retourne dict: {niveau, P_VERT, P_ORANGE, P_ROUGE}
    """
    model = load_catboost_model()

    if coef_a is None:
        A_map = {"0": 0.0, "I": 0.10, "IIa": 0.15, "IIb": 0.20, "III": 0.25}
        coef_a = A_map.get(str(zone), 0.15)
    if coef_v is None:
        V_map = {"B": 0.75, "C": 0.55, "D": 0.35}
        coef_v = V_map.get(str(classe), 0.55)

    row = pd.DataFrame([{
        "ZONE_FINALE": str(zone),
        "VULNERABILITE_CLASSE": str(classe),
        "TYPE_N": str(type_risque),
        "CAPITAL_ASSURE": float(capital_da),
        "VULNERABILITE_V": float(coef_v),
        "COEFFICIENT_A": float(coef_a),
    }])
    pred = model.predict(row)[0]
    if hasattr(pred, "__iter__") and not isinstance(pred, str):
        pred = pred[0]
    probas = model.predict_proba(row)[0]
    classes_ord = model.classes_
    result = {"niveau": str(pred)}
    for cls, p in zip(classes_ord, probas):
        result[f"P_{cls}"] = float(p)
    return result


# =============================================================================
# CENTROÏDES WILAYAS
# =============================================================================
WILAYA_CENTROIDS = {
    1: (27.877, -0.284, "ADRAR"),
    2: (36.165, 1.334, "CHLEF"),
    3: (34.077, 2.877, "LAGHOUAT"),
    4: (35.875, 7.107, "O.E.B"),
    5: (35.555, 6.175, "BATNA"),
    6: (36.754, 5.084, "BEJAIA"),
    7: (34.849, 5.724, "BISKRA"),
    8: (31.620, -2.219, "BECHAR"),
    9: (36.470, 2.828, "BLIDA"),
    10: (36.377, 3.902, "BOUIRA"),
    11: (22.787, 5.523, "TAMANRASSET"),
    12: (35.406, 8.116, "TEBESSA"),
    13: (34.881, -1.315, "TLEMCEN"),
    14: (35.371, 1.320, "TIARET"),
    15: (36.718, 4.046, "TIZI OUZOU"),
    16: (36.753, 3.058, "ALGER"),
    17: (34.664, 3.251, "DJELFA"),
    18: (36.822, 5.762, "JIJEL"),
    19: (36.190, 5.408, "SETIF"),
    20: (34.841, 0.142, "SAIDA"),
    21: (36.876, 6.908, "SKIKDA"),
    22: (35.203, -0.636, "SBA"),
    23: (36.900, 7.766, "ANNABA"),
    24: (36.462, 7.436, "GUELMA"),
    25: (36.365, 6.615, "CONSTANTINE"),
    26: (36.264, 2.755, "MEDEA"),
    27: (35.929, 0.089, "MOSTAGANEM"),
    28: (35.704, 4.541, "M'SILA"),
    29: (35.396, 0.140, "MASCARA"),
    30: (32.484, 3.673, "OUARGLA"),
    31: (35.698, -0.632, "ORAN"),
    32: (33.680, 1.015, "EL BAYADH"),
    33: (26.495, 8.477, "ILLIZI"),
    34: (36.068, 4.764, "B.B ARRERIDJ"),
    35: (36.767, 3.478, "BOUMERDES"),
    36: (36.729, 8.304, "EL TARF"),
    37: (27.676, -8.147, "TINDOUF"),
    38: (35.362, 1.317, "TISSEMSILT"),
    39: (33.366, 6.862, "EL OUED"),
    40: (35.426, 7.144, "KHENCHELA"),
    41: (36.276, 7.952, "SOUK AHRAS"),
    42: (36.589, 2.449, "TIPAZA"),
    43: (36.456, 6.263, "MILA"),
    44: (36.264, 1.968, "AIN DEFLA"),
    45: (29.585, -0.268, "NAAMA"),
    46: (35.298, -1.135, "A.TEMOUCHENT"),
    47: (32.479, 3.677, "GHARDAIA"),
    48: (35.737, 0.555, "RELIZANE"),
}


# =============================================================================
# HELPERS FORMATAGE
# =============================================================================
def fmt_mds(v):
    if pd.isna(v): return "—"
    return f"{v/1000:,.1f} Mds DA".replace(",", " ")


def fmt_m(v):
    if pd.isna(v): return "—"
    return f"{v:,.0f} M DA".replace(",", " ")


def fmt_pct(v, decimals=1):
    if pd.isna(v): return "—"
    return f"{v:.{decimals}f} %"


def fmt_int(v):
    if pd.isna(v): return "—"
    return f"{int(v):,}".replace(",", " ")


def status_dot(niveau):
    """Génère un status dot pulsant pour un niveau de criticité."""
    mapping = {
        "Critique": "critical",
        "Attention": "warning",
        "Surveillance": "monitor",
        "Normal": "normal",
    }
    cls = mapping.get(niveau, "normal")
    return f'<span class="status-dot {cls}"></span>'


def calc_prime_recommandee(capital, zone, classe):
    taux = GRILLE_TARIFAIRE.get(zone, {}).get(classe, 0)
    return capital * taux / 1000, taux


def calc_prime_actuelle(capital):
    return capital * TAUX_ACTUEL_UNIFORME / 1000
