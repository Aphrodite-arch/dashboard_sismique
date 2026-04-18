"""
Alertes & Limites — Surveillance temps réel des accumulations vs seuils de rétention.

En mode BRUT (100% du risque souscrit) : seuils commune 300/150/50 M DA.
En mode NET GAM (30% conservé) : seuils recalibrés 200/100/50 M DA net,
correspondant à 40%/20%/10% de la rétention brute implicite (1 667 M DA).

La reclassification entre les deux modes fait passer le nombre de communes
CRITIQUES de 14 (brut) à 3 (net : Alger, Oran, Sétif). Les 11 autres
basculent en ATTENTION ou SURVEILLANCE — politique plus ciblée sans
sur-réglementation du réseau commercial.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from theme import apply_theme, apply_plotly_dark, ACCENT_RED, ACCENT_ORANGE, ACCENT_GREEN, ACCENT_YELLOW
from utils import (
    points_chauds_wilaya_view, points_chauds_commune_view,
    COLOR_CRITICITE, fmt_int, fmt_m, status_dot,
    render_view_toggle, is_net_view, view_label,
    get_seuils_commune, get_seuils_wilaya,
    RETENTION_NETTE_EVENT, RETENTION_BRUTE_IMPLICITE,
)

st.set_page_config(page_title="Alertes & Limites", layout="wide")
apply_theme()
render_view_toggle()
NET = is_net_view()

st.markdown(f"""
<div class="hero-block">
  <h1>Alertes & Limites</h1>
  <p>Surveillance des accumulations géographiques et règles de souscription différenciées selon le niveau de criticité atteint — vision {view_label(short=True)}.</p>
</div>
""", unsafe_allow_html=True)

df_w = points_chauds_wilaya_view()
df_c = points_chauds_commune_view()
seuils_c = get_seuils_commune()
seuils_w = get_seuils_wilaya()


# =============================================================================
# BANDEAU EXPLICATIF MODE ACTIF
# =============================================================================
if NET:
    st.markdown(f"""
    <div class="insight-card info">
      <h4>Seuils recalibrés sur la rétention nette GAM</h4>
      <p>Rétention nette par événement : <strong>{RETENTION_NETTE_EVENT:.0f} M DA</strong> ·
      Rétention brute implicite : <strong>{RETENTION_BRUTE_IMPLICITE:,.0f} M DA</strong><br>
      Critique ≥ 40% de la rétention brute ({seuils_c['Critique']} M DA net) ·
      Attention ≥ 20% ({seuils_c['Attention']} M DA net) ·
      Surveillance ≥ 10% ({seuils_c['Surveillance']} M DA net)
      </p>
    </div>
    """.replace(",", " "), unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="insight-card warning">
      <h4>Seuils bruts — référentiel Phase 2</h4>
      <p>Ces seuils classent les communes sur le risque total souscrit (100% du capital).
      Pour une vue opérationnelle décisionnelle GAM, basculer en vision nette dans le panneau latéral.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# SYNTHÈSE DES ALERTES EN COURS
# =============================================================================
st.markdown("### Synthèse des alertes en cours")

crit_w_cnt = (df_w["Niveau_clean"] == "Critique").sum()
warn_w_cnt = (df_w["Niveau_clean"] == "Attention").sum()
mon_w_cnt  = (df_w["Niveau_clean"] == "Surveillance").sum()
crit_c_cnt = (df_c["Niveau_clean"] == "Critique").sum()
warn_c_cnt = (df_c["Niveau_clean"] == "Attention").sum()
mon_c_cnt  = (df_c["Niveau_clean"] == "Surveillance").sum()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="insight-card critical">
      <h4>{status_dot("Critique")} Critique</h4>
      <p style="font-size:1.5rem;font-weight:700;color:#ffffff;margin:0.3rem 0">{crit_w_cnt} wilayas · {crit_c_cnt} communes</p>
      <p>Action immédiate requise — autorisation Direction Technique obligatoire pour tout nouveau capital.</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="insight-card warning">
      <h4>{status_dot("Attention")} Attention</h4>
      <p style="font-size:1.5rem;font-weight:700;color:#ffffff;margin:0.3rem 0">{warn_w_cnt} wilayas · {warn_c_cnt} communes</p>
      <p>Validation souscripteur senior requise. Étude de structure si capital supérieur à 50 M DA brut.</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="insight-card" style="border-left-color: {ACCENT_YELLOW}">
      <h4>{status_dot("Surveillance")} Surveillance</h4>
      <p style="font-size:1.5rem;font-weight:700;color:#ffffff;margin:0.3rem 0">{mon_w_cnt} wilayas · {mon_c_cnt} communes</p>
      <p>Souscription standard avec reporting trimestriel à la Direction Technique.</p>
    </div>
    """, unsafe_allow_html=True)

with c4:
    normal_w = len(df_w) - crit_w_cnt - warn_w_cnt - mon_w_cnt
    normal_c = len(df_c) - crit_c_cnt - warn_c_cnt - mon_c_cnt
    st.markdown(f"""
    <div class="insight-card success">
      <h4>{status_dot("Normal")} Normal</h4>
      <p style="font-size:1.5rem;font-weight:700;color:#ffffff;margin:0.3rem 0">{normal_w} wilayas · {normal_c} communes</p>
      <p>Souscription standard sans restriction additionnelle.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# RECLASSIFICATION BRUT → NET (si pertinent)
# =============================================================================
if NET:
    st.markdown("---")
    st.markdown("### Effet du passage brut → net sur la classification")

    # En brut, les seuils sont 300/150/50 et produisent 14 communes critiques
    # En net (projection × 30% + seuils 200/100/50) on obtient 3/9/2 (selon la note)
    repart_brut = {"Critique": 14, "Attention": 29, "Surveillance": 57, "Normal": 918}
    repart_net  = {"Critique": crit_c_cnt, "Attention": warn_c_cnt,
                   "Surveillance": mon_c_cnt, "Normal": normal_c}

    fig = go.Figure()
    for niveau, color in [("Critique", "#ff4757"), ("Attention", "#ff7f50"),
                          ("Surveillance", "#ffd32a"), ("Normal", "#2ed573")]:
        fig.add_trace(go.Bar(
            name=niveau,
            x=["Classification brute", "Classification nette GAM"],
            y=[repart_brut[niveau], repart_net[niveau]],
            marker=dict(color=color, line=dict(color='rgba(255,255,255,0.15)', width=1)),
            text=[repart_brut[niveau], repart_net[niveau]],
            textposition="inside",
            textfont=dict(color="#ffffff", size=12),
        ))
    fig.update_layout(
        height=380,
        barmode="stack",
        yaxis_title="Nombre de communes",
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div class="insight-card success">
      <h4>Politique plus ciblée</h4>
      <p>Le nombre de communes véritablement critiques du point de vue opérationnel GAM passe de <strong>14 en brut</strong>
      à <strong>{crit_c_cnt} en net</strong>. Les autres basculent en Attention ou Surveillance — elles restent à surveiller
      mais ne justifient plus les mesures les plus contraignantes (autorisation Direction Technique obligatoire, audit systématique).
      Cela évite une sur-réglementation du réseau commercial sans dégrader la qualité du pilotage du risque.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# SEUILS DE DÉCLENCHEMENT
# =============================================================================
st.markdown("---")
st.markdown(f"### Seuils de déclenchement actifs — {view_label(short=True)}")

col_c, col_w = st.columns(2)

with col_c:
    st.markdown("##### Niveau commune (CEP)")
    seuils_rows_c = [
        ("Critique",     f"≥ {seuils_c['Critique']} M DA",
         "Autorisation Direction Technique obligatoire", "#ff4757"),
        ("Attention",    f"{seuils_c['Attention']} à {seuils_c['Critique']} M DA",
         "Validation souscripteur senior", "#ff7f50"),
        ("Surveillance", f"{seuils_c['Surveillance']} à {seuils_c['Attention']} M DA",
         "Souscription standard avec signalement", "#ffd32a"),
        ("Normal",       f"< {seuils_c['Surveillance']} M DA",
         "Souscription standard", "#2ed573"),
    ]
    for niveau, seuil, regle, color in seuils_rows_c:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03);
                    border-left: 4px solid {color};
                    padding: 0.8rem 1.1rem;
                    border-radius: 10px;
                    margin-bottom: 0.5rem;
                    border: 1px solid rgba(255,255,255,0.05);">
          <strong style="color:{color}">{niveau}</strong> · <span style="color:#c5cedb">{seuil}</span><br>
          <span style="color:#8a94a8; font-size:0.88rem">{regle}</span>
        </div>
        """, unsafe_allow_html=True)

with col_w:
    st.markdown("##### Niveau wilaya (CEP)")
    seuils_rows_w = [
        ("Critique",     f"≥ {seuils_w['Critique']} M DA",
         "Revue mensuelle ComEx", "#ff4757"),
        ("Attention",    f"{seuils_w['Attention']} à {seuils_w['Critique']} M DA",
         "Revue trimestrielle", "#ff7f50"),
        ("Surveillance", f"{seuils_w['Surveillance']} à {seuils_w['Attention']} M DA",
         "Reporting semestriel", "#ffd32a"),
        ("Normal",       f"< {seuils_w['Surveillance']} M DA",
         "Aucune contrainte additionnelle", "#2ed573"),
    ]
    for niveau, seuil, regle, color in seuils_rows_w:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03);
                    border-left: 4px solid {color};
                    padding: 0.8rem 1.1rem;
                    border-radius: 10px;
                    margin-bottom: 0.5rem;
                    border: 1px solid rgba(255,255,255,0.05);">
          <strong style="color:{color}">{niveau}</strong> · <span style="color:#c5cedb">{seuil}</span><br>
          <span style="color:#8a94a8; font-size:0.88rem">{regle}</span>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# COMMUNES EN ALERTE CRITIQUE — liste opérationnelle
# =============================================================================
st.markdown("---")
st.markdown("### Communes en alerte critique — action immédiate")

df_crit = df_c[df_c["Niveau_clean"] == "Critique"].copy()
df_crit["CEP (M DA)"] = pd.to_numeric(df_crit["CEP (M DA)"], errors="coerce")
df_crit = df_crit.sort_values("CEP (M DA)", ascending=False)

if len(df_crit):
    fig = go.Figure(go.Bar(
        x=df_crit["CEP (M DA)"],
        y=df_crit["Commune"] + " · " + df_crit["Wilaya"],
        orientation="h",
        marker=dict(color=ACCENT_RED, line=dict(color='rgba(255,255,255,0.15)', width=1)),
        text=[f"{v:.0f} M DA" for v in df_crit["CEP (M DA)"]],
        textposition="outside",
        textfont=dict(color="#ffffff"),
        hovertemplate="<b>%{y}</b><br>CEP : %{x:,.0f} M DA<extra></extra>",
    ))
    fig.update_layout(
        height=max(380, len(df_crit) * 30),
        xaxis_title=f"CEP (M DA) — {view_label(short=True)}",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=220, r=80),
        showlegend=False,
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune commune en alerte critique actuellement.")


# =============================================================================
# PLAFONDS DE SOUSCRIPTION PAR NIVEAU — TOUJOURS EN BRUT
# =============================================================================
st.markdown("---")
st.markdown("### Plafonds de souscription par niveau de criticité")
st.caption("Plafonds exprimés en capital brut — GAM reste engagée face à l'assuré pour 100% du capital souscrit.")

plafonds = pd.DataFrame([
    ("Critique",     "50 M DA",   "Direction Technique obligatoire",  "Audit technique + certification parasismique"),
    ("Attention",    "100 M DA",  "Souscripteur senior",               "Étude structure si capital > 50 M DA brut"),
    ("Surveillance", "250 M DA",  "Standard avec signalement",         "Reporting trimestriel"),
    ("Normal",       "Pas de plafond spécifique", "Standard",          "Aucune action additionnelle"),
], columns=["Niveau", "Plafond nouveau capital (brut)", "Validation requise", "Action complémentaire"])

st.dataframe(plafonds, use_container_width=True, hide_index=True)


# =============================================================================
# FOCUS WILAYAS CRITIQUES
# =============================================================================
st.markdown("---")
st.markdown("### Focus wilayas critiques")

df_w_crit = df_w[df_w["Niveau_clean"] == "Critique"].copy()
df_w_crit["CEP (M DA)"] = pd.to_numeric(df_w_crit["CEP (M DA)"], errors="coerce")
df_w_crit["Capital (M DA)"] = pd.to_numeric(df_w_crit["Capital (M DA)"], errors="coerce")
df_w_crit["Part CEP portefeuille %"] = pd.to_numeric(df_w_crit["Part CEP portefeuille %"], errors="coerce")
df_w_crit = df_w_crit.sort_values("CEP (M DA)", ascending=False).head(4)

if len(df_w_crit):
    cols = st.columns(min(len(df_w_crit), 4))
    for i, (_, row) in enumerate(df_w_crit.iterrows()):
        with cols[i]:
            st.markdown(f"""
            <div class="insight-card critical">
              <h4>{row['Wilaya']}</h4>
              <p style="line-height:1.8">
                <strong style="color:#ffffff">{row['CEP (M DA)']:,.0f} M DA</strong> de CEP<br>
                <strong style="color:#ffffff">{int(row['Nb polices']):,}</strong> polices actives<br>
                <strong style="color:#ffffff">{row['Part CEP portefeuille %']:.1f}%</strong> du portefeuille total
              </p>
            </div>
            """.replace(",", " "), unsafe_allow_html=True)
else:
    st.info("Aucune wilaya en alerte critique dans la configuration actuelle.")


st.markdown("""
<div class="insight-card info" style="margin-top:1.5rem">
  <h4>Rappel opérationnel</h4>
  <p>Toute nouvelle police supérieure à 50 M DA brut sur une commune critique requiert une autorisation explicite de la Direction Technique,
  accompagnée d'un audit technique de conformité aux normes parasismiques et d'un certificat de moins de 5 ans.</p>
</div>
""", unsafe_allow_html=True)
