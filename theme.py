"""
theme.py - Thème visuel du dashboard.

Injecte le CSS dark mode avec :
- Fond animé (gradients radiaux qui flottent lentement)
- Grille subtile en surimpression
- Cartes glassmorphism (transparence + blur)
- Typography moderne (Inter)
- Effets hover sur les métriques
- Status dots pulsants

Appeler apply_theme() au tout début de chaque page.
"""

import streamlit as st


def apply_theme():
    """Applique le thème dark mode sur toute la page."""
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    <style>
    /* =================================================================
       FOND ANIMÉ — base sombre + gradients radiaux qui flottent
       ================================================================= */
    .stApp {
        background: #060814;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Blobs animés */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            radial-gradient(circle at 15% 25%, rgba(220, 50, 50, 0.12) 0%, transparent 45%),
            radial-gradient(circle at 85% 70%, rgba(40, 130, 220, 0.10) 0%, transparent 45%),
            radial-gradient(circle at 50% 95%, rgba(150, 70, 220, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 95% 15%, rgba(255, 140, 60, 0.06) 0%, transparent 40%);
        animation: orbFloat 22s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }

    /* Grille subtile */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
        background-size: 60px 60px;
        pointer-events: none;
        z-index: 0;
    }

    @keyframes orbFloat {
        0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.85;
        }
        25% {
            transform: translate(40px, -30px) scale(1.08);
            opacity: 1;
        }
        50% {
            transform: translate(-20px, 40px) scale(0.95);
            opacity: 0.9;
        }
        75% {
            transform: translate(30px, 20px) scale(1.05);
            opacity: 0.95;
        }
    }

    /* Contenu au-dessus des fonds */
    .main .block-container {
        position: relative;
        z-index: 1;
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1500px;
    }

    /* =================================================================
       TYPOGRAPHIE
       ================================================================= */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    h1 {
        font-size: 2.3rem;
        background: linear-gradient(135deg, #ffffff 0%, #9ca8bc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }

    h2 { font-size: 1.5rem; margin-top: 2rem; color: #f0f3f8; }
    h3 { font-size: 1.2rem; color: #d8e0eb; font-weight: 600; }

    p, li, label, .stMarkdown {
        color: #c5cedb;
        line-height: 1.6;
    }

    /* =================================================================
       MÉTRIQUES (glassmorphism)
       ================================================================= */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    [data-testid="stMetric"]:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.18);
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
    }

    [data-testid="stMetricLabel"] {
        color: #7c8699 !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 600;
    }

    [data-testid="stMetricLabel"] p {
        color: #7c8699 !important;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.85rem !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    [data-testid="stMetricDelta"] {
        color: #9ca8bc !important;
        font-size: 0.85rem !important;
        font-weight: 500;
    }

    /* =================================================================
       SIDEBAR
       ================================================================= */
    [data-testid="stSidebar"] {
        background: rgba(6, 8, 20, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        color: #c5cedb;
        border-radius: 8px;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.06);
        color: #ffffff;
    }

    /* =================================================================
       TABS
       ================================================================= */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 5px;
        gap: 4px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 9px;
        color: #8a94a8;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.04);
        color: #ffffff;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.10) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    /* =================================================================
       DATAFRAMES
       ================================================================= */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        overflow: hidden;
    }

    /* =================================================================
       INPUTS, SELECTS, SLIDERS
       ================================================================= */
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }

    .stNumberInput input,
    .stTextInput input {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }

    .stSlider [data-baseweb="slider"] > div > div > div {
        background: linear-gradient(90deg, #ff4757 0%, #ff6b7a 100%) !important;
    }

    /* Checkbox */
    .stCheckbox label {
        color: #c5cedb !important;
    }

    /* =================================================================
       EXPANDER
       ================================================================= */
    .streamlit-expanderHeader,
    [data-testid="stExpander"] summary {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        color: #ffffff;
        font-weight: 500;
    }

    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }

    /* =================================================================
       BOUTONS
       ================================================================= */
    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #ff4757 0%, #c0392b 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #ffffff;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.5rem 1.2rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.01em;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 28px rgba(255, 71, 87, 0.35);
        border-color: rgba(255, 255, 255, 0.25);
    }

    /* =================================================================
       ALERTES (info/warning/success/error)
       ================================================================= */
    .stAlert {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        color: #e8ecf0;
    }

    div[data-testid="stAlert"] > div {
        color: #e8ecf0;
    }

    /* =================================================================
       SCROLLBAR
       ================================================================= */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.2);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.12);
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.22);
    }

    /* =================================================================
       HERO — bandeau haut de page
       ================================================================= */
    .hero-block {
        background: linear-gradient(135deg, rgba(255,71,87,0.18) 0%, rgba(10,14,26,0.3) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 2rem 2.3rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }

    .hero-block::before {
        content: '';
        position: absolute;
        top: -60%;
        right: -15%;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(255,71,87,0.20) 0%, transparent 65%);
        animation: heroPulse 9s ease-in-out infinite;
        pointer-events: none;
    }

    @keyframes heroPulse {
        0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.7; }
        50% { transform: scale(1.25) rotate(15deg); opacity: 1; }
    }

    .hero-block h1 {
        position: relative;
        z-index: 1;
        font-size: 2.4rem;
        margin: 0;
    }

    .hero-block p {
        position: relative;
        z-index: 1;
        color: #9ca8bc;
        font-size: 1.02rem;
        margin: 0.6rem 0 0 0;
        max-width: 800px;
    }

    /* =================================================================
       STATUS DOTS pulsants
       ================================================================= */
    .status-dot {
        display: inline-block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        margin-right: 10px;
        animation: dotPulse 2s ease-in-out infinite;
        vertical-align: middle;
    }

    .status-dot.critical {
        background: #ff4757;
        box-shadow: 0 0 12px #ff4757, 0 0 4px #ff4757;
    }
    .status-dot.warning {
        background: #ffa502;
        box-shadow: 0 0 12px #ffa502, 0 0 4px #ffa502;
    }
    .status-dot.monitor {
        background: #ffd32a;
        box-shadow: 0 0 12px #ffd32a, 0 0 4px #ffd32a;
    }
    .status-dot.normal {
        background: #2ed573;
        box-shadow: 0 0 12px #2ed573, 0 0 4px #2ed573;
    }

    @keyframes dotPulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%      { opacity: 0.6; transform: scale(0.85); }
    }

    /* =================================================================
       CARDS custom (pour constats, alertes visuelles)
       ================================================================= */
    .insight-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #ff4757;
        border-radius: 12px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .insight-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.15);
        border-left-color: #ff4757;
        transform: translateX(4px);
    }

    .insight-card h4 {
        margin: 0 0 0.5rem 0;
        color: #ffffff;
        font-size: 1.05rem;
    }

    .insight-card p {
        margin: 0;
        color: #a5b0c2;
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .insight-card.info      { border-left-color: #3498db; }
    .insight-card.warning   { border-left-color: #ffa502; }
    .insight-card.critical  { border-left-color: #ff4757; }
    .insight-card.success   { border-left-color: #2ed573; }

    /* =================================================================
       Footer et éléments cachés
       ================================================================= */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Caption */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #7c8699 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# TEMPLATE PLOTLY DARK — à appliquer sur chaque figure
# =============================================================================
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, -apple-system, sans-serif', color='#c5cedb', size=12),
    xaxis=dict(
        gridcolor='rgba(255,255,255,0.06)',
        zeroline=False,
        linecolor='rgba(255,255,255,0.15)',
        tickcolor='rgba(255,255,255,0.15)',
        title_font=dict(color='#8a94a8', size=12),
        tickfont=dict(color='#a5b0c2', size=11),
    ),
    yaxis=dict(
        gridcolor='rgba(255,255,255,0.06)',
        zeroline=False,
        linecolor='rgba(255,255,255,0.15)',
        tickcolor='rgba(255,255,255,0.15)',
        title_font=dict(color='#8a94a8', size=12),
        tickfont=dict(color='#a5b0c2', size=11),
    ),
    legend=dict(
        font=dict(color='#c5cedb', size=11),
        bgcolor='rgba(0,0,0,0)',
    ),
    hoverlabel=dict(
        bgcolor='#11172a',
        bordercolor='rgba(255,255,255,0.2)',
        font=dict(color='#ffffff', family='Inter'),
    ),
    margin=dict(t=40, b=50, l=60, r=40),
)


def apply_plotly_dark(fig):
    """Applique le layout dark à une figure Plotly."""
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# =============================================================================
# COULEURS DARK-OPTIMISÉES
# =============================================================================
ACCENT_RED = "#ff4757"
ACCENT_ORANGE = "#ffa502"
ACCENT_YELLOW = "#ffd32a"
ACCENT_GREEN = "#2ed573"
ACCENT_BLUE = "#3498db"
ACCENT_PURPLE = "#9b59b6"
ACCENT_CYAN = "#1abc9c"

TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#c5cedb"
TEXT_MUTED = "#7c8699"
