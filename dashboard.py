"""
Tableau de bord — Vue opérationnelle du portefeuille risque sismique.
Point d'entrée principal. Navigation via la sidebar gauche.

Le switch BRUTE / NETTE GAM dans la sidebar pilote tous les indicateurs
monétaires du dashboard (projection × 30% côté conservé).
"""

import streamlit as st
import plotly.graph_objects as go
from theme import apply_theme, apply_plotly_dark, ACCENT_RED, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_BLUE
from utils import (
    load_portefeuille, load_aep, load_distribution,
    points_chauds_commune_view, points_chauds_wilaya_view,
    render_view_toggle, is_net_view, project_value, view_label,
    fmt_mds, fmt_m, fmt_int, fmt_pct, status_dot,
    QS_RATIO_CONSERVE, RETENTION_NETTE_EVENT,
)

# =============================================================================
# CONFIG
# =============================================================================
st.set_page_config(
    page_title="Risque Sismique — Pilotage",
    page_icon="assets/icon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
render_view_toggle()
NET = is_net_view()


# =============================================================================
# HERO
# =============================================================================
sub = "Portefeuille garantie Tremblement de Terre — surveillance des accumulations, scénarios de perte, tarification et programme de réassurance."
if NET:
    sub += " Vision nette GAM après quota-share 30/70."

st.markdown(f"""
<div class="hero-block">
  <h1>Pilotage du Risque Sismique</h1>
  <p>{sub}</p>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# DONNÉES
# =============================================================================
try:
    df_porte = load_portefeuille()
    df_pcw   = points_chauds_wilaya_view()
    df_pcc   = points_chauds_commune_view()
    df_aep   = load_aep()
    df_dist  = load_distribution()
except FileNotFoundError as e:
    st.error(f"Fichier de données introuvable. Vérifier le contenu du dossier `data/`. Détail : {e}")
    st.stop()

df_2025 = df_porte[df_porte["ANNEE"] == 2025]


# =============================================================================
# KPIs PRINCIPAUX
# =============================================================================
label_kpi = "Indicateurs du portefeuille actif" + (" — Net GAM" if NET else "")
st.markdown(f"### {label_kpi}")

capital_total_brut = df_2025["CAPITAL_ASSURE"].sum() / 1e9
cep_total_brut = df_2025["CAPITAL_EXPOSE_PONDERE"].sum() / 1e9
prime_nette_brut = df_2025["PRIME_NETTE_TOTALE"].sum() / 1e6

capital_affiche = project_value(capital_total_brut)
cep_affiche = project_value(cep_total_brut)
prime_affichee = project_value(prime_nette_brut)
nb_polices = len(df_2025)
ratio_cep_cap = cep_affiche / capital_affiche * 100 if capital_affiche else 0

aal_row = df_dist[df_dist["Statistique"].astype(str).str.contains("Moyenne", na=False)]
aal_mda_brut = float(aal_row["Valeur (M DA)"].iloc[0]) if len(aal_row) else 1225.6
aal_affiche = project_value(aal_mda_brut)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Capital assuré", f"{capital_affiche:.1f} Mds DA",
          "× 30%" if NET else None, delta_color="off")
c2.metric("Polices actives", fmt_int(nb_polices))
c3.metric("CEP cumulé", f"{cep_affiche:.1f} Mds DA", f"{ratio_cep_cap:.1f}% du capital")
c4.metric("Prime nette", fmt_m(prime_affichee))
c5.metric("Perte annuelle moyenne", fmt_m(aal_affiche),
          f"x{aal_affiche/prime_affichee:.1f} vs prime", delta_color="inverse")


# =============================================================================
# ENCADRÉ MODE NET
# =============================================================================
if NET:
    st.markdown(f"""
    <div class="insight-card info" style="margin-top:0.5rem">
      <h4>Structure de cession active</h4>
      <p>Quota-share 30/70 — GAM conserve 30% du risque. Rétention nette par événement : <strong>{RETENTION_NETTE_EVENT:.0f} M DA</strong>.
      Tous les indicateurs monétaires ci-dessous sont projetés sur la part nette conservée. Les grilles tarifaires, plafonds de souscription
      et engagements face à l'assuré restent exprimés en capital brut.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# STATUS GÉNÉRAL DU PORTEFEUILLE
# =============================================================================
st.markdown("### État de surveillance")

crit_w = (df_pcw["Niveau_clean"] == "Critique").sum()
warn_w = (df_pcw["Niveau_clean"] == "Attention").sum()
crit_c = (df_pcc["Niveau_clean"] == "Critique").sum()
warn_c = (df_pcc["Niveau_clean"] == "Attention").sum()

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(f"""
    <div class="insight-card critical">
      <h4>{status_dot("Critique")} Wilayas critiques</h4>
      <p><strong>{crit_w}</strong> wilayas au-dessus du seuil de rétention. {warn_w} en surveillance rapprochée.</p>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown(f"""
    <div class="insight-card warning">
      <h4>{status_dot("Attention")} Communes sensibles</h4>
      <p><strong>{crit_c + warn_c}</strong> communes dépassent le seuil de vigilance. {crit_c} nécessitent une action immédiate.</p>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    gap_factor = aal_affiche / prime_affichee if prime_affichee else 0
    st.markdown(f"""
    <div class="insight-card warning">
      <h4>{status_dot("Attention")} Écart tarifaire</h4>
      <p>Prime pure technique <strong>x{gap_factor:.1f}</strong> supérieure à la prime collectée. Ajustement progressif en cours.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# ÉQUATION ÉCONOMIQUE — graphique comparatif
# =============================================================================
st.markdown("### Structure économique du risque")

col_graph, col_insight = st.columns([1.6, 1])

with col_graph:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Prime collectée", "Prime pure technique", "Prime cible recommandée"],
        y=[prime_affichee, aal_affiche, aal_affiche * 1.5],
        marker=dict(
            color=[ACCENT_RED, ACCENT_ORANGE, ACCENT_GREEN],
            line=dict(color='rgba(255,255,255,0.15)', width=1),
        ),
        text=[f"{prime_affichee:.0f} M DA", f"{aal_affiche:.0f} M DA", f"{aal_affiche*1.5:.0f} M DA"],
        textposition="outside",
        textfont=dict(size=13, color="#ffffff"),
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} M DA<extra></extra>",
    ))
    fig.update_layout(
        height=380,
        yaxis_title="M DA par an",
        showlegend=False,
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

with col_insight:
    couverture = prime_affichee/aal_affiche*100 if aal_affiche else 0
    st.markdown(f"""
    <div class="insight-card info" style="height: 100%;">
      <h4>Lecture économique</h4>
      <p>La prime collectée couvre aujourd'hui <strong>{couverture:.0f}%</strong> de la sinistralité espérée.
      Sans correction progressive, chaque année creuse le déséquilibre technique.</p>
      <p style="margin-top:0.8rem;">Cible de convergence : <strong>{aal_affiche*1.5:.0f} M DA</strong> sur 24 à 36 mois avec plafond de hausse annuelle de +50%.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# COURBE AEP
# =============================================================================
st.markdown("### Scénarios de perte annuelle cumulée")

col_aep, col_rep = st.columns([2, 1])

with col_aep:
    pml_series = df_aep["PML (M DA)"].astype(float)
    if NET:
        pml_series = pml_series * QS_RATIO_CONSERVE

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_aep["Période retour (ans)"],
        y=pml_series,
        mode="lines+markers",
        line=dict(color=ACCENT_RED, width=3),
        marker=dict(size=10, color=ACCENT_RED, line=dict(color='#ffffff', width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(255,71,87,0.15)",
        hovertemplate="<b>Période retour %{x} ans</b><br>Perte cumulée : %{y:,.0f} M DA<extra></extra>",
        name="PML annuelle",
    ))
    fig2.update_layout(
        height=400,
        xaxis_title="Période de retour (ans) — échelle logarithmique",
        yaxis_title=f"Perte annuelle cumulée (M DA) — {view_label(short=True)}",
        xaxis_type="log",
        showlegend=False,
    )
    apply_plotly_dark(fig2)
    st.plotly_chart(fig2, use_container_width=True)

with col_rep:
    st.markdown("#### Seuils de référence")
    for rp_ref in [100, 250, 500]:
        row = df_aep[df_aep["Période retour (ans)"] == rp_ref]
        if len(row):
            val = float(row["PML (M DA)"].iloc[0])
            val_aff = project_value(val)
            st.metric(f"Retour {rp_ref} ans", f"{val_aff:,.0f} M DA".replace(",", " "))


# =============================================================================
# NAVIGATION RAPIDE
# =============================================================================
st.markdown("### Modules disponibles")

nav_items = [
    ("Portefeuille", "Filtrage dynamique de l'ensemble des polices actives par wilaya, commune, type, zone et classe."),
    ("Structure de Risque", "Analyse de la vulnérabilité du portefeuille et matrice d'exposition Zone × Classe."),
    ("Cartographie", "Top wilayas et communes, courbe de concentration, carte interactive de l'Algérie."),
    ("Scénarios de Perte", "Courbes de perte annuelle et événementielle, contribution par source et par région."),
    ("Moteur de Tarification", "Calcul de prime actuelle vs recommandée, impact portefeuille, trajectoire de rattrapage."),
    ("Réassurance", "Paramétrage du programme de couverture catastrophe avec prise en compte du quota-share existant."),
    ("Alertes & Limites", "Surveillance temps réel des accumulations vs seuils de rétention."),
    ("Scoring Automatique", "Classement instantané d'une nouvelle police à la souscription via le modèle pré-entraîné."),
]

cols = st.columns(2)
for i, (titre, desc) in enumerate(nav_items):
    with cols[i % 2]:
        st.markdown(f"""
        <div class="insight-card info">
          <h4>{titre}</h4>
          <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.caption(
    f"Vision active : {view_label()} · "
    "Données portefeuille consolidé 2023–2025 · Référentiels RPA99 version 2003 (DTR B C 2 48) et EMS-98"
)
