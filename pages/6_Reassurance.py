"""
Réassurance — Dimensionnement du programme de couverture catastrophe
                au-dessus du quota-share 30/70 existant.

Structure à trois niveaux :
  1. Rétention nette conservée par GAM : 500 M DA par événement
  2. Couche 1 Cat XL standard : 500 M → PML RP100 net
  3. Couche 2 Cat XL excess   : PML RP100 net → PML RP500 net
  Au-delà de RP500 net : non couvert (risque résiduel)

La prise en compte du QS existant divise la capacité Cat XL nécessaire
par ~3 et la prime par ~3, soit 200 à 300 M DA d'économie annuelle.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from theme import apply_theme, apply_plotly_dark, ACCENT_RED, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_BLUE
from utils import (
    load_aep, fmt_m, fmt_mds,
    render_view_toggle, is_net_view, view_label,
    QS_RATIO_CONSERVE, RETENTION_NETTE_EVENT, RETENTION_BRUTE_IMPLICITE,
)

st.set_page_config(page_title="Réassurance", layout="wide")
apply_theme()
render_view_toggle()
NET = is_net_view()

st.markdown(f"""
<div class="hero-block">
  <h1>Réassurance</h1>
  <p>Programme de couverture catastrophe par-dessus le quota-share 30/70 existant.
  Structure à trois niveaux — rétention nette, couche 1 standard, couche 2 excess.</p>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# STRUCTURE DE CESSION RAPPEL
# =============================================================================
st.markdown("### Structure de cession en vigueur")

col_qs1, col_qs2, col_qs3 = st.columns(3)
with col_qs1:
    st.markdown(f"""
    <div class="insight-card info">
      <h4>Quota-share 30 / 70</h4>
      <p>GAM conserve <strong>{QS_RATIO_CONSERVE*100:.0f}%</strong> de chaque risque souscrit.
      Les <strong>70%</strong> restants sont cédés au pool de réassureurs sur l'ensemble du portefeuille garantie TDT.</p>
    </div>
    """, unsafe_allow_html=True)

with col_qs2:
    st.markdown(f"""
    <div class="insight-card warning">
      <h4>Rétention nette par événement</h4>
      <p>Montant maximal conservé par GAM sur un événement unique : <strong>{RETENTION_NETTE_EVENT:.0f} M DA</strong>.
      Soit une rétention brute implicite de <strong>{RETENTION_BRUTE_IMPLICITE:,.0f} M DA</strong>.</p>
    </div>
    """.replace(",", " "), unsafe_allow_html=True)

with col_qs3:
    st.markdown(f"""
    <div class="insight-card success">
      <h4>Couverture par le QS</h4>
      <p>Le quota-share absorbe <strong>70%</strong> de toute perte, avant Cat XL.
      Cela réduit mécaniquement la capacité Cat XL nécessaire et le coût de placement.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# PARAMÈTRES MODIFIABLES DU CAT XL
# =============================================================================
st.markdown("---")
st.markdown("### Paramétrage du programme Cat XL")

col1, col2, col3 = st.columns(3)
with col1:
    retention = st.number_input(
        "Rétention nette par événement (M DA)",
        min_value=200, max_value=2000, value=RETENTION_NETTE_EVENT, step=50,
        help="Montant conservé en propre avant déclenchement Cat XL",
    )
with col2:
    rol_couche1 = st.slider(
        "Taux prime Couche 1 Cat XL (%)",
        min_value=1.0, max_value=4.0, value=2.5, step=0.25,
        help="Rate-on-Line couche standard",
    )
with col3:
    rol_couche2 = st.slider(
        "Taux prime Couche 2 Cat XL (%)",
        min_value=0.5, max_value=2.5, value=1.75, step=0.25,
        help="Rate-on-Line couche excess",
    )


# =============================================================================
# CALCULS SUR LES PML NETS
# =============================================================================
df_aep = load_aep()
df_aep["Période retour (ans)"] = pd.to_numeric(df_aep["Période retour (ans)"], errors="coerce")
df_aep["PML (M DA)"] = pd.to_numeric(df_aep["PML (M DA)"], errors="coerce")

def get_pml_net(rp):
    """Retourne le PML NET GAM (× 30%) pour une période de retour donnée, en M DA."""
    row = df_aep[df_aep["Période retour (ans)"] == rp]
    if len(row):
        return float(row["PML (M DA)"].iloc[0]) * QS_RATIO_CONSERVE
    return None

pml_50_net  = get_pml_net(50)  or 2200 * QS_RATIO_CONSERVE
pml_100_net = get_pml_net(100) or 3115
pml_250_net = get_pml_net(250) or 5200
pml_500_net = get_pml_net(500) or 6403

# Couche 1 : du point de rétention à PML100 net
couche1_limite = max(pml_100_net - retention, 0)
# Couche 2 : de PML100 net à PML500 net
couche2_limite = max(pml_500_net - pml_100_net, 0)
capacite_totale = couche1_limite + couche2_limite

prime_c1 = couche1_limite * rol_couche1 / 100
prime_c2 = couche2_limite * rol_couche2 / 100
prime_total = prime_c1 + prime_c2

# Comparaison avec le programme initial (sans prise en compte du QS)
prime_programme_initial = 390  # moyenne de la fourchette 325-460 M DA/an
economie_annuelle = prime_programme_initial - prime_total


# =============================================================================
# KPIs du programme
# =============================================================================
st.markdown("---")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Rétention nette", f"{retention:.0f} M DA")
k2.metric("Capacité Cat XL totale", f"{capacite_totale:,.0f} M DA".replace(",", " "),
          f"Couche 1 : {couche1_limite:,.0f} + Couche 2 : {couche2_limite:,.0f}".replace(",", " "),
          delta_color="off")
k3.metric("Prime annuelle estimée", fmt_m(prime_total),
          f"{prime_total/(1226*QS_RATIO_CONSERVE)*100:.1f}% de l'AAL net", delta_color="off")
k4.metric("Économie vs programme brut", fmt_m(economie_annuelle),
          "Grâce au QS existant", delta_color="off")


# =============================================================================
# VISUALISATION DE LA STRUCTURE EN COUCHES
# =============================================================================
st.markdown("---")
st.markdown("### Structure des couches — vision nette GAM")

structure = [
    ("Rétention nette GAM",     0,           retention,        "#5b6374",
     f"Conservé par GAM après QS"),
    ("Couche 1 Cat XL standard", retention,  couche1_limite,   "#ffa502",
     f"Taux {rol_couche1:.2f}% — Prime {fmt_m(prime_c1)}"),
    ("Couche 2 Cat XL excess",   pml_100_net, couche2_limite,  "#ff4757",
     f"Taux {rol_couche2:.2f}% — Prime {fmt_m(prime_c2)}"),
    ("Au-dessus de RP500 net (non couvert)", pml_500_net, 1500, "#2a3448",
     "Risque résiduel"),
]

fig = go.Figure()
for i, (label, base, hauteur, color, annot) in enumerate(structure):
    fig.add_shape(
        type="rect",
        x0=0.15 + i*0.20, x1=0.15 + i*0.20 + 0.16,
        y0=base, y1=base + hauteur,
        fillcolor=color,
        line=dict(color="rgba(255,255,255,0.2)", width=2),
    )
    text_color = "#ffffff" if i in [1, 2] else "#c5cedb"
    fig.add_annotation(
        x=0.15 + i*0.20 + 0.08, y=base + hauteur/2,
        text=f"<b>{label}</b><br>{hauteur:,.0f} M DA<br><i>{annot}</i>".replace(",", " "),
        showarrow=False,
        font=dict(color=text_color, size=10),
        align="center",
    )

# Lignes de repère pour les PML de référence
reperes = [(50, pml_50_net, "#4fa9e3"),
           (100, pml_100_net, "#ffa502"),
           (250, pml_250_net, "#9b59b6"),
           (500, pml_500_net, "#ff4757")]
for rp, val, color in reperes:
    fig.add_shape(type="line", x0=0, x1=1, y0=val, y1=val,
                  line=dict(color=color, width=1, dash="dot"))
    fig.add_annotation(
        x=1.02, y=val,
        text=f"<b>RP {rp} ans</b><br>{val:,.0f} M DA".replace(",", " "),
        showarrow=False,
        font=dict(color=color, size=10),
        xanchor="left",
    )

fig.update_xaxes(visible=False, range=[0, 1.2])
fig.update_yaxes(title="Perte agrégée annuelle — NET GAM (M DA)",
                 range=[0, pml_500_net + 2000])
fig.update_layout(height=560, showlegend=False, margin=dict(r=180))
apply_plotly_dark(fig)
st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# COMPARAISON AVANT / APRÈS PRISE EN COMPTE DU QS
# =============================================================================
st.markdown("---")
st.markdown("### Impact de la prise en compte du QS existant")

df_comp = pd.DataFrame([
    ("Rétention nette",           2500,         retention,       "M DA"),
    ("Capacité Cat XL totale",    19000,        capacite_totale, "M DA"),
    ("Prime Cat XL annuelle",     390,          prime_total,     "M DA/an"),
], columns=["Élément", "Programme initial (brut)", "Programme refondé (net)", "Unité"])

fig_comp = go.Figure()
fig_comp.add_trace(go.Bar(
    name="Programme initial (brut)",
    x=df_comp["Élément"],
    y=df_comp["Programme initial (brut)"],
    marker=dict(color="#5b6374", line=dict(color='rgba(255,255,255,0.15)', width=1)),
    text=[f"{v:,.0f}".replace(",", " ") for v in df_comp["Programme initial (brut)"]],
    textposition="outside",
    textfont=dict(color="#ffffff", size=12),
))
fig_comp.add_trace(go.Bar(
    name="Programme refondé (net)",
    x=df_comp["Élément"],
    y=df_comp["Programme refondé (net)"],
    marker=dict(color=ACCENT_GREEN, line=dict(color='rgba(255,255,255,0.15)', width=1)),
    text=[f"{v:,.0f}".replace(",", " ") for v in df_comp["Programme refondé (net)"]],
    textposition="outside",
    textfont=dict(color="#ffffff", size=12),
))
fig_comp.update_layout(
    height=420,
    barmode="group",
    yaxis_title="Valeur (M DA ou M DA/an)",
    yaxis_type="log",
    legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
)
apply_plotly_dark(fig_comp)
st.plotly_chart(fig_comp, use_container_width=True)

st.markdown(f"""
<div class="insight-card success">
  <h4>Économie globale</h4>
  <p>La prise en compte du QS existant libère environ <strong>{economie_annuelle:.0f} M DA</strong> de prime Cat XL annuelle.
  Cet argent n'est pas un gain — il reflète le fait que le QS joue déjà un rôle de transfert massif.
  La question de second ordre à poser : le QS 30/70 actuel est-il optimal, ou faut-il le renégocier ?</p>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# ÉQUATION ÉCONOMIQUE EN NET
# =============================================================================
st.markdown("---")
st.markdown("### Équation économique cible — vision nette GAM")

aal_net = 1226 * QS_RATIO_CONSERVE
prime_cible_net = aal_net * 1.5
frais_gestion = prime_cible_net * 0.15
resultat = prime_cible_net - prime_total - frais_gestion - aal_net

fig_wf = go.Figure(go.Waterfall(
    orientation="v",
    measure=["absolute", "relative", "relative", "relative", "total"],
    x=["Prime nette cible", "− Coût Cat XL", "− Frais de gestion", "− Sinistralité nette attendue", "Résultat technique"],
    y=[prime_cible_net, -prime_total, -frais_gestion, -aal_net, resultat],
    text=[f"{v:+,.0f}".replace(",", " ") for v in [prime_cible_net, -prime_total, -frais_gestion, -aal_net, resultat]],
    textposition="outside",
    textfont=dict(color="#ffffff", size=12),
    connector={"line": {"color": "rgba(255,255,255,0.2)"}},
    increasing={"marker": {"color": ACCENT_GREEN, "line": dict(color="rgba(255,255,255,0.2)", width=1)}},
    decreasing={"marker": {"color": ACCENT_RED, "line": dict(color="rgba(255,255,255,0.2)", width=1)}},
    totals={"marker": {"color": ACCENT_BLUE, "line": dict(color="rgba(255,255,255,0.2)", width=1)}},
))
fig_wf.update_layout(
    height=480,
    yaxis_title="M DA par an — NET GAM",
)
apply_plotly_dark(fig_wf)
st.plotly_chart(fig_wf, use_container_width=True)

if resultat >= 0:
    st.markdown(f"""
    <div class="insight-card success">
      <h4>Équation équilibrée</h4>
      <p>Résultat technique attendu sur la part nette conservée par GAM : <strong>{resultat:+.0f} M DA par an</strong>.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="insight-card warning">
      <h4>Déséquilibre à corriger</h4>
      <p>Déficit attendu sur la part nette : <strong>{resultat:.0f} M DA</strong>. Trois leviers possibles :
      augmenter la prime encaissée (via la grille tarifaire), réduire la rétention nette, ou renégocier la cession du QS.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# OPTIONS ALTERNATIVES
# =============================================================================
st.markdown("---")
st.markdown("### Leviers alternatifs à explorer")

options = pd.DataFrame([
    ("Renégociation du QS",      "Ajustement de la quote-part conservée (ex. 25/75 ou 35/65) selon l'appétence au risque",
     "Impact direct sur la rétention et la capacité Cat XL nécessaire"),
    ("Cat bond",                  "Capacité additionnelle, indépendance des cycles de réassurance traditionnelle",
     "Coût de structuration élevé, minimum ~50 M USD, délai 12-18 mois"),
    ("Stop-loss annuel",          "Protection du résultat technique au-delà d'un seuil annuel cumulé",
     "Utile contre les années à événements multiples, coût non négligeable"),
    ("Couverture paramétrique",   "Déclenchement rapide sur critère objectif (magnitude + localisation)",
     "Risque de base significatif, mais liquidité immédiate post-sinistre"),
    ("Pool sectoriel national",   "Mutualisation entre compagnies algériennes, coût partagé",
     "Gouvernance complexe, dépendance politique"),
], columns=["Option", "Description", "Point de vigilance"])

st.dataframe(options, use_container_width=True, hide_index=True, height=260)


# =============================================================================
# PROTOCOLE DE PLACEMENT
# =============================================================================
st.markdown("---")
st.markdown("### Protocole de placement recommandé")

st.markdown("""
<div class="insight-card info">
  <h4>Séquence en 5 étapes</h4>
  <p style="line-height:1.8">
  <strong>1.</strong> Validation interne de la rétention nette cible (500 M DA) par la Direction Technique<br>
  <strong>2.</strong> Consultation d'au moins 3 courtiers de réassurance pour quotation Cat XL sur la structure ci-dessus<br>
  <strong>3.</strong> Comparaison des offres : capacité, rate-on-line, clauses d'exclusion, conditions de reconstitution<br>
  <strong>4.</strong> Sélection et négociation finale — obtenir une proposition de renouvellement annuel automatique<br>
  <strong>5.</strong> Intégration contractuelle synchronisée avec la période de renouvellement du QS existant
  </p>
</div>
""", unsafe_allow_html=True)
