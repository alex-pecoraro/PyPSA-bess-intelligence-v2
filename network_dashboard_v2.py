"""
California BESS Siting Intelligence Platform
2050 Forecasted Grid Conditions | PyPSA-USA | CAISO LMP 2024 Actuals
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="California BESS Siting Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────
CA_FIPS = {
    "p06001":"Alameda","p06003":"Alpine","p06005":"Amador","p06007":"Butte",
    "p06009":"Calaveras","p06011":"Colusa","p06013":"Contra Costa",
    "p06015":"Del Norte","p06017":"El Dorado","p06019":"Fresno",
    "p06021":"Glenn","p06023":"Humboldt","p06025":"Imperial",
    "p06027":"Inyo","p06029":"Kern","p06031":"Kings","p06033":"Lake",
    "p06035":"Lassen","p06037":"Los Angeles","p06039":"Madera",
    "p06041":"Marin","p06043":"Mariposa","p06045":"Mendocino",
    "p06047":"Merced","p06049":"Modoc","p06051":"Mono",
    "p06053":"Monterey","p06055":"Napa","p06057":"Nevada",
    "p06059":"Orange","p06061":"Placer","p06063":"Plumas",
    "p06065":"Riverside","p06067":"Sacramento","p06069":"San Benito",
    "p06071":"San Bernardino","p06073":"San Diego","p06075":"San Francisco",
    "p06077":"San Joaquin","p06079":"San Luis Obispo","p06081":"San Mateo",
    "p06083":"Santa Barbara","p06085":"Santa Clara","p06087":"Santa Cruz",
    "p06089":"Shasta","p06091":"Sierra","p06093":"Siskiyou",
    "p06095":"Solano","p06097":"Sonoma","p06099":"Stanislaus",
    "p06101":"Sutter","p06103":"Tehama","p06105":"Trinity",
    "p06107":"Tulare","p06109":"Tuolumne","p06111":"Ventura",
    "p06113":"Yolo","p06115":"Yuba",
}

BA_LABELS = {
    "CISO-PGAE":"CAISO PG&E","CISO-SCE":"CAISO SCE","CISO-SDGE":"CAISO SDG&E",
    "LDWP":"LA DWP","BANC":"BANC","IID":"Imperial IID",
    "PACW":"PacifiCorp West","TIDC":"Turlock ID","WALC":"WALC",
}

VOLTAGE_COLORS = {
    "138 kV": "#7a8a9a",
    "230 kV": "#4a7fba",
    "345 kV": "#c07030",
    "500 kV": "#7a4fb0",
    "765 kV": "#b03030",
}

# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────
DATA_DIR = "data/"

@st.cache_data
def load_buses(_mtime=None):
    # _mtime is passed solely to bust the cache when the parquet is updated
    df = pd.read_parquet(DATA_DIR + "bus_data_v2.parquet")
    df['bus_id'] = df['bus_id'].astype(str)
    df['county_name'] = df['county'].map(CA_FIPS).fillna(df['county'])
    df['ba_label'] = df['balancing_area'].map(BA_LABELS).fillna(df['balancing_area'])
    df['voltage_cat'] = pd.cut(df['v_nom'],
        bins=[0, 138, 230, 345, 500, 9999],
        labels=['138 kV', '230 kV', '345 kV', '500 kV', '765 kV'])
    df['tier'] = pd.cut(df['composite'],
        bins=[-1, 40, 60, 80, 101],
        labels=['< 40 (Low)', '40–59 (Tier 3)', '60–79 (Tier 2)', '>=80 (Tier 1)'])
    return df

@st.cache_data
def load_lines():
    try:
        return pd.read_parquet(DATA_DIR + "lines_v2.parquet")
    except:
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if 'shortlist' not in st.session_state:
    st.session_state.shortlist = []

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f172a; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSlider label { color: #94a3b8 !important; font-size:0.78rem !important; }
.main-header { font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-bottom: 0; letter-spacing: -0.5px; }
.sub-header  { font-size: 0.85rem; color: #64748b; margin-top: 2px; }
.scenario-badge { background:#1e3a5f; color:#c8daf0; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:700; }
.kpi-box { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px 16px; text-align:center; }
.kpi-value { font-size:1.6rem; font-weight:800; color:#0f172a; }
.kpi-label { font-size:0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:.06em; }
.tier1 { color:#1a6b45; font-weight:700; }
.tier2 { color:#2d5986; font-weight:700; }
.tier3 { color:#8a5c2a; font-weight:700; }
.bus-chip { background:#dbe9f5; color:#1e3a5f; padding:2px 8px; border-radius:4px; font-family:monospace; font-size:0.8rem; }
.calc-row { background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:10px 14px; margin-bottom:8px; font-size:0.88rem; }
.calc-formula { color:#64748b; font-family:monospace; font-size:0.82rem; }
.calc-result { font-weight:700; color:#0f172a; font-size:1.05rem; }
.build-clear { color:#1a6b45; font-weight:700; }
.build-limited { color:#8a5c2a; font-weight:700; }
.build-restricted { color:#8b2d2d; font-weight:700; }
.land-info-box { background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:10px 14px; font-size:0.85rem; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">California BESS Siting Intelligence Platform '
    '<span class="scenario-badge">2050 FORECASTED GRID</span></div>'
    '<div class="sub-header">PyPSA-USA Network Model · CAISO LMP 2024 Actuals · 3,453 California Substations</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
import os as _os
_parquet_mtime = _os.path.getmtime(DATA_DIR + "bus_data_v2.parquet")
df_all = load_buses(_mtime=_parquet_mtime)

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### BESS Siting Tool")
    st.markdown("**3,453 CA substations** | 138–765 kV")
    st.markdown("2050 demand scenario + CAISO 2024 LMP")
    st.markdown("---")

    st.markdown("**Map Layers**")
    show_lines = st.checkbox("Show transmission lines", value=True)
    voltage_filter = st.multiselect(
        "Voltage levels to show on map",
        ['138 kV', '230 kV', '345 kV', '765 kV'],
        default=['230 kV', '345 kV', '765 kV']
    )

    st.markdown("---")
    st.markdown("**Filter Sites**")

    min_comp = st.slider("Min. composite score", 0, 80, 0, 5)

    ba_options = ['All'] + sorted(df_all['balancing_area'].dropna().unique().tolist())
    ba_sel = st.selectbox("Balancing area", ba_options)

    tech_options = ['All'] + sorted(df_all['dominant_tech'].dropna().unique().tolist())
    tech_sel = st.selectbox("Dominant technology", tech_options)

    v_options = ['All', '138 kV', '230 kV', '345 kV', '765 kV']
    v_sel = st.selectbox("Transmission voltage", v_options)

    search = st.text_input("Search county / balancing area", placeholder="e.g. Kern, Sonoma, CISO-SCE")

    st.markdown("---")
    st.markdown("**Land Buildability**")
    build_filter = st.multiselect(
        "Show buildability tiers",
        ['Clear', 'Limited', 'Restricted'],
        default=['Clear', 'Limited', 'Restricted'],
        help="Clear: <25% protected land + low flood risk. Limited: moderate constraints. Restricted: >55% protected or high flood risk county.",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Shortlist**")
    sl = st.session_state.shortlist
    if not sl:
        st.caption("No sites shortlisted yet. Select from the map table below.")
    else:
        for b in sl:
            row = df_all[df_all['bus_id'] == b]
            if not row.empty:
                name = row.iloc[0].get('county_name', b)
                score = row.iloc[0]['composite']
                st.markdown(f"<span class='bus-chip'>{b}</span> {name} · **{score:.0f}**",
                            unsafe_allow_html=True)
        if st.button("Clear shortlist", use_container_width=True):
            st.session_state.shortlist = []
            st.rerun()

# ─────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────
filt = df_all[df_all['composite'].fillna(0) >= min_comp].copy()

if ba_sel != 'All':
    filt = filt[filt['balancing_area'] == ba_sel]
if tech_sel != 'All' and 'dominant_tech' in filt.columns:
    filt = filt[filt['dominant_tech'].fillna('Unknown') == tech_sel]
if v_sel != 'All':
    vmap = {'138 kV': 138, '230 kV': 230, '345 kV': 345, '765 kV': 765}
    if v_sel in vmap:
        filt = filt[filt['v_nom'] == vmap[v_sel]]
if search:
    s = search.lower()
    mask = (
        filt['county_name'].str.lower().str.contains(s, na=False) |
        filt['balancing_area'].str.lower().str.contains(s, na=False) |
        filt['ba_label'].str.lower().str.contains(s, na=False)
    )
    filt = filt[mask]
if build_filter and 'buildability' in filt.columns:
    filt = filt[filt['buildability'].isin(build_filter)]

# ─────────────────────────────────────────────────────────────
# KPI BAR
# ─────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)

def kpi(col, val, label):
    col.markdown(
        f'<div class="kpi-box"><div class="kpi-value">{val}</div>'
        f'<div class="kpi-label">{label}</div></div>',
        unsafe_allow_html=True
    )

kpi(k1, f"{len(filt):,}", "Sites Shown")
kpi(k2, f"{(filt['composite'] >= 80).sum()}", "Tier 1 (>=80)")
kpi(k3, f"{(filt['composite'] >= 60).sum()}", "Tier 1+2 (>=60)")
kpi(k4, f"{filt['composite'].mean():.1f}" if len(filt) else "N/A", "Avg Score")
n_clear = int((filt['buildability'] == 'Clear').sum()) if 'buildability' in filt.columns else 0
kpi(k5, f"{n_clear}", "Clear Land")
kpi(k6, f"{len(st.session_state.shortlist)}", "Shortlisted")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab_screen, tab_compare, tab_brief, tab_econ, tab_method = st.tabs([
    "① Screen", "② Compare", "③ Site Brief", "④ Economics", "⑤ Methodology"
])

# ═══════════════════════════════════════════════════════════════
# TAB ①: SCREEN
# ═══════════════════════════════════════════════════════════════
with tab_screen:
    map_col, table_col = st.columns([3, 2])

    with map_col:
        def tier_color(score):
            if score >= 80:   return '#1a6b45'
            elif score >= 60: return '#2d5986'
            elif score >= 40: return '#8a5c2a'
            else:             return '#6b7280'

        filt['_size'] = (filt['composite'] / 100 * 12 + 4).clip(4, 16)

        fig = go.Figure()

        # Transmission lines
        if show_lines:
            lines_df = load_lines()
            if len(lines_df) > 0:
                vcats_selected = set(voltage_filter) if voltage_filter else set()
                for vcat, vcol in VOLTAGE_COLORS.items():
                    if vcat not in vcats_selected:
                        continue
                    sub = lines_df[lines_df['voltage_cat'] == vcat]
                    if len(sub) == 0:
                        continue
                    lons, lats = [], []
                    for _, row in sub.iterrows():
                        lons += [row['x0'], row['x1'], None]
                        lats += [row['y0'], row['y1'], None]
                    fig.add_trace(go.Scattermapbox(
                        lon=lons, lat=lats,
                        mode='lines',
                        line=dict(color=vcol, width=1.5 if '345' in vcat or '765' in vcat else 0.8),
                        name=f"Lines {vcat}",
                        hoverinfo='none',
                        opacity=0.6,
                    ))

        # Substation scatter
        if len(filt) > 0:
            hover_parts = [
                "<b>Bus %{customdata[0]}</b>",
                "%{customdata[1]} · %{customdata[2]}",
                "────────────────",
                "Composite: %{customdata[3]:.1f}",
                "Renewable Sat: %{customdata[4]:.1f}",
                "Load: %{customdata[5]:.1f}",
                "Congestion: %{customdata[6]:.1f}",
                "LMP Score: %{customdata[7]:.1f}",
                "Voltage: %{customdata[8]} kV",
                "Load Mean: %{customdata[9]:.1f} MW",
            ]
            hover_template = "<br>".join(hover_parts) + "<extra></extra>"

            cdata_cols = ['bus_id', 'county_name', 'ba_label', 'composite',
                          'renewable_sat', 'load_imbalance', 'congestion_score',
                          'lmp_score', 'v_nom', 'load_mean_mw']
            for col in cdata_cols:
                if col not in filt.columns:
                    filt[col] = 'N/A'

            fig.add_trace(go.Scattermapbox(
                lon=filt['x'],
                lat=filt['y'],
                mode='markers',
                marker=dict(
                    size=filt['_size'],
                    color=filt['composite'],
                    colorscale=[[0,'#6b7280'],[0.4,'#8a5c2a'],[0.6,'#2d5986'],[0.8,'#1a6b45'],[1,'#0d3d28']],
                    cmin=0, cmax=100,
                    colorbar=dict(title="Score", thickness=12, len=0.5),
                    opacity=0.85,
                ),
                customdata=filt[cdata_cols].values,
                hovertemplate=hover_template,
                name="Substations",
            ))

            # Shortlisted highlight
            sl_filt = filt[filt['bus_id'].isin(st.session_state.shortlist)]
            if len(sl_filt) > 0:
                fig.add_trace(go.Scattermapbox(
                    lon=sl_filt['x'], lat=sl_filt['y'],
                    mode='markers',
                    marker=dict(size=18, color='#d4a017', symbol='star', opacity=1.0),
                    name='Shortlisted',
                    hoverinfo='skip',
                ))

        center_lon = filt['x'].mean() if len(filt) else -119.4
        center_lat = filt['y'].mean() if len(filt) else 36.8

        fig.update_layout(
            mapbox=dict(style="open-street-map",
                        center=dict(lon=center_lon, lat=center_lat),
                        zoom=5.5),
            height=560,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(bgcolor='rgba(255,255,255,0.85)', bordercolor='#e2e8f0',
                        borderwidth=1, font=dict(size=10)),
            paper_bgcolor='white',
        )

        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

        if show_lines and voltage_filter:
            leg_parts = [f"<span style='color:{VOLTAGE_COLORS[v]};font-weight:700'>&#9679;</span> {v}"
                         for v in voltage_filter if v in VOLTAGE_COLORS]
            st.caption("Line colours: " + " · ".join(leg_parts))

        st.caption(
            f"Showing **{len(filt):,}** substations. "
            "Scroll/pinch to zoom. Hover for details. Add sites to shortlist using the table."
        )

    with table_col:
        st.markdown("#### Site Rankings")

        sort_col_label = st.selectbox(
            "Sort by",
            ["Composite", "Renewable Sat", "Load Imbalance", "Congestion", "LMP Score"],
            label_visibility="collapsed"
        )
        sort_map = {
            "Composite": "composite",
            "Renewable Sat": "renewable_sat",
            "Load Imbalance": "load_imbalance",
            "Congestion": "congestion_score",
            "LMP Score": "lmp_score",
        }
        sort_key = sort_map.get(sort_col_label, "composite")
        if sort_key not in filt.columns:
            sort_key = "composite"

        display = filt.sort_values(sort_key, ascending=False).head(200)

        disp_cols = ['bus_id', 'county_name', 'balancing_area', 'v_nom',
                     'composite', 'renewable_sat', 'load_imbalance',
                     'congestion_score', 'buildability', 'dominant_tech']
        disp_cols = [c for c in disp_cols if c in display.columns]
        rename = {
            'bus_id': 'Bus', 'county_name': 'County', 'balancing_area': 'BA',
            'v_nom': 'kV', 'composite': 'Score', 'renewable_sat': 'Renew',
            'load_imbalance': 'Load', 'congestion_score': 'Cong',
            'buildability': 'Land', 'dominant_tech': 'Use Case',
        }

        st.dataframe(
            display[disp_cols].rename(columns=rename).reset_index(drop=True),
            height=430,
            use_container_width=True,
            column_config={
                "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f"),
                "Renew": st.column_config.ProgressColumn("Renew", min_value=0, max_value=100, format="%.1f"),
                "Load":  st.column_config.ProgressColumn("Load",  min_value=0, max_value=100, format="%.1f"),
                "Cong":  st.column_config.ProgressColumn("Cong",  min_value=0, max_value=100, format="%.1f"),
                "Land":  st.column_config.TextColumn("Land", help="County-level buildability: Clear / Limited / Restricted"),
            }
        )

        st.markdown("**Add to Shortlist**")
        bus_options = display['bus_id'].tolist()
        disp_idx = display.set_index('bus_id')
        to_add = st.multiselect(
            "Select bus IDs",
            options=bus_options,
            format_func=lambda b: f"{b}: {disp_idx.loc[b,'county_name']} ({disp_idx.loc[b,'composite']:.0f})" if b in disp_idx.index else b,
            default=[b for b in st.session_state.shortlist if b in bus_options],
            label_visibility="collapsed",
            max_selections=8,
        )
        if set(to_add) != set(b for b in st.session_state.shortlist if b in bus_options):
            keep = [b for b in st.session_state.shortlist if b not in bus_options]
            st.session_state.shortlist = list(set(keep + to_add))
            st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB ②: COMPARE
# ═══════════════════════════════════════════════════════════════
with tab_compare:
    if not st.session_state.shortlist:
        st.markdown(
            '<div style="background:#f0f5fa;border:1px solid #c5d8ed;border-radius:8px;'
            'padding:24px;text-align:center;">'
            'No sites shortlisted yet. Go to <strong>Screen</strong> and select up to 8 sites.</div>',
            unsafe_allow_html=True
        )
    else:
        sl = st.session_state.shortlist
        sl_df = df_all[df_all['bus_id'].isin(sl)].copy()

        st.markdown("#### Opportunity Score Ranking")
        st.caption("Scores reflect grid signal opportunity: 4 independent signals, each 0–100. For revenue projections, see Economics tab.")

        # Horizontal leaderboard
        sl_sorted = sl_df.sort_values('composite', ascending=True)

        fig_rank = go.Figure()
        for _, row in sl_sorted.iterrows():
            score = row['composite']
            color = tier_color(score)
            fig_rank.add_trace(go.Bar(
                x=[score],
                y=[f"{row['bus_id']} · {row.get('county_name', '')}"],
                orientation='h',
                marker_color=color,
                text=f"  {score:.1f}",
                textposition='outside',
                width=0.55,
                showlegend=False,
                hovertemplate=f"<b>{row['bus_id']}</b><br>Score: {score:.1f}<extra></extra>",
            ))

        fig_rank.update_layout(
            height=max(200, len(sl_sorted) * 52 + 60),
            xaxis=dict(range=[0, 105], title="Composite Score (0–100)"),
            yaxis=dict(autorange=True, tickfont=dict(size=11)),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=160, r=60, t=20, b=40),
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        # Signal radar
        st.markdown("#### Signal Profile")
        signal_cols   = ['renewable_sat', 'load_imbalance', 'congestion_score', 'lmp_score']
        signal_labels = ['Renewable\nSaturation', 'Load\nImbalance', 'Congestion\nRelief', 'LMP\nAttractiveness']
        radar_cols    = [c for c in signal_cols if c in sl_df.columns]
        radar_labels  = [signal_labels[signal_cols.index(c)] for c in radar_cols]

        if len(radar_cols) >= 3:
            fig_radar = go.Figure()
            colors_radar = ['#2d5986','#1a6b45','#8a5c2a','#6b3f94','#8b2d2d','#1a7a6b','#c07030','#5a3fa0']

            def hex_to_rgba(hex_color, alpha=0.15):
                h = hex_color.lstrip('#')
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                return f'rgba({r},{g},{b},{alpha})'

            for i, (_, row) in enumerate(sl_df.iterrows()):
                vals        = [row.get(c, 0) for c in radar_cols]
                vals_wrap   = vals + [vals[0]]
                labels_wrap = radar_labels + [radar_labels[0]]
                color       = colors_radar[i % len(colors_radar)]
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals_wrap, theta=labels_wrap,
                    fill='toself',
                    fillcolor=hex_to_rgba(color),
                    line=dict(color=color, width=2),
                    name=f"{row['bus_id']} ({row.get('county_name','')})",
                    opacity=0.9,
                ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                height=380, paper_bgcolor='white',
                legend=dict(font=dict(size=10)),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Score contribution stacked bar
        st.markdown("#### Score Contribution Breakdown")
        weights = {'renewable_sat': 0.35, 'load_imbalance': 0.25,
                   'congestion_score': 0.20, 'lmp_score': 0.20}
        contrib_cols  = [c for c in weights if c in sl_df.columns]
        stack_colors  = {'renewable_sat':'#1a6b45','load_imbalance':'#2d5986',
                         'congestion_score':'#8a5c2a','lmp_score':'#6b3f94'}
        stack_labels  = {'renewable_sat':'Renewable Sat.','load_imbalance':'Load Imbalance',
                         'congestion_score':'Congestion','lmp_score':'LMP Attractiveness'}

        fig_stack = go.Figure()
        for cc in contrib_cols:
            fig_stack.add_trace(go.Bar(
                x=[row['bus_id'] for _, row in sl_df.iterrows()],
                y=(sl_df[cc] * weights[cc]).values,
                name=stack_labels.get(cc, cc),
                marker_color=stack_colors.get(cc, '#94a3b8'),
            ))
        fig_stack.update_layout(
            barmode='stack', height=300,
            yaxis_title="Score Points",
            plot_bgcolor='white', paper_bgcolor='white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            margin=dict(l=40, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_stack, use_container_width=True)

        # Forecasted grid characteristics table
        st.markdown("#### Forecasted Grid Characteristics")
        char_cols = ['bus_id', 'county_name', 'balancing_area', 'v_nom',
                     'n_lines', 'total_thermal_mva', 'solar_mean_cf',
                     'wind_mean_cf', 'load_mean_mw', 'buildability',
                     'pct_protected', 'dominant_tech']
        char_cols = [c for c in char_cols if c in sl_df.columns]
        ch_rename = {
            'bus_id':'Bus', 'county_name':'County', 'balancing_area':'BA',
            'v_nom':'kV', 'n_lines':'Lines', 'total_thermal_mva':'Thermal Cap (MVA)',
            'solar_mean_cf':'Solar CF', 'wind_mean_cf':'Wind CF',
            'load_mean_mw':'Forecasted Avg Load (MW)',
            'buildability':'Land', 'pct_protected':'Protected %',
            'dominant_tech':'Use Case',
        }
        st.dataframe(sl_df[char_cols].rename(columns=ch_rename).reset_index(drop=True),
                     use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB ③: SITE BRIEF
# ═══════════════════════════════════════════════════════════════
with tab_brief:
    if not st.session_state.shortlist:
        st.info("No sites shortlisted. Go to Screen to select sites.")
    else:
        brief_bus = st.selectbox(
            "Select site for detailed brief",
            options=st.session_state.shortlist,
            format_func=lambda b: f"Bus {b}: " + (
                df_all[df_all['bus_id']==b].iloc[0].get('county_name', b)
                if len(df_all[df_all['bus_id']==b]) > 0 else b
            )
        )
        row = df_all[df_all['bus_id'] == brief_bus].iloc[0] \
              if len(df_all[df_all['bus_id']==brief_bus]) > 0 else None

        if row is not None:
            score     = row['composite']
            tier_str  = ("Tier 1: Prime"    if score >= 80 else
                         "Tier 2: Qualified" if score >= 60 else
                         "Tier 3: Marginal"  if score >= 40 else
                         "Below threshold")
            tier_cls  = "tier1" if score >= 80 else "tier2" if score >= 60 else "tier3"

            st.markdown(
                f"## Site Brief: Bus `{brief_bus}`  "
                f"<span class='{tier_cls}'>{tier_str} ({score:.1f}/100)</span>",
                unsafe_allow_html=True
            )

            b1, b2, b3 = st.columns(3)
            with b1:
                st.metric("Composite Score", f"{score:.1f}/100")
                st.metric("Dominant Use Case", row.get('dominant_tech', 'N/A'))
            with b2:
                st.metric("County", row.get('county_name', row.get('county', 'N/A')))
                st.metric("Balancing Area", row.get('balancing_area', 'N/A'))
            with b3:
                st.metric("Voltage", f"{row.get('v_nom', 'N/A'):.0f} kV")
                st.metric("Grid Lines", f"{int(row.get('n_lines', 0))}")

            st.markdown("---")
            st.markdown("**Signal Detail**")

            sig_data = {
                'Renewable Saturation': row.get('renewable_sat', 0),
                'Load Imbalance':       row.get('load_imbalance', 0),
                'Congestion Score':     row.get('congestion_score', 0),
                'LMP Attractiveness':   row.get('lmp_score', 0),
            }
            for sname, sval in sig_data.items():
                pct   = min(100, max(0, float(sval)))
                color = '#1a6b45' if pct >= 70 else '#2d5986' if pct >= 40 else '#8a5c2a'
                st.markdown(
                    f"**{sname}** {sval:.1f}/100  \n"
                    f'<div style="background:#f1f5f9;border-radius:4px;height:10px;margin-bottom:8px;">'
                    f'<div style="background:{color};width:{pct}%;height:10px;border-radius:4px;"></div></div>',
                    unsafe_allow_html=True
                )

            st.markdown("---")
            st.markdown("**Grid Infrastructure (2050 Forecasted)**")
            gi1, gi2, gi3, gi4 = st.columns(4)
            gi1.metric("Transmission Lines", f"{int(row.get('n_lines', 0))}")
            gi2.metric("Total Thermal Capacity", f"{row.get('total_thermal_mva', 0):.0f} MVA")
            gi3.metric("Solar Capacity Factor", f"{row.get('solar_mean_cf', 0):.3f}")
            gi4.metric("Wind Capacity Factor", f"{row.get('wind_mean_cf', 0):.3f}")

            st.markdown("**Forecasted Demand Profile (2050)**")
            dm1, dm2 = st.columns(2)
            dm1.metric("Mean Load", f"{row.get('load_mean_mw', 0):.1f} MW")
            dm2.metric("Peak Load", f"{row.get('load_peak_mw', 0):.1f} MW")

            st.markdown("---")
            st.markdown("**LMP Characteristics (DC LOPF Nodal)**")
            lmp_mean = float(row.get('lmp_mean', 45))
            lmp_std  = float(row.get('lmp_std', 35))
            lmp_p95  = float(row.get('lmp_p95', 120))
            l1, l2, l3 = st.columns(3)
            l1.metric("Annual Mean LMP", f"${lmp_mean:.2f}/MWh")
            l2.metric("Price Volatility (1-sigma)", f"${lmp_std:.2f}/MWh")
            l3.metric("95th Percentile LMP", f"${lmp_p95:.2f}/MWh")

            st.markdown("---")
            st.markdown("**Land Context** *(county-level estimate)*")
            build_val   = row.get('buildability', 'N/A')
            prot_pct    = int(row.get('pct_protected', 0))
            flood_num   = int(row.get('flood_risk', 1))
            flood_label = {1: "Low", 2: "Medium", 3: "High"}.get(flood_num, "Unknown")
            build_cls   = {'Clear': 'build-clear', 'Limited': 'build-limited',
                           'Restricted': 'build-restricted'}.get(build_val, '')

            lc1, lc2, lc3 = st.columns(3)
            lc1.markdown(
                f'<div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:.06em;">Buildability</div>'
                f'<div class="{build_cls}" style="font-size:1.1rem;">{build_val}</div>',
                unsafe_allow_html=True
            )
            lc2.metric("Protected Land (County)", f"{prot_pct}%")
            lc3.metric("Flood Risk (County)", flood_label)
            st.caption(
                "County-level estimates only. Protected land: PADUS 3.0 (USGS GAP). "
                "Flood risk: FEMA NFIP county statistics. Verify at parcel level before any site commitment."
            )

# ═══════════════════════════════════════════════════════════════
# TAB ④: ECONOMICS
# ═══════════════════════════════════════════════════════════════
with tab_econ:
    st.markdown("### Project Economics Calculator")
    st.caption("Select a site and adjust assumptions. Every line item shows its formula so you can see exactly where each number comes from.")

    # Site selector
    econ_options = st.session_state.shortlist or df_all['bus_id'].head(5).tolist()
    econ_bus = st.selectbox(
        "Select site",
        options=econ_options,
        format_func=lambda b: f"Bus {b}: " + (
            df_all[df_all['bus_id']==b].iloc[0].get('county_name', b)
            if len(df_all[df_all['bus_id']==b]) > 0 else b
        )
    )
    econ_row = df_all[df_all['bus_id'] == econ_bus].iloc[0] \
               if len(df_all[df_all['bus_id']==econ_bus]) > 0 else None

    if econ_row is not None:
        site_lmp_mean = float(econ_row.get('lmp_mean', 45))
        site_lmp_std  = float(econ_row.get('lmp_std', 35))

        st.markdown("---")
        st.markdown("#### Step 1: Define the System")
        s1, s2, s3 = st.columns(3)
        with s1:
            capacity_mw   = st.number_input("Power capacity (MW)", 10, 500, 100, 10,
                                            help="The maximum charge or discharge rate.")
        with s2:
            duration_hrs  = st.selectbox("Storage duration (hours)", [2, 4, 6, 8], index=1,
                                         help="Hours the system can discharge at full power.")
        with s3:
            roundtrip_eff = st.slider("Round-trip efficiency (%)", 80, 95, 87,
                                      help="Energy out / energy in. Typical Li-ion: 85–90%.") / 100

        capacity_mwh = capacity_mw * duration_hrs
        st.markdown(
            f'<div class="calc-row">'
            f'<b>System size:</b> {capacity_mw} MW × {duration_hrs} hr = '
            f'<span class="calc-result">{capacity_mwh} MWh</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.markdown("#### Step 2: Revenue Inputs")

        rev_col1, rev_col2 = st.columns(2)

        with rev_col1:
            st.markdown("**Energy Arbitrage**")
            cycles_yr  = st.slider("Full cycles per year", 150, 365, 250,
                                   help="Number of full charge-discharge cycles annually. 250 is typical for a 4-hr asset in California.")
            avg_spread = st.number_input(
                "Average buy/sell spread ($/MWh)",
                5.0, 100.0,
                float(min(100.0, max(5.0, round(site_lmp_std * 0.8, 1)))),
                2.5,
                help=f"Price differential between off-peak charging and on-peak discharging. "
                     f"Pre-filled from this site's LMP volatility (sigma = ${site_lmp_std:.1f}/MWh)."
            )

            st.markdown("**Resource Adequacy**")
            ra_value = st.number_input(
                "RA capacity value ($/kW-yr)",
                0, 200, 65, 5,
                help="CPUC annual RA clearing price for the site's BA. 2024 range: $50–$120/kW-yr."
            )

        with rev_col2:
            st.markdown("**Ancillary Services**")
            ancillary = st.number_input(
                "Ancillary services revenue ($/MW-yr)",
                0, 50000, 12000, 1000,
                help="CAISO Reg Up/Down, Spinning Reserve. Flat rate simplification; actual values vary by season."
            )

            st.markdown("**Capital & Incentives**")
            capex_kwh = st.number_input(
                "All-in CapEx ($/kWh)",
                150, 500, 280, 10,
                help="Installed cost including EPC, interconnection, and soft costs. 2024 utility-scale range: $250–$350/kWh."
            )
            itc_pct = st.slider(
                "ITC credit (%)", 0, 40, 30,
                help="Investment Tax Credit under IRA. Base: 30%. With domestic content + energy community adders: up to 40%."
            )

        # ── Calculations ──
        energy_rev  = capacity_mwh * cycles_yr * roundtrip_eff * avg_spread
        ra_rev      = capacity_mw * ra_value * 1_000          # $/kW-yr × 1000 kW/MW
        ancil_rev   = capacity_mw * ancillary
        gross_rev   = energy_rev + ra_rev + ancil_rev
        total_capex = capex_kwh * capacity_mwh * 1_000        # $/kWh × kWh × 1000 kWh/MWh
        itc_credit  = total_capex * itc_pct / 100
        net_capex   = total_capex - itc_credit
        opex_yr     = total_capex * 0.025                     # 2.5% of gross capex/yr
        ebitda_yr   = gross_rev - opex_yr
        simple_pb   = net_capex / ebitda_yr if ebitda_yr > 0 else float('inf')

        st.markdown("---")
        st.markdown("#### Step 3: Calculation Breakdown")
        st.caption("Each row shows the formula, the numbers plugged in, and the result.")

        def calc_row(label, formula, result_str, color="#0f172a"):
            st.markdown(
                f'<div class="calc-row">'
                f'<b>{label}</b><br>'
                f'<span class="calc-formula">{formula}</span><br>'
                f'<span class="calc-result" style="color:{color};">{result_str}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        calc_row(
            "Energy Arbitrage Revenue",
            f"{capacity_mwh} MWh × {cycles_yr} cycles × {roundtrip_eff:.0%} eff × ${avg_spread:.2f}/MWh",
            f"${energy_rev/1e6:.3f}M / yr",
            "#1a6b45"
        )
        calc_row(
            "Resource Adequacy Revenue",
            f"{capacity_mw} MW × {ra_value} $/kW-yr × 1,000 kW/MW",
            f"${ra_rev/1e6:.3f}M / yr",
            "#2d5986"
        )
        calc_row(
            "Ancillary Services Revenue",
            f"{capacity_mw} MW × ${ancillary:,}/MW-yr",
            f"${ancil_rev/1e6:.3f}M / yr",
            "#6b3f94"
        )
        calc_row(
            "Gross Revenue",
            f"${energy_rev/1e6:.3f}M + ${ra_rev/1e6:.3f}M + ${ancil_rev/1e6:.3f}M",
            f"${gross_rev/1e6:.3f}M / yr",
            "#0f172a"
        )
        calc_row(
            "Operating Expenses (OpEx)",
            f"2.5% × total CapEx = 2.5% × ${total_capex/1e6:.2f}M",
            f"–${opex_yr/1e6:.3f}M / yr",
            "#8b2d2d"
        )
        calc_row(
            "EBITDA",
            f"Gross Revenue – OpEx = ${gross_rev/1e6:.3f}M – ${opex_yr/1e6:.3f}M",
            f"${ebitda_yr/1e6:.3f}M / yr",
            "#0f172a"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Step 4: Capital Cost & Payback")

        calc_row(
            "Total CapEx",
            f"${capex_kwh}/kWh × {capacity_mwh} MWh × 1,000 kWh/MWh",
            f"${total_capex/1e6:.2f}M"
        )
        calc_row(
            "ITC Credit",
            f"{itc_pct}% × ${total_capex/1e6:.2f}M",
            f"–${itc_credit/1e6:.2f}M",
            "#1a6b45"
        )
        calc_row(
            "Net CapEx (after ITC)",
            f"${total_capex/1e6:.2f}M – ${itc_credit/1e6:.2f}M",
            f"${net_capex/1e6:.2f}M"
        )
        calc_row(
            "Simple Payback Period",
            f"Net CapEx / EBITDA = ${net_capex/1e6:.2f}M / ${ebitda_yr/1e6:.3f}M",
            f"{simple_pb:.1f} years" if simple_pb < 100 else ">25 years",
            "#1a6b45" if simple_pb <= 8 else "#8a5c2a" if simple_pb <= 12 else "#8b2d2d"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Revenue Waterfall")

        fig_wf = go.Figure(go.Waterfall(
            orientation='v',
            measure=['relative', 'relative', 'relative', 'total', 'relative', 'total'],
            x=['Energy Arb.', 'Resource Adequacy', 'Ancillary Svcs',
               'Gross Revenue', 'OpEx', 'EBITDA'],
            y=[energy_rev/1e6, ra_rev/1e6, ancil_rev/1e6, 0, -opex_yr/1e6, 0],
            text=[f"${v/1e6:.2f}M" for v in
                  [energy_rev, ra_rev, ancil_rev, gross_rev, opex_yr, ebitda_yr]],
            textposition='outside',
            connector=dict(line=dict(color='#94a3b8', width=1)),
            increasing=dict(marker_color='#1a6b45'),
            decreasing=dict(marker_color='#8b2d2d'),
            totals=dict(marker_color='#2d5986'),
        ))
        fig_wf.update_layout(
            height=340,
            yaxis_title="$M per year",
            plot_bgcolor='white', paper_bgcolor='white',
            margin=dict(l=40, r=20, t=20, b=40),
            showlegend=False,
        )
        st.plotly_chart(fig_wf, use_container_width=True)

        with st.expander("Key Caveats and Assumptions"):
            st.markdown("""
**Energy arbitrage** uses a constant annual spread. Actual spreads vary by season, time of day, and renewable curtailment patterns specific to this location.

**Resource Adequacy** value reflects 2024 CPUC NP15/SP15/ZP26 RA clearing prices. These shift year-to-year based on CPUC proceedings and load growth.

**Ancillary services** are modelled as a flat $/MW-yr rate. CAISO Regulation and Spinning Reserve markets are competitive and capacity-limited; actual revenues depend on dispatch strategy and co-optimization.

**OpEx** is estimated at 2.5% of total gross CapEx per year. This does not include insurance, land lease, or interconnection O&M.

**ITC** reflects the base 30% Investment Tax Credit under the Inflation Reduction Act (2022). Project-specific adders for domestic content (+10%) and energy community siting (+10%) can increase the effective rate to 40%.

**Revenue stacking conflicts** (e.g. simultaneous RA availability and energy dispatch) are not modelled. A dispatch optimization model is required for precise revenue estimation.
""")

# ═══════════════════════════════════════════════════════════════
# TAB ⑤: METHODOLOGY
# ═══════════════════════════════════════════════════════════════
with tab_method:
    st.markdown("### Methodology")
    st.markdown(
        "Full technical documentation covering the network model, scoring signals, "
        "LMP and resource adequacy data, economics formulas, data sources, and limitations."
    )
    st.markdown("<br>", unsafe_allow_html=True)
    try:
        with open(DATA_DIR + "methodology.pdf", "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="Download Methodology (PDF)",
            data=pdf_bytes,
            file_name="BESS_Siting_Methodology.pdf",
            mime="application/pdf",
            use_container_width=False,
        )
    except FileNotFoundError:
        st.error("Methodology PDF not found in data/ folder.")
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("California BESS Siting Intelligence Platform  |  PyPSA-USA elec_base_network_dem.nc  |  CAISO LMP 2024 actuals")


