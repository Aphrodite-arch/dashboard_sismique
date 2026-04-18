"""
Moteur de Tarification — Calcul opérationnel de la prime selon la grille en vigueur.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from theme import apply_theme, apply_plotly_dark, ACCENT_RED, ACCENT_GREEN, ACCENT_ORANGE
from utils import (
    load_portefeuille,
    GRILLE_TARIFAIRE, TAUX_ACTUEL_UNIFORME,
    calc_prime_recommandee, calc_prime_actuelle,
    fmt_m, fmt_mds,
    render_view_toggle, is_net_view,
)

st.set_page_config(page_title="Moteur de Tarification", layout="wide")
apply_theme()
render_view_toggle()
NET = is_net_view()

st.markdown("""
<div class="hero-block">
  <h1>Moteur de Tarification</h1>
  <p>Calcul opérationnel de la prime recommandée pour une police. Comparaison avec la prime uniforme actuelle et simulation d'impact sur le portefeuille.</p>
</div>
""", unsafe_allow_html=True)

if NET:
    st.markdown("""
    <div class="insight-card info" style="margin-bottom:1rem">
      <h4>Tarification toujours exprimée en brut</h4>
      <p>La grille tarifaire et les primes individuelles s'appliquent au capital brut — la compagnie reste engagée face à l'assuré pour 100% du capital souscrit, indépendamment de la cession. Seul l'agrégat portefeuille est exposé en net en bas de page pour faciliter la comparaison avec les PML.</p>
    </div>
    """, unsafe_allow_html=True)

df = load_portefeuille()


# =============================================================================
# SIMULATEUR INDIVIDUEL
# =============================================================================
st.markdown("### Calcul individuel")

col_in, col_out = st.columns([1, 1])

with col_in:
    st.markdown("##### Paramètres de la police")

    capital_m = st.number_input(
        "Capital assuré (M DA)",
        min_value=0.1, max_value=10000.0, value=20.0, step=0.5,
    )
    capital = capital_m * 1_000_000

    type_risque = st.selectbox(
        "Type de risque",
        ["Bien immobilier", "Installation commerciale", "Installation industrielle"],
    )

    zone = st.selectbox(
        "Zone sismique",
        ["0", "I", "IIa", "IIb", "III"],
        index=2,
    )

    if type_risque == "Bien immobilier":
        if capital_m < 3: classe_auto = "B"
        elif capital_m < 30: classe_auto = "C"
        else: classe_auto = "D"
    elif type_risque == "Installation commerciale":
        if capital_m < 5: classe_auto = "B"
        elif capital_m < 100: classe_auto = "C"
        else: classe_auto = "D"
    else:
        if capital_m < 100: classe_auto = "C"
        else: classe_auto = "D"

    classe = st.selectbox(
        "Classe de vulnérabilité",
        ["B", "C", "D"],
        index=["B", "C", "D"].index(classe_auto),
        help=f"Détection automatique : {classe_auto}",
    )

    bonus_rpa = st.checkbox(
        "Bonus conformité aux normes parasismiques (−15%)",
        value=False,
        help="Certificat technique valide de moins de 5 ans, réservé aux classes C et D",
    )
    malus_nondoc = st.checkbox(
        "Malus absence de documentation (+25%)",
        value=False,
        help="Surtarification après 12 mois sans information structurelle",
    )

with col_out:
    st.markdown("##### Résultat")

    prime_actuelle = calc_prime_actuelle(capital)
    prime_reco, taux_reco = calc_prime_recommandee(capital, zone, classe)

    prime_reco_ajust = prime_reco
    if bonus_rpa and classe in ["C", "D"]:
        prime_reco_ajust *= 0.85
    if malus_nondoc:
        prime_reco_ajust *= 1.25

    ecart_abs = prime_reco_ajust - prime_actuelle
    ecart_fact = prime_reco_ajust / prime_actuelle if prime_actuelle > 0 else 0

    cc1, cc2 = st.columns(2)
    cc1.metric("Prime actuelle (taux uniforme)", fmt_m(prime_actuelle / 1e6))
    cc2.metric("Prime recommandée",
               fmt_m(prime_reco_ajust / 1e6),
               f"x{ecart_fact:.1f}",
               delta_color="inverse")

    st.markdown(f"""
    <div class="insight-card info" style="margin-top:1rem">
      <h4>Détail du calcul</h4>
      <p style="line-height: 1.8;">
        Capital : <strong>{fmt_m(capital_m)}</strong><br>
        Taux grille ({zone} × {classe}) : <strong>{taux_reco} ‰</strong><br>
        {'Bonus conformité : −15 %<br>' if (bonus_rpa and classe in ['C','D']) else ''}
        {'Malus non-documentation : +25 %<br>' if malus_nondoc else ''}
        Écart absolu : <strong>{fmt_m(ecart_abs/1e6)}</strong><br>
        Taux effectif : <strong>{prime_reco_ajust / capital * 1000:.2f} ‰</strong>
      </p>
    </div>
    """, unsafe_allow_html=True)

    if classe == "B" and zone in ["IIb", "III"]:
        st.markdown("""
        <div class="insight-card warning" style="margin-top:1rem">
          <h4>Franchise obligatoire</h4>
          <p>5% du capital (minimum 500 000 DA), non rachetable. Applicable aux polices en classe B situées en zones IIb et III.</p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# GRILLE TARIFAIRE
# =============================================================================
st.markdown("---")
st.markdown("### Grille tarifaire en vigueur")

zones_ord = ["0", "I", "IIa", "IIb", "III"]
classes_ord = ["B", "C", "D"]
grille_matrix = [[GRILLE_TARIFAIRE[z][c] for c in classes_ord] for z in zones_ord]

fig = go.Figure(data=go.Heatmap(
    z=grille_matrix,
    x=[f"Classe {c}" for c in classes_ord],
    y=[f"Zone {z}" for z in zones_ord],
    colorscale=[
        [0, "rgba(255,255,255,0.03)"],
        [0.2, "#2a3448"],
        [0.5, "#8c4a0f"],
        [0.75, "#cc3b3b"],
        [1, "#ff4757"],
    ],
    text=[[f"<b>{v:.1f} ‰</b>" for v in row] for row in grille_matrix],
    texttemplate="%{text}",
    textfont=dict(size=18, color="#ffffff"),
    colorbar=dict(
        title=dict(text="Taux (‰)", font=dict(color="#c5cedb")),
        tickfont=dict(color="#c5cedb"),
    ),
    hovertemplate="<b>%{y} × %{x}</b><br>Taux : %{z} ‰<extra></extra>",
))
fig.update_layout(
    height=440,
    yaxis=dict(autorange="reversed"),
)
apply_plotly_dark(fig)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"Taux uniforme actuellement pratiqué : {TAUX_ACTUEL_UNIFORME} ‰")


# =============================================================================
# IMPACT SUR LE PORTEFEUILLE
# =============================================================================
st.markdown("---")
st.markdown("### Impact sur le portefeuille 2025")

df_2025 = df[df["ANNEE"] == 2025].copy()

df_2025["TAUX_RECO_PER_MILLE"] = df_2025.apply(
    lambda r: GRILLE_TARIFAIRE.get(r["ZONE_FINALE"], {}).get(r["VULNERABILITE_CLASSE"], 0),
    axis=1,
)
df_2025["PRIME_RECO"] = df_2025["CAPITAL_ASSURE"] * df_2025["TAUX_RECO_PER_MILLE"] / 1000

prime_actuelle_tot = df_2025["PRIME_NETTE_TOTALE"].sum()
prime_reco_tot = df_2025["PRIME_RECO"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Prime actuelle collectée", fmt_m(prime_actuelle_tot / 1e6))
c2.metric("Prime grille recommandée",
          fmt_m(prime_reco_tot / 1e6),
          f"x{prime_reco_tot/prime_actuelle_tot:.1f}")
c3.metric("Écart à combler", fmt_m((prime_reco_tot - prime_actuelle_tot) / 1e6))

# Comparaison par zone
st.markdown("##### Répartition de la prime par zone sismique")
evo_zone = df_2025.groupby("ZONE_FINALE").agg(
    prime_actuelle=("PRIME_NETTE_TOTALE", "sum"),
    prime_reco=("PRIME_RECO", "sum"),
).reset_index()
evo_zone["zone_order"] = evo_zone["ZONE_FINALE"].map({"0":0,"I":1,"IIa":2,"IIb":3,"III":4})
evo_zone = evo_zone.sort_values("zone_order")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=evo_zone["ZONE_FINALE"],
    y=evo_zone["prime_actuelle"] / 1e6,
    name="Prime actuelle",
    marker=dict(color="#5b6374", line=dict(color='rgba(255,255,255,0.15)', width=1)),
    text=[f"{v/1e6:.1f}" for v in evo_zone["prime_actuelle"]],
    textposition="outside",
    textfont=dict(color="#ffffff"),
))
fig.add_trace(go.Bar(
    x=evo_zone["ZONE_FINALE"],
    y=evo_zone["prime_reco"] / 1e6,
    name="Prime recommandée",
    marker=dict(color=ACCENT_RED, line=dict(color='rgba(255,255,255,0.15)', width=1)),
    text=[f"{v/1e6:.0f}" for v in evo_zone["prime_reco"]],
    textposition="outside",
    textfont=dict(color="#ffffff"),
))
fig.update_layout(
    height=460,
    barmode="group",
    yaxis_title="Prime annuelle (M DA)",
    xaxis_title="Zone",
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
)
apply_plotly_dark(fig)
st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# CHEMIN DE TRANSITION
# =============================================================================
st.markdown("---")
st.markdown("### Trajectoire de rattrapage — effet cliquet sur renouvellements")

plafond = st.slider(
    "Plafond de hausse tarifaire annuelle autorisé",
    min_value=20, max_value=100, value=50, step=10,
    format="%d %%",
)

ratio = prime_reco_tot / prime_actuelle_tot
n_annees = 0
prime_courante = prime_actuelle_tot
path = [{"Année": 0, "Prime (M DA)": prime_actuelle_tot / 1e6}]
while prime_courante < prime_reco_tot and n_annees < 10:
    n_annees += 1
    prime_courante = min(prime_courante * (1 + plafond/100), prime_reco_tot)
    path.append({"Année": n_annees, "Prime (M DA)": prime_courante / 1e6})

df_path = pd.DataFrame(path)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_path["Année"],
    y=df_path["Prime (M DA)"],
    mode="lines+markers+text",
    line=dict(color=ACCENT_RED, width=3),
    marker=dict(size=13, color=ACCENT_RED, line=dict(color='#ffffff', width=1.5)),
    text=[f"{v:,.0f}".replace(",", " ") for v in df_path["Prime (M DA)"]],
    textposition="top center",
    textfont=dict(color="#ffffff", size=11),
    fill="tozeroy",
    fillcolor="rgba(255,71,87,0.12)",
))
fig.add_hline(
    y=prime_reco_tot / 1e6,
    line_dash="dash", line_color=ACCENT_GREEN,
    annotation_text=f"Cible : {prime_reco_tot/1e6:,.0f} M DA".replace(",", " "),
    annotation_position="bottom right",
    annotation_font=dict(color=ACCENT_GREEN),
)
fig.update_layout(
    height=400,
    xaxis_title="Année de renouvellement",
    yaxis_title="Prime annuelle (M DA)",
    showlegend=False,
)
apply_plotly_dark(fig)
fig.update_xaxes(tickmode="linear")
st.plotly_chart(fig, use_container_width=True)

st.markdown(f"""
<div class="insight-card success">
  <h4>Convergence</h4>
  <p>Avec un plafond de <strong>+{plafond}%</strong> par an, la cible est atteinte en <strong>{n_annees} ans</strong>.</p>
</div>
""", unsafe_allow_html=True)
