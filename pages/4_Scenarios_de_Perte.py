"""
Scénarios de Perte — Courbes de perte par période de retour et contribution aux pertes.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from theme import apply_theme, apply_plotly_dark, ACCENT_RED, ACCENT_ORANGE
from utils import (
    load_aep, load_oep, load_sources_scenarios, load_wilayas_scenarios,
    load_events_scenarios, load_distribution,
    fmt_m, fmt_int,
    render_view_toggle, is_net_view, project_value, view_label,
    QS_RATIO_CONSERVE,
)

st.set_page_config(page_title="Scénarios de Perte", layout="wide")
apply_theme()
render_view_toggle()
NET = is_net_view()

st.markdown("""
<div class="hero-block">
  <h1>Scénarios de Perte</h1>
  <p>Courbes de perte annuelle cumulée et événementielle, contribution par source sismique et par wilaya aux pertes du portefeuille.</p>
</div>
""", unsafe_allow_html=True)

df_aep = load_aep()
df_oep = load_oep()
df_src = load_sources_scenarios()
df_wloss = load_wilayas_scenarios()
df_events = load_events_scenarios()
df_dist = load_distribution()


# =============================================================================
# STATS
# =============================================================================
st.markdown("### Statistiques annuelles de référence")

stats = {}
for _, row in df_dist.iterrows():
    lib = str(row["Statistique"]).strip()
    val = pd.to_numeric(row.get("Valeur (M DA)"), errors="coerce")
    if not pd.isna(val):
        stats[lib] = val

c1, c2, c3, c4 = st.columns(4)
c1.metric("Perte moyenne annuelle", fmt_m(project_value(stats.get("Moyenne (AAL)", 1226))))
c2.metric("Médiane annuelle", fmt_m(project_value(stats.get("Médiane", 432))))
c3.metric("Décile 90 (1 an sur 10)", fmt_m(project_value(stats.get("p90", 3220))))
c4.metric("Centile 99 (1 an sur 100)", fmt_m(project_value(stats.get("p99", 10383))))


# =============================================================================
# ONGLETS
# =============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Perte annuelle cumulée",
    "Perte événementielle",
    "Par source sismique",
    "Par wilaya",
    "Événements de référence",
])

with tab1:
    st.markdown("##### Probabilité de dépassement de la perte annuelle cumulée")

    df_aep["Période retour (ans)"] = pd.to_numeric(df_aep["Période retour (ans)"], errors="coerce")
    df_aep["PML (M DA)"] = pd.to_numeric(df_aep["PML (M DA)"], errors="coerce")
    pml_display = df_aep["PML (M DA)"] * (QS_RATIO_CONSERVE if NET else 1.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_aep["Période retour (ans)"],
        y=pml_display,
        mode="lines+markers",
        line=dict(color=ACCENT_RED, width=3),
        marker=dict(size=10, color=ACCENT_RED, line=dict(color='#ffffff', width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(255,71,87,0.15)",
        hovertemplate="<b>Retour %{x} ans</b><br>Perte : %{y:,.0f} M DA<extra></extra>",
    ))

    for rp_ref in [100, 250, 500]:
        row = df_aep[df_aep["Période retour (ans)"] == rp_ref]
        if len(row):
            y_val = project_value(float(row["PML (M DA)"].iloc[0]))
            fig.add_annotation(
                x=rp_ref, y=y_val,
                text=f"<b>{rp_ref} ans<br>{y_val:,.0f} M DA</b>".replace(",", " "),
                showarrow=True, arrowhead=2, arrowcolor="rgba(255,255,255,0.4)",
                ax=-20, ay=-40,
                bgcolor="rgba(17,23,42,0.9)",
                bordercolor=ACCENT_RED, borderwidth=1,
                font=dict(color="#ffffff"),
            )

    fig.update_layout(
        height=460,
        xaxis_title="Période de retour (ans) — échelle logarithmique",
        yaxis_title=f"Perte annuelle cumulée (M DA) — {view_label(short=True)}",
        xaxis_type="log",
        showlegend=False,
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Sélecteur interactif")
    rp_select = st.select_slider(
        "Période de retour",
        options=sorted(df_aep["Période retour (ans)"].dropna().astype(int).tolist()),
        value=100,
    )
    row_sel = df_aep[df_aep["Période retour (ans)"] == rp_select].iloc[0]
    proba = pd.to_numeric(row_sel["Proba dépassement annuelle"], errors="coerce")

    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Période de retour", f"{rp_select} ans")
    cc2.metric("Probabilité annuelle", f"{proba*100:.2f} %" if not pd.isna(proba) else "—")
    cc3.metric("Perte associée", fmt_m(project_value(row_sel["PML (M DA)"])))

    df_aep_display = df_aep[["Période retour (ans)", "Proba dépassement annuelle", "PML (M DA)"]].copy()
    if NET:
        df_aep_display["PML (M DA)"] = df_aep_display["PML (M DA)"] * QS_RATIO_CONSERVE
    st.dataframe(
        df_aep_display.rename(columns={"Proba dépassement annuelle": "Probabilité annuelle"}),
        use_container_width=True, hide_index=True,
    )


with tab2:
    st.markdown(f"##### Perte maximale sur un événement unique — {view_label(short=True)}")

    df_oep["Période retour (ans)"] = pd.to_numeric(df_oep["Période retour (ans)"], errors="coerce")
    df_oep["OEP PML (M DA)"] = pd.to_numeric(df_oep["OEP PML (M DA)"], errors="coerce")
    oep_display = df_oep["OEP PML (M DA)"] * (QS_RATIO_CONSERVE if NET else 1.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_oep["Période retour (ans)"],
        y=oep_display,
        mode="lines+markers",
        line=dict(color=ACCENT_ORANGE, width=3),
        marker=dict(size=10, color=ACCENT_ORANGE, line=dict(color='#ffffff', width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(255,165,2,0.15)",
        hovertemplate="<b>Retour %{x} ans</b><br>Perte événement : %{y:,.0f} M DA<extra></extra>",
    ))
    fig.update_layout(
        height=460,
        xaxis_title="Période de retour (ans)",
        yaxis_title="Perte événement unique (M DA)",
        xaxis_type="log",
        showlegend=False,
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)


with tab3:
    st.markdown("##### Contribution de chaque source sismique aux pertes totales")

    df_src["Part %"] = pd.to_numeric(df_src["Part %"], errors="coerce")

    fig = go.Figure(go.Pie(
        labels=df_src["Source sismique"],
        values=df_src["Part %"],
        hole=0.5,
        marker=dict(
            colors=["#ff4757", "#ff7f50", "#ffa502", "#ffd32a", "#4fa9e3", "#5b6374"],
            line=dict(color='#0a0e1a', width=2),
        ),
        textinfo="label+percent",
        textfont=dict(color="#ffffff", size=12),
    ))
    fig.update_layout(
        height=480,
        legend=dict(orientation="v", y=0.5, font=dict(color="#ffffff")),
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight-card critical">
      <h4>Source dominante</h4>
      <p>La source Tellienne centrale (Alger-Blida-Boumerdès) concentre à elle seule <strong>70%</strong> du risque du portefeuille.
      Toute la stratégie de couverture doit être calibrée sur cette source.</p>
    </div>
    """, unsafe_allow_html=True)


with tab4:
    st.markdown("##### Contribution de chaque wilaya aux pertes")

    n_wil = st.slider("Nombre de wilayas à afficher", 5, 20, 15)
    top_w = df_wloss.head(n_wil).copy()
    top_w["Part %"] = pd.to_numeric(top_w["Part %"], errors="coerce")

    fig = go.Figure(go.Bar(
        x=top_w["Part %"],
        y=top_w["Wilaya"],
        orientation="h",
        marker=dict(color=ACCENT_RED, line=dict(color='rgba(255,255,255,0.15)', width=1)),
        text=[f"{v:.1f} %" for v in top_w["Part %"]],
        textposition="outside",
        textfont=dict(color="#ffffff"),
    ))
    fig.update_layout(
        height=max(400, n_wil * 30),
        xaxis_title="Contribution aux pertes (%)",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=140, r=60),
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)


with tab5:
    st.markdown("##### Top 30 événements de référence les plus coûteux")

    df_events["Magnitude"] = pd.to_numeric(df_events["Magnitude"], errors="coerce")
    df_events["Perte (M DA)"] = pd.to_numeric(df_events["Perte (M DA)"], errors="coerce")

    df_ev_top = df_events.head(30)

    source_colors = {
        "Tellienne centrale (Alger-Blida-Boumerdes)": "#ff4757",
        "Tellienne occidentale (Chlef-Oran)": "#ff7f50",
        "Tellienne orientale (Constantine-Annaba)": "#ffa502",
        "Atlas tellien sud (Médéa-Sétif-Batna)": "#ffd32a",
        "Hauts Plateaux": "#4fa9e3",
        "Saharienne (faible)": "#5b6374",
    }

    fig = go.Figure()
    for source in df_ev_top["Source"].unique():
        sub = df_ev_top[df_ev_top["Source"] == source]
        fig.add_trace(go.Scatter(
            x=sub["Magnitude"],
            y=sub["Perte (M DA)"],
            mode="markers",
            marker=dict(
                size=14,
                color=source_colors.get(source, "#5b6374"),
                line=dict(color="rgba(255,255,255,0.3)", width=1),
            ),
            name=source,
            hovertemplate="<b>%{text}</b><br>Magnitude : %{x:.2f}<br>Perte : %{y:,.0f} M DA<extra></extra>",
            text=[f"Scénario #{int(y)}" for y in sub["Année simulée"]],
        ))
    fig.update_layout(
        height=480,
        xaxis_title="Magnitude",
        yaxis_title="Perte (M DA) — échelle logarithmique",
        yaxis_type="log",
        legend=dict(orientation="h", y=-0.2),
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df_ev_top[["Rang", "Source", "Magnitude", "Latitude", "Longitude", "Perte (M DA)"]],
        use_container_width=True, hide_index=True, height=380,
    )
