"""
Structure de Risque — Analyse de la vulnérabilité et matrice d'exposition.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from theme import apply_theme, apply_plotly_dark, ACCENT_RED, ACCENT_BLUE
from utils import (
    load_portefeuille,
    COLOR_CLASSE, COLOR_ZONE,
    fmt_int, fmt_pct, fmt_mds,
    render_view_toggle, is_net_view, project_value,
)

st.set_page_config(page_title="Structure de Risque", layout="wide")
apply_theme()
render_view_toggle()
NET = is_net_view()

st.markdown("""
<div class="hero-block">
  <h1>Structure de Risque</h1>
  <p>Répartition du portefeuille par classe de vulnérabilité et matrice d'exposition croisant zone sismique et classe de résistance.</p>
</div>
""", unsafe_allow_html=True)

df = load_portefeuille()

# Sélecteur d'année
annee = st.selectbox("Année d'analyse", sorted(df["ANNEE"].unique()), index=2)
df_y = df[df["ANNEE"] == annee]


# =============================================================================
# BIMODALITÉ
# =============================================================================
st.markdown(f"### Répartition par classe de vulnérabilité — portefeuille {annee}")

agg = df_y.groupby("VULNERABILITE_CLASSE").agg(
    polices=("NUMERO_POLICE", "count"),
    capital=("CAPITAL_M", "sum"),
    cep=("CEP_M", "sum"),
).reset_index()

total_p = agg["polices"].sum()
total_c = agg["capital"].sum()
total_e = agg["cep"].sum()
agg["pct_polices"] = agg["polices"] / total_p * 100
agg["pct_capital"] = agg["capital"] / total_c * 100
agg["pct_cep"]     = agg["cep"] / total_e * 100

fig = go.Figure()
metriques = [
    ("pct_polices", "Nombre de polices",  "#8a94a8"),
    ("pct_capital", "Capital assuré",     "#4fa9e3"),
    ("pct_cep",     "CEP",                "#ff4757"),
]
for col, label, color in metriques:
    fig.add_trace(go.Bar(
        x=agg["VULNERABILITE_CLASSE"], y=agg[col],
        name=label,
        marker=dict(color=color, line=dict(color='rgba(255,255,255,0.15)', width=1)),
        text=[f"{v:.0f}%" for v in agg[col]],
        textposition="outside",
        textfont=dict(size=13, color="#ffffff"),
    ))

fig.update_layout(
    height=460,
    barmode="group",
    yaxis_title="% du total portefeuille",
    xaxis_title="Classe de vulnérabilité",
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    yaxis=dict(range=[0, max(agg[["pct_polices","pct_capital","pct_cep"]].max()) * 1.15]),
)
apply_plotly_dark(fig)
st.plotly_chart(fig, use_container_width=True)

st.markdown("""
<div class="insight-card info">
  <h4>Lecture</h4>
  <p>La classe <strong>B</strong> (maçonnerie traditionnelle) concentre une majorité écrasante de polices pour un poids modéré en capital — sinistralité de masse attendue.
  La classe <strong>D</strong> (bâti conforme aux normes parasismiques) est l'inverse : peu de polices mais des capitaux unitaires élevés, d'où un risque de sinistre catastrophique ponctuel.</p>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# DÉTAIL PAR CLASSE
# =============================================================================
st.markdown("### Détail par classe")
c1, c2, c3 = st.columns(3)

for col, cl in zip([c1, c2, c3], ["B", "C", "D"]):
    row = agg[agg["VULNERABILITE_CLASSE"] == cl]
    if len(row) == 0: continue
    row = row.iloc[0]
    label = {"B": "Très vulnérable", "C": "Moyennement vulnérable", "D": "Résistant aux normes"}[cl]
    color = COLOR_CLASSE[cl]
    with col:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color}22 0%, rgba(255,255,255,0.03) 100%);
                    border-left:4px solid {color};
                    padding:1.2rem 1.4rem;
                    border-radius:12px;
                    backdrop-filter: blur(12px);
                    border: 1px solid rgba(255,255,255,0.08);">
          <h4 style="margin:0;color:{color}">Classe {cl} — {label}</h4>
          <p style="margin:0.7rem 0 0 0;color:#c5cedb; line-height: 1.8;">
            <strong style="color:#ffffff">{fmt_int(row['polices'])}</strong> polices · {row['pct_polices']:.0f}%<br>
            <strong style="color:#ffffff">{fmt_mds(row['capital'])}</strong> de capital · {row['pct_capital']:.0f}%<br>
            <strong style="color:#ffffff">{fmt_mds(row['cep'])}</strong> de CEP · {row['pct_cep']:.0f}%
          </p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# MATRICE ZONE × CLASSE
# =============================================================================
st.markdown("### Matrice Zone × Classe — CEP cumulé")

mat_cep = df_y.pivot_table(
    index="ZONE_FINALE", columns="VULNERABILITE_CLASSE",
    values="CEP_M", aggfunc="sum", fill_value=0,
) / 1000

zones_order = [z for z in ["0", "I", "IIa", "IIb", "III"] if z in mat_cep.index]
classes_order = [c for c in ["B", "C", "D"] if c in mat_cep.columns]
mat_cep = mat_cep.loc[zones_order, classes_order]

fig = go.Figure(data=go.Heatmap(
    z=mat_cep.values,
    x=[f"Classe {c}" for c in mat_cep.columns],
    y=[f"Zone {z}" for z in mat_cep.index],
    colorscale=[
        [0, "rgba(255,255,255,0.02)"],
        [0.15, "#2a3448"],
        [0.4, "#8c4a0f"],
        [0.7, "#cc3b3b"],
        [1, "#ff4757"],
    ],
    text=[[f"<b>{v:.1f}</b><br>Mds DA" for v in row] for row in mat_cep.values],
    texttemplate="%{text}",
    textfont=dict(size=14, color="#ffffff"),
    colorbar=dict(
        title=dict(text="CEP (Mds DA)", font=dict(color="#c5cedb")),
        tickfont=dict(color="#c5cedb"),
    ),
    hovertemplate="<b>%{y} × %{x}</b><br>CEP : %{z:.2f} Mds DA<extra></extra>",
))
fig.update_layout(
    height=440,
    yaxis=dict(autorange="reversed"),
)
apply_plotly_dark(fig)
st.plotly_chart(fig, use_container_width=True)

# Top 2 cellules
mat_long = mat_cep.stack().reset_index()
mat_long.columns = ["Zone", "Classe", "CEP_Mds"]
mat_long = mat_long.sort_values("CEP_Mds", ascending=False).head(2)

cc1, cc2 = st.columns(2)
for col, (_, row) in zip([cc1, cc2], mat_long.iterrows()):
    with col:
        st.markdown(f"""
        <div class="insight-card critical">
          <h4>{row['Zone']} × Classe {row['Classe']}</h4>
          <p>Concentre <strong>{row['CEP_Mds']:.1f} Mds DA</strong> de CEP, la cellule la plus exposée de la matrice.</p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# GRILLE DE VULNÉRABILITÉ (référence)
# =============================================================================
st.markdown("### Référentiel de classification")
with st.expander("Grille de vulnérabilité utilisée pour la classification"):
    grille = [
        ("Bien immobilier", "< 3 M DA",        "B", 0.85, "Habitat individuel, maçonnerie traditionnelle"),
        ("Bien immobilier", "3 à 10 M DA",     "C", 0.65, "Logement moderne, maçonnerie chaînée"),
        ("Bien immobilier", "10 à 30 M DA",    "C", 0.50, "Immeuble collectif moderne, portiques béton armé"),
        ("Bien immobilier", "≥ 30 M DA",       "D", 0.35, "Grande résidence, voiles béton armé conforme"),
        ("Commerciale",     "< 5 M DA",        "B", 0.75, "Petit local commercial de RDC"),
        ("Commerciale",     "5 à 20 M DA",     "C", 0.55, "Commerce moyen, béton armé"),
        ("Commerciale",     "20 à 100 M DA",   "C", 0.45, "Centre commercial, immeuble de bureau"),
        ("Commerciale",     "≥ 100 M DA",      "D", 0.35, "Grande surface, complexe conforme"),
        ("Industrielle",    "< 10 M DA",       "C", 0.60, "Atelier, petite industrie"),
        ("Industrielle",    "10 à 100 M DA",   "C", 0.50, "Usine moyenne, structure métallique ou béton armé"),
        ("Industrielle",    "100 à 500 M DA",  "D", 0.40, "Complexe industriel, étude parasismique spécifique"),
        ("Industrielle",    "≥ 500 M DA",      "D", 0.30, "Grande industrie, conformité normes spécifiques"),
    ]
    grille_df = pd.DataFrame(grille, columns=["Catégorie", "Tranche capital", "Classe", "V", "Typologie"])
    st.dataframe(grille_df, use_container_width=True, hide_index=True,
                 column_config={"V": st.column_config.NumberColumn(format="%.2f")})

st.caption("CEP = Capital × V × A  —  V coefficient de vulnérabilité (proxy basé sur type et tranche de capital)  ·  A coefficient d'accélération de zone.")
