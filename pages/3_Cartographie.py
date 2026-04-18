"""
Cartographie — Points chauds, concentration géographique et visualisation territoriale.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from theme import apply_theme, apply_plotly_dark, ACCENT_RED
from utils import (
    points_chauds_wilaya_view, points_chauds_commune_view, load_pareto,
    WILAYA_CENTROIDS, COLOR_CRITICITE,
    render_view_toggle, is_net_view, view_label, project_value,
    get_seuils_commune, get_seuils_wilaya,
)

st.set_page_config(page_title="Cartographie", layout="wide")
apply_theme()
render_view_toggle()
NET = is_net_view()

st.markdown("""
<div class="hero-block">
  <h1>Cartographie</h1>
  <p>Identification des zones de surconcentration du portefeuille et visualisation géographique des expositions.</p>
</div>
""", unsafe_allow_html=True)

df_w = points_chauds_wilaya_view()
df_c = points_chauds_commune_view()
df_p = load_pareto()

# En mode net, les CEP ont été projetés ; on retrie par CEP décroissant
if NET:
    df_w = df_w.sort_values("CEP_M_num", ascending=False).reset_index(drop=True)
    df_w["Rang"] = df_w.index + 1
    df_c = df_c.sort_values("CEP_M_num", ascending=False).reset_index(drop=True)
    df_c["Rang"] = df_c.index + 1


# =============================================================================
# RÉPARTITION DES NIVEAUX
# =============================================================================
st.markdown("### Répartition des niveaux de criticité")

c1, c2 = st.columns(2)

with c1:
    st.markdown("##### Wilayas (54 actives)")
    counts_w = df_w["Niveau_clean"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts_w.index,
        values=counts_w.values,
        hole=0.55,
        marker=dict(
            colors=[COLOR_CRITICITE.get(n, "#5b6374") for n in counts_w.index],
            line=dict(color='#0a0e1a', width=2),
        ),
        textinfo="label+value",
        textfont=dict(color="#ffffff", size=13),
    ))
    fig.update_layout(height=340, showlegend=True,
                      legend=dict(orientation="h", y=-0.1))
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("##### Communes (1 018 actives)")
    counts_c = df_c["Niveau_clean"].value_counts()
    fig2 = go.Figure(go.Pie(
        labels=counts_c.index,
        values=counts_c.values,
        hole=0.55,
        marker=dict(
            colors=[COLOR_CRITICITE.get(n, "#5b6374") for n in counts_c.index],
            line=dict(color='#0a0e1a', width=2),
        ),
        textinfo="label+value",
        textfont=dict(color="#ffffff", size=13),
    ))
    fig2.update_layout(height=340, showlegend=True,
                       legend=dict(orientation="h", y=-0.1))
    apply_plotly_dark(fig2)
    st.plotly_chart(fig2, use_container_width=True)


# =============================================================================
# ONGLETS
# =============================================================================
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["Top wilayas", "Top communes", "Concentration", "Carte Algérie"])

with tab1:
    n_w = st.slider("Nombre de wilayas à afficher", 5, 30, 15, key="nw")
    top_w = df_w.head(n_w).copy()
    top_w["CEP (M DA)"] = pd.to_numeric(top_w["CEP (M DA)"], errors="coerce")

    fig = go.Figure(go.Bar(
        x=top_w["CEP (M DA)"],
        y=top_w["Wilaya"],
        orientation="h",
        marker=dict(
            color=[COLOR_CRITICITE.get(n, "#5b6374") for n in top_w["Niveau_clean"]],
            line=dict(color='rgba(255,255,255,0.15)', width=1),
        ),
        text=[f"{v:,.0f} M DA".replace(",", " ") for v in top_w["CEP (M DA)"]],
        textposition="outside",
        textfont=dict(color="#ffffff"),
        hovertemplate="<b>%{y}</b><br>CEP : %{x:,.0f} M DA<extra></extra>",
    ))
    fig.update_layout(
        height=max(400, n_w * 30),
        xaxis_title="CEP cumulé (M DA)",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=140, r=80),
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        top_w[["Rang", "Wilaya", "Niveau", "Nb polices", "Capital (M DA)", "CEP (M DA)", "Part CEP portefeuille %"]],
        use_container_width=True, hide_index=True,
    )


with tab2:
    niveau_filter = st.multiselect(
        "Niveau de criticité",
        ["Critique", "Attention", "Surveillance", "Normal"],
        default=["Critique", "Attention"],
    )
    df_c_f = df_c[df_c["Niveau_clean"].isin(niveau_filter)].copy()
    df_c_f["CEP (M DA)"] = pd.to_numeric(df_c_f["CEP (M DA)"], errors="coerce")

    st.caption(f"{len(df_c_f):,} communes correspondent aux niveaux sélectionnés".replace(",", " "))

    df_c_f_top = df_c_f.head(30)
    fig = go.Figure(go.Bar(
        x=df_c_f_top["CEP (M DA)"],
        y=df_c_f_top["Commune"] + " (" + df_c_f_top["Wilaya"] + ")",
        orientation="h",
        marker=dict(
            color=[COLOR_CRITICITE.get(n, "#5b6374") for n in df_c_f_top["Niveau_clean"]],
            line=dict(color='rgba(255,255,255,0.15)', width=1),
        ),
        text=[f"{v:.0f}" for v in df_c_f_top["CEP (M DA)"]],
        textposition="outside",
        textfont=dict(color="#ffffff"),
    ))
    fig.update_layout(
        height=max(400, min(30, len(df_c_f_top)) * 26),
        xaxis_title="CEP commune (M DA)",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=220, r=60),
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df_c_f[["Rang", "Commune", "Wilaya", "Zone RPA", "Niveau", "Nb polices", "Capital (M DA)", "CEP (M DA)"]],
        use_container_width=True, hide_index=True, height=400,
    )


with tab3:
    st.markdown("##### Concentration — part cumulée du CEP par rang de commune")

    df_p["CEP cumulé (M DA)"] = pd.to_numeric(df_p["CEP cumulé (M DA)"], errors="coerce")
    df_p["Part cumulée %"]    = pd.to_numeric(df_p["Part cumulée %"], errors="coerce")
    df_p["Rang"]              = pd.to_numeric(df_p["Rang"], errors="coerce")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_p["Rang"],
        y=df_p["Part cumulée %"],
        mode="lines",
        line=dict(color=ACCENT_RED, width=3),
        fill="tozeroy",
        fillcolor="rgba(255,71,87,0.15)",
        hovertemplate="Rang %{x}<br>Part cumulée : %{y:.1f}%<extra></extra>",
        name="Concentration",
    ))

    reperes = [(10, "10 premières"), (50, "50 premières"), (100, "100 premières")]
    for rang, label in reperes:
        row = df_p[df_p["Rang"] == rang]
        if len(row):
            y_val = row["Part cumulée %"].iloc[0]
            fig.add_trace(go.Scatter(
                x=[rang], y=[y_val], mode="markers+text",
                marker=dict(size=14, color=ACCENT_RED,
                            line=dict(color="#ffffff", width=2)),
                text=[f"<b>{label}<br>{y_val:.1f}%</b>"],
                textposition="top center",
                textfont=dict(color="#ffffff"),
                showlegend=False,
                hoverinfo="skip",
            ))

    fig.add_hline(y=80, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                  annotation_text="Seuil 80%",
                  annotation_font=dict(color="#c5cedb"))

    fig.update_layout(
        height=460,
        xaxis_title="Rang de commune (échelle logarithmique)",
        yaxis_title="% cumulé du CEP",
        xaxis_type="log",
        yaxis=dict(range=[0, 105]),
        showlegend=False,
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight-card success">
      <h4>Implication opérationnelle</h4>
      <p>Une action ciblée sur les <strong>100 premières communes</strong> couvre plus de <strong>82%</strong> de l'exposition totale.
      Cela permet de concentrer l'effort de surveillance et de gestion sans pénaliser 92% du territoire.</p>
    </div>
    """, unsafe_allow_html=True)


with tab4:
    st.markdown("##### Carte interactive — CEP par wilaya")
    st.caption("Chaque bulle représente une wilaya. Taille proportionnelle au CEP, couleur selon le niveau de criticité.")

    map_data = []
    for _, row in df_w.iterrows():
        code = row.get("Code wilaya") or row.get("Code")
        if pd.isna(code): continue
        try:
            code = int(code)
            if code in WILAYA_CENTROIDS:
                lat, lon, name = WILAYA_CENTROIDS[code]
                cep = pd.to_numeric(row["CEP (M DA)"], errors="coerce")
                if not pd.isna(cep) and cep > 0:
                    map_data.append({
                        "lat": lat, "lon": lon,
                        "wilaya": row["Wilaya"],
                        "cep": cep,
                        "niveau": row["Niveau_clean"],
                        "nb_polices": row["Nb polices"],
                        "capital": row["Capital (M DA)"],
                    })
        except (ValueError, TypeError):
            continue

    df_map = pd.DataFrame(map_data)

    if len(df_map):
        fig = px.scatter_mapbox(
            df_map,
            lat="lat", lon="lon",
            size="cep", color="niveau",
            hover_name="wilaya",
            hover_data={
                "cep": ":,.0f",
                "nb_polices": True,
                "capital": ":,.0f",
                "lat": False, "lon": False, "niveau": False,
            },
            color_discrete_map=COLOR_CRITICITE,
            size_max=55,
            zoom=4.8,
            center={"lat": 32.5, "lon": 2.5},
            mapbox_style="carto-darkmatter",
            labels={"cep": "CEP (M DA)", "nb_polices": "Polices", "capital": "Capital (M DA)"},
        )
        fig.update_layout(
            height=620,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                title=dict(text="Niveau", font=dict(color="#ffffff")),
                orientation="h", y=-0.05, x=0.5, xanchor="center",
                font=dict(color="#ffffff"),
                bgcolor='rgba(17,23,42,0.7)',
            ),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Pas de données cartographiques disponibles.")


# =============================================================================
# CLUSTERS URBAINS
# =============================================================================
st.markdown("---")
st.markdown("### Clusters urbains — risque co-localisé")
st.caption("Un séisme unique peut frapper plusieurs communes contiguës simultanément. Les clusters révèlent la concentration réelle à l'échelle d'une agglomération.")

clusters_brut = [
    ("Agglomération Alger",    2385, 5, "Alger centre, Cheraga, Rouiba, Staoueli, Alger-100"),
    ("Agglomération Sétif",    1441, 2, "Sétif chef-lieu, El Eulma"),
    ("Agglomération Oran",     1154, 31, "Oran et communes avoisinantes"),
    ("Tizi-Ouzou",              476, 1, "Tizi-Ouzou chef-lieu"),
    ("Bordj B. Arreridj",       442, 1, "Bordj Bou Arreridj"),
    ("Constantine",             374, 1, "Constantine chef-lieu"),
]
# Palette selon seuils actifs
seuils_c = get_seuils_commune()
def _color(v):
    if v >= seuils_c["Critique"] * 2: return "#ff4757"
    if v >= seuils_c["Critique"]:     return "#ff4757"
    if v >= seuils_c["Attention"]:    return "#ff7f50"
    if v >= seuils_c["Surveillance"]: return "#ffd32a"
    return "#2ed573"

clusters = []
for nom, cep, n, detail in clusters_brut:
    cep_aff = project_value(cep)
    clusters.append((nom, cep_aff, n, _color(cep_aff), detail))

df_cl = pd.DataFrame(clusters, columns=["Cluster", "CEP (M DA)", "Nb communes", "Couleur", "Détail"])

fig = go.Figure(go.Bar(
    x=df_cl["CEP (M DA)"],
    y=df_cl["Cluster"],
    orientation="h",
    marker=dict(
        color=df_cl["Couleur"],
        line=dict(color='rgba(255,255,255,0.15)', width=1),
    ),
    text=[f"<b>{v:,.0f} M DA</b>  ·  {n} commune(s)".replace(",", " ") for v, n in zip(df_cl["CEP (M DA)"], df_cl["Nb communes"])],
    textposition="outside",
    textfont=dict(color="#ffffff"),
    customdata=df_cl[["Détail"]],
    hovertemplate="<b>%{y}</b><br>CEP : %{x:,.0f} M DA<br>%{customdata[0]}<extra></extra>",
))
fig.update_layout(
    height=380,
    xaxis_title=f"CEP agrégé du cluster (M DA) — {view_label(short=True)}",
    yaxis=dict(autorange="reversed"),
    margin=dict(l=200, r=140),
    showlegend=False,
)
apply_plotly_dark(fig)
st.plotly_chart(fig, use_container_width=True)

alger_cep = project_value(2385)
alger_isole = project_value(860)
st.markdown(f"""
<div class="insight-card critical">
  <h4>Zone-scénario dominante</h4>
  <p>L'agglomération d'Alger cumule <strong>{alger_cep:,.0f} M DA</strong> de CEP sur 5 communes contiguës — soit près de <strong>{alger_cep/alger_isole:.1f}x</strong> le CEP de la commune la plus exposée prise isolément.
  C'est la zone-scénario de référence pour le dimensionnement du programme de réassurance.</p>
</div>
""".replace(",", " "), unsafe_allow_html=True)
