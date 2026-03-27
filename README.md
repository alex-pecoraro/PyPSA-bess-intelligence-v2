# California BESS Siting Intelligence Platform

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pypsa-bess-intelligence-v2.streamlit.app)

A utility-scale battery energy storage system (BESS) site selection tool for California, built on a DC Optimal Power Flow run against the full PyPSA-USA 2050 California network.

---

## What it does

Scores all **3,453 California transmission substations** (138–765 kV) across four grid signals derived from a solved DC Linear Optimal Power Flow, then overlays a county-level land buildability filter to flag sites with structural development constraints.

**Grid signals (composite score 0–100)**

| Signal | Weight | Source |
|--------|--------|--------|
| Renewable Saturation | 35% | NREL WRF/ERA5 solar + wind CFs via PyPSA-USA |
| Load Imbalance | 25% | PyPSA-USA 2050 high-electrification demand |
| Congestion Score | 20% | Line utilization from DC LOPF solution |
| LMP Attractiveness | 20% | Nodal LMPs from DC LOPF dual variables |

**Land Buildability Filter (sidebar overlay)**

| Rating | Criteria |
|--------|----------|
| Clear (498 sites) | <25% county protected land + Low flood risk |
| Limited (2,440 sites) | 25–55% protected OR Medium flood risk |
| Restricted (515 sites) | >55% protected OR High flood risk |

Sources: PADUS 3.0 (USGS), FEMA NFIP county statistics. County-level estimates.

---

## Tabs

- **Screen** — map of all substations with filters, rankings table, shortlist selector
- **Compare** — side-by-side radar and bar charts for up to 8 shortlisted sites
- **Site Brief** — single-site detail: grid signals, infrastructure, LMPs, land context
- **Economics** — project pro-forma with energy arbitrage, RA, ancillary services, ITC
- **Methodology** — downloadable PDF with full technical documentation

---

## Running locally

```bash
pip install -r requirements.txt
python -m streamlit run network_dashboard_v2.py
```

---

## Data

```
data/
  bus_data_v2.parquet      — 3,453 CA substations, all signals + land buildability
  lines_v2.parquet         — 3,913 CA transmission lines with coordinates
  methodology.pdf          — Full technical methodology document
```

The parquet was built by:
1. Loading `elec_base_network_dem.nc` (PyPSA-USA California network)
2. Running a DC LOPF via `n.optimize(solver_name='highs')` on 24 representative snapshots
3. Extracting nodal LMPs (`n.buses_t.marginal_price`) and line utilization (`n.lines_t.p0`)
4. Normalizing all signals to 0–100 and computing the weighted composite
5. Joining county-level land buildability data (PADUS 3.0, FEMA)

---

## Data sources

| Dataset | Source | License |
|---------|--------|---------|
| Network topology | [PyPSA-USA](https://github.com/PyPSA/pypsa-usa) (Breakthrough Energy / NREL) | MIT |
| 2050 demand projections | PyPSA-USA high-electrification scenario | MIT |
| Renewable capacity factors | NREL WRF/ERA5 via PyPSA-USA | MIT |
| Nodal LMPs + congestion | DC LOPF (PyPSA v0.35 / HiGHS solver) | MIT / LGPL-3 |
| Substation IDs | [HIFLD Open Data](https://hifld-geoplatform.hub.arcgis.com/) (DHS) | CC0 |
| RA pricing | CPUC RA proceedings (2024) | Public record |
| Protected land % | [PADUS 3.0](https://www.usgs.gov/programs/gap-analysis-project) (USGS GAP) | Public domain |
| Flood risk | FEMA NFIP county statistics | Public domain |
| County FIPS codes | US Census Bureau | Public domain |

---

## Stack

Python · Streamlit · Plotly · PyPSA · HiGHS (LP solver) · pandas · ReportLab
