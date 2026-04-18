"""
Portefeuille — Exploration interactive de l'ensemble des polices actives.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from theme import apply_theme, apply_plotly_dark, ACCENT_RED
from utils import (
    load_portefeuille, fmt_mds, fmt_m, fmt_int, fmt_pct,
    COLOR_ZONE, COLOR_CLASSE,
    render_view_toggle, is_net_view, project_value, view_label,
)

st.set_page_config(page_title="Portefeuille", layout="wide")
apply_theme()
render_view_toggle()
NET = is_net_view()

st.markdown("""
<div class="hero-block">
  <h1>Portefeuille</h1>
  <p>Parcourir l'ensemble des polices actives avec filtres multi-critères. Toutes les visualisations se recalculent en direct.</p>
</div>
""", unsafe_allow_html=True)

df = load_portefeuille()


# =============================================================================
# FILTRES
# =============================================================================
st.sidebar.markdown("### Filtres")

annees = sorted(df["ANNEE"].unique())
annee_sel = st.sidebar.multiselect("Année", annees, default=annees)

types = sorted(df["TYPE_COURT"].unique())
type_sel = st.sidebar.multiselect("Type de risque", types, default=types)

zones = ["0", "I", "IIa", "IIb", "III"]
zones_portef = [z for z in zones if z in df["ZONE_FINALE"].unique()]
zone_sel = st.sidebar.multiselect("Zone sismique", zones_portef, default=zones_portef)

classes = ["B", "C", "D"]
classes_portef = [c for c in classes if c in df["VULNERABILITE_CLASSE"].unique()]
classe_sel = st.sidebar.multiselect("Classe de vulnérabilité", classes_portef, default=classes_portef)

wilayas = sorted(df["NOM_WILAYA"].dropna().unique())
wilaya_sel = st.sidebar.multiselect("Wilaya", wilayas, default=[],
                                     help="Laisser vide pour toutes les wilayas")

st.sidebar.markdown("---")
st.sidebar.caption(f"Portefeuille total : {len(df):,} lignes · {df['NOM_WILAYA'].nunique()} wilayas · {df['NOM_COMMUNE'].nunique()} communes".replace(",", " "))


# =============================================================================
# APPLIQUER FILTRES
# =============================================================================
mask = (
    df["ANNEE"].isin(annee_sel)
    & df["TYPE_COURT"].isin(type_sel)
    & df["ZONE_FINALE"].isin(zone_sel)
    & df["VULNERABILITE_CLASSE"].isin(classe_sel)
)
if wilaya_sel:
    mask &= df["NOM_WILAYA"].isin(wilaya_sel)

df_f = df[mask]

if len(df_f) == 0:
    st.warning("Aucune police ne correspond aux filtres sélectionnés.")
    st.stop()


# =============================================================================
# KPIs
# =============================================================================
st.markdown(f"### Indicateurs du sous-ensemble sélectionné — {view_label(short=True)}")

cap_sum = project_value(df_f["CAPITAL_M"].sum())
cep_sum = project_value(df_f["CEP_M"].sum())
prime_sum = project_value(df_f["PRIME_M"].sum())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Polices", fmt_int(len(df_f)), f"{len(df_f)/len(df)*100:.1f}% du total")
k2.metric("Capital", fmt_mds(cap_sum))
k3.metric("CEP", fmt_mds(cep_sum))
k4.metric("Prime", fmt_m(prime_sum))
ratio = cep_sum / cap_sum * 100 if cap_sum else 0
k5.metric("Ratio CEP/Capital", fmt_pct(ratio))


# =============================================================================
# ONGLETS
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["Répartitions", "Top wilayas", "Évolution", "Détail polices"])

with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Par zone sismique")
        agg_zone = df_f.groupby("ZONE_FINALE").agg(
            capital=("CAPITAL_M", "sum"),
            cep=("CEP_M", "sum"),
            polices=("NUMERO_POLICE", "count"),
        ).reset_index()
        agg_zone["zone_order"] = agg_zone["ZONE_FINALE"].map({"0":0,"I":1,"IIa":2,"IIb":3,"III":4})
        agg_zone = agg_zone.sort_values("zone_order")

        fig = go.Figure(go.Bar(
            x=agg_zone["ZONE_FINALE"],
            y=agg_zone["capital"],
            marker=dict(
                color=[COLOR_ZONE.get(z, "#5b6374") for z in agg_zone["ZONE_FINALE"]],
                line=dict(color='rgba(255,255,255,0.15)', width=1),
            ),
            text=[f"{v/1000:.1f} Mds" for v in agg_zone["capital"]],
            textposition="outside",
            textfont=dict(color="#ffffff"),
        ))
        fig.update_layout(height=340, showlegend=False,
                          yaxis_title="Capital (M DA)", xaxis_title="Zone")
        apply_plotly_dark(fig)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("##### Par classe de vulnérabilité")
        agg_cl = df_f.groupby("VULNERABILITE_CLASSE").agg(
            polices=("NUMERO_POLICE", "count"),
        ).reset_index()

        fig2 = go.Figure(go.Bar(
            x=agg_cl["VULNERABILITE_CLASSE"],
            y=agg_cl["polices"],
            marker=dict(
                color=[COLOR_CLASSE.get(c, "#5b6374") for c in agg_cl["VULNERABILITE_CLASSE"]],
                line=dict(color='rgba(255,255,255,0.15)', width=1),
            ),
            text=[fmt_int(v) for v in agg_cl["polices"]],
            textposition="outside",
            textfont=dict(color="#ffffff"),
        ))
        fig2.update_layout(height=340, showlegend=False,
                           yaxis_title="Nombre de polices",
                           xaxis_title="Classe")
        apply_plotly_dark(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("##### Par type de risque")
    agg_type = df_f.groupby("TYPE_COURT").agg(
        capital=("CAPITAL_M", "sum"),
    ).reset_index()

    fig3 = go.Figure(go.Pie(
        labels=agg_type["TYPE_COURT"],
        values=agg_type["capital"],
        hole=0.55,
        marker=dict(
            colors=["#4fa9e3", "#1abc9c", "#9b59b6"],
            line=dict(color='#0a0e1a', width=2),
        ),
        textinfo="label+percent",
        textfont=dict(color="#ffffff", size=13),
    ))
    fig3.update_layout(
        height=380,
        showlegend=True,
        annotations=[dict(
            text=f"<b>{fmt_mds(df_f['CAPITAL_M'].sum())}</b>",
            showarrow=False,
            font=dict(size=14, color="#ffffff"),
        )],
    )
    apply_plotly_dark(fig3)
    st.plotly_chart(fig3, use_container_width=True)


with tab2:
    st.markdown("##### Top 15 wilayas du sous-ensemble filtré")
    top_w = df_f.groupby("NOM_WILAYA").agg(
        capital=("CAPITAL_M", "sum"),
        cep=("CEP_M", "sum"),
        polices=("NUMERO_POLICE", "count"),
    ).reset_index().sort_values("cep", ascending=False).head(15)

    fig = go.Figure(go.Bar(
        x=top_w["cep"],
        y=top_w["NOM_WILAYA"],
        orientation="h",
        marker=dict(
            color=ACCENT_RED,
            line=dict(color='rgba(255,255,255,0.15)', width=1),
        ),
        text=[f"{v:.0f} M DA" for v in top_w["cep"]],
        textposition="outside",
        textfont=dict(color="#ffffff"),
    ))
    fig.update_layout(
        height=560,
        xaxis_title="CEP (M DA)",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=130, r=60),
    )
    apply_plotly_dark(fig)
    st.plotly_chart(fig, use_container_width=True)


with tab3:
    st.markdown("##### Évolution par année sur les filtres sélectionnés")
    evo = df_f.groupby(["ANNEE", "ZONE_FINALE"]).agg(
        capital=("CAPITAL_M", "sum"),
    ).reset_index()

    fig = go.Figure()
    for zone in ["0", "I", "IIa", "IIb", "III"]:
        sub = evo[evo["ZONE_FINALE"] == zone]
        if len(sub):
            fig.add_trace(go.Bar(
                x=sub["ANNEE"],
                y=sub["capital"],
                name=f"Zone {zone}",
                marker_color=COLOR_ZONE.get(zone, "#5b6374"),
                marker_line=dict(color='rgba(255,255,255,0.15)', width=1),
            ))
    fig.update_layout(
        height=440,
        barmode="stack",
        yaxis_title="Capital (M DA)",
        xaxis_title="Année",
    )
    apply_plotly_dark(fig)
    fig.update_xaxes(tickmode="array", tickvals=sorted(df_f["ANNEE"].unique()))
    st.plotly_chart(fig, use_container_width=True)


with tab4:
    st.markdown(f"##### Détail des {len(df_f):,} polices".replace(",", " "))

    cols_aff = ["ANNEE", "NUMERO_POLICE", "TYPE_COURT", "NOM_WILAYA", "NOM_COMMUNE",
                "ZONE_FINALE", "VULNERABILITE_CLASSE", "CAPITAL_M", "CEP_M", "PRIME_M"]
    df_aff = df_f[cols_aff].copy()
    df_aff.columns = ["Année", "N° Police", "Type", "Wilaya", "Commune",
                      "Zone", "Classe", "Capital (M)", "CEP (M)", "Prime (M)"]

    st.dataframe(df_aff.head(2000),
                 use_container_width=True, height=500,
                 column_config={
                     "Capital (M)": st.column_config.NumberColumn(format="%.2f"),
                     "CEP (M)":     st.column_config.NumberColumn(format="%.2f"),
                     "Prime (M)":   st.column_config.NumberColumn(format="%.3f"),
                 })

    if len(df_aff) > 2000:
        st.caption(f"Affichage des 2 000 premières lignes sur {len(df_aff):,}. Export complet disponible.".replace(",", " "))

    csv = df_aff.to_csv(index=False).encode("utf-8")
    st.download_button("Télécharger le détail filtré (CSV)", csv, "portefeuille_filtre.csv", "text/csv")
