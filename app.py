"""Neythal: coastal intelligence dashboard (prototype)."""
import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import data_sources as ds
from modules import theme
from modules.models import (blue_carbon_estimate, energy_estimate, ocean_future_scenario,
                            ocean_risk_score, tc_to_tco2e)
from modules.regions import REGIONS, get_region

st.set_page_config(page_title="Neythal: coastal intelligence", page_icon="🌊", layout="wide")

PAGES = {  # key: (icon, title, description, group)
    "overview": ("🌊", "Overview", "Latest sea temperature, stress and risk at a glance.", "Observe"),
    "climate": ("🌡️", "Climate monitor", "Sea-surface temperature, anomaly and heat stress over 90 days.", "Observe"),
    "life": ("🐠", "Marine life", "Where species have been recorded in the region.", "Observe"),
    "habitat": ("🪸", "Habitats", "Reefs, seagrass, mangroves and protected areas.", "Observe"),
    "energy": ("⚡", "Blue energy", "Cultivated seaweed to biogas: a what-if calculator.", "Estimate"),
    "carbon": ("🌿", "Blue carbon", "Seagrass conservation carbon scenarios.", "Estimate"),
    "twin": ("🔮", "Digital twin", "Warm the sea and watch the risk score respond.", "Estimate"),
    "warning": ("🚨", "Early warning", "Heat-stress levels from NOAA thresholds.", "Protect"),
    "pollution": ("🧪", "Pollution watch", "Satellite chlorophyll-a: an indicator of algal growth and water quality.", "Protect"),
}
ORDER = ["home"] + list(PAGES)
LABEL = {"home": "🏠 Home", **{k: f"{v[0]} {v[1]}" for k, v in PAGES.items()}}

st.session_state.setdefault("nav", "home")


def go_to(key):
    st.session_state["nav"] = key


def _jump():
    if st.session_state.get("jump"):
        st.session_state["nav"] = st.session_state["jump"]
    st.session_state["jump"] = None


mode = "dark" if st.session_state.get("dark", False) else "light"
theme.inject(mode)
PAL = theme.PALETTES[mode]

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown("### 🌊 Neythal")
    st.selectbox("Jump to", [k for k in ORDER if k != "home"], index=None, key="jump",
                 format_func=lambda k: LABEL[k], placeholder="Search a tool…", on_change=_jump)
    st.radio("Go to", ORDER, key="nav", format_func=lambda k: LABEL[k], label_visibility="collapsed")
    st.divider()
    region_key = st.selectbox("Region", [k for k, r in REGIONS.items() if r.enabled],
                              format_func=lambda k: REGIONS[k].name)
    st.caption("Palk Bay is planned, not enabled.")
    map_style = st.selectbox("Map style", ["Satellite", "Light", "Dark"])
    demo = st.toggle("Demo data (synthetic)", key="demo", help="Fake data for layout testing only.")
    st.toggle("Dark mode", key="dark")
    if st.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()

region = get_region(region_key)
page = st.session_state["nav"]


# ---------------- data ----------------
@st.cache_data(ttl=3600, show_spinner=False)
def _noaa(key):
    r = get_region(key)
    return ds.fetch_noaa_series(r.lat, r.lon)


@st.cache_data(ttl=86400, show_spinner=False)
def _habitat(kind, key):
    return ds.fetch_habitat(kind, get_region(key))


@st.cache_data(ttl=3600, show_spinner=False)
def _chl(key):
    r = get_region(key)
    return ds.fetch_chlorophyll(r.lat, r.lon)


@st.cache_data(ttl=3600, show_spinner=False)
def _obis(key):
    return ds.fetch_obis(get_region(key).wkt)


def load(kind):
    if demo:
        return {"noaa": ds.demo_series, "chl": ds.demo_chlorophyll}.get(kind, lambda: ds.demo_obis(region))()
    try:
        with st.spinner("Contacting data source…"):
            return {"noaa": _noaa, "chl": _chl}.get(kind, _obis)(region.key)
    except ds.DataUnavailable as exc:
        st.error(f"Data unavailable: {exc} Try Refresh data, or switch on Demo data to test the layout.")
        return None


def passport(res):
    meta = res["meta"]
    theme.chip("Demo data: synthetic" if meta["synthetic"] else "Live source", demo=meta["synthetic"])
    with st.expander("Data passport"):
        st.table(pd.DataFrame({"Field": [k for k in meta if k != "synthetic"],
                               "Value": [str(v) for k, v in meta.items() if k != "synthetic"]}))


ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
MARK = {"Satellite": "#FFD54A", "Light": "#B3261E", "Dark": "#4FD1C5"}
HAB_COLOR = {"coral": "#FF4D8D", "seagrass": "#2EE6A6", "mangrove": "#1FA34A", "protected": "#FFB300"}


def map_layout(fig, zoom=7):
    mp = dict(center=dict(lat=region.lat, lon=region.lon), zoom=zoom)
    if map_style == "Satellite":
        mp.update(style="white-bg", layers=[dict(sourcetype="raster", source=[ESRI], below="traces",
                                                 sourceattribution="Imagery © Esri, Maxar, Earthstar Geographics")])
    else:
        mp["style"] = "carto-darkmatter" if map_style == "Dark" else "carto-positron"
    fig.update_layout(map=mp, legend=dict(bgcolor=PAL["surface"], font=dict(color=PAL["ink"])))
    return fig


def box_trace():
    return go.Scattermap(lat=[region.south, region.south, region.north, region.north, region.south],
                         lon=[region.west, region.east, region.east, region.west, region.west], mode="lines",
                         line=dict(color="#FFFFFF" if map_style != "Light" else "#0A2530", width=2),
                         name="Region box", hoverinfo="skip")


def style(fig, h=340):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=30, b=8), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(color=PAL["ink"]),
                      colorway=[PAL["accent"], PAL["pearl"], "#E4572E"], legend_title_text="",
                      hoverlabel=dict(bgcolor=PAL["surface"], font=dict(color=PAL["ink"]), bordercolor=PAL["accent"]),
                      modebar=dict(bgcolor="rgba(0,0,0,0)", color=PAL["muted"], activecolor=PAL["accent"]))
    fig.update_xaxes(gridcolor=PAL["line"])
    fig.update_yaxes(gridcolor=PAL["line"])
    return fig


def band(score):
    return "No data" if score is None else next(
        (n for lim, n in ((25, "Low"), (50, "Moderate"), (75, "High")) if score < lim), "Very high")


def latest(df, col):
    s = df[col].dropna()
    return None if s.empty else float(s.iloc[-1])


def head(key):
    icon, title, desc, _ = PAGES[key]
    theme.hero(f"{icon} {title}", desc, page=True)


def fmt(v, unit, d=2):
    return "No data" if v is None else f"{v:.{d}f} {unit}"


# ---------------- pages ----------------
def page_home():
    theme.hero("Neythal", "The coast, understood. Neythal is the Sangam-era Tamil word for the seashore "
               "landscape. This prototype brings sea temperature, species records and blue-energy "
               "what-ifs together, starting with the Gulf of Mannar.", tamil="நெய்தல்")
    st.caption("Pick a tool below, use the search box in the sidebar, or the list on the left.")
    for group in ("Observe", "Estimate", "Protect"):
        keys = [k for k, v in PAGES.items() if v[3] == group]
        st.subheader(group)
        for col, k in zip(st.columns(len(keys)), keys):
            icon, title, desc, _ = PAGES[k]
            with col.container(key=f"tile_{k}"):
                st.markdown(f'<div class="tile-t">{icon} {html.escape(title)}</div>'
                            f'<div class="tile-d">{html.escape(desc)}</div>', unsafe_allow_html=True)
                st.button("Open", key=f"open_{k}", on_click=go_to, args=(k,))


def page_overview():
    head("overview")
    res = load("noaa")
    if not res:
        return
    passport(res)
    df = res["df"]
    sst, anom, dhw = latest(df, "CRW_SST"), latest(df, "CRW_SSTANOMALY"), latest(df, "CRW_DHW")
    risk = ocean_risk_score(anom)
    a, b, c, d = st.columns(4)
    a.metric("Sea temperature", fmt(sst, "°C"))
    b.metric("Anomaly", fmt(anom, "°C"))
    c.metric("Heat stress (DHW)", fmt(dhw, "°C-weeks"))
    d.metric("Priority score", "No data" if risk is None else f"{risk['score']} · {band(risk['score'])}")
    st.caption("The score counts temperature only. Set habitat and pollution pressure yourself in the "
               "Digital twin. It is a screening aid, not a damage prediction.")
    fig = px.line(df, x="time", y="CRW_SST", labels={"time": "", "CRW_SST": "°C"})
    st.plotly_chart(style(fig), width="stretch")


def page_climate():
    head("climate")
    res = load("noaa")
    if not res:
        return
    passport(res)
    df = res["df"]
    tabs = st.tabs(["Temperature", "Anomaly", "Heat stress"])
    for tab, col, lab in zip(tabs, ("CRW_SST", "CRW_SSTANOMALY", "CRW_DHW"),
                             ("°C", "°C above long-term mean", "°C-weeks")):
        with tab:
            fig = (px.bar if col == "CRW_SSTANOMALY" else px.line)(df, x="time", y=col, labels={"time": "", col: lab})
            st.plotly_chart(style(fig), width="stretch")
    st.download_button("Download CSV", df.to_csv(index=False), "neythal_noaa_series.csv", "text/csv")


def page_life():
    head("life")
    res = load("obis")
    if not res:
        return
    passport(res)
    df = res["df"]
    st.warning("Records show where species were observed, not how many exist. Sampling effort is "
               "uneven, and a blank area does not mean absence.")
    a, b = st.columns(2)
    a.metric("Records shown", len(df))
    b.metric("Species names", df["scientificName"].nunique())
    fig = go.Figure([box_trace(), go.Scattermap(
        lat=df["decimalLatitude"], lon=df["decimalLongitude"], mode="markers", text=df["scientificName"],
        hoverinfo="text", name="Records", marker=dict(size=9, color=MARK[map_style], opacity=0.85))])
    st.plotly_chart(style(map_layout(fig), 460), width="stretch")
    top = df["scientificName"].value_counts().head(12).rename_axis("Species").reset_index(name="Records")
    st.plotly_chart(style(px.bar(top, x="Records", y="Species", orientation="h")), width="stretch")


def page_habitat():
    head("habitat")
    st.caption("Reference maps from UNEP-WCMC and partners. They show where habitat was mapped in the past, "
               "not today's extent, and a blank area does not prove absence.")
    picks = st.multiselect("Layers", list(ds.HABITAT), default=list(ds.HABITAT),
                           format_func=lambda k: ds.HABITAT[k][1])
    fig, rows, cols = go.Figure([box_trace()]), [], st.columns(max(len(picks), 1))
    for col, k in zip(cols, picks):
        label = ds.HABITAT[k][1]
        try:
            with st.spinner(f"Loading {label.lower()}…"):
                res = _habitat(k, region.key)
        except ds.DataUnavailable as exc:
            col.error(f"{label}: {exc} Try Refresh data.")
            continue
        col.metric(label, f"{res['n']} polygons")
        rows.append({"Layer": label, **{f: str(v) for f, v in res["meta"].items() if f in
                     ("Source", "Observation period", "Retrieved (UTC)", "Limitations")}})
        if res["n"]:
            colr = HAB_COLOR[k]
            fig.add_trace(go.Choroplethmap(
                geojson=res["geojson"], locations=list(range(res["n"])), z=[1] * res["n"],
                featureidkey="properties.nid", colorscale=[[0, colr], [1, colr]], showscale=False,
                text=res["names"], hoverinfo="text", name=label, showlegend=True,
                marker=dict(opacity=0.25 if k == "protected" else 0.6, line=dict(color=colr, width=2))))
        else:
            col.caption("No polygons from this layer fall in the region box.")
    st.plotly_chart(style(map_layout(fig), 480), width="stretch")
    if rows:
        with st.expander("Data passport for each layer"):
            st.table(pd.DataFrame(rows))
    st.caption("Seagrass shown here is for conservation context only. Never harvest it for energy.")


def page_energy():
    head("energy")
    st.info("Cultivated seaweed or macroalgae only. Never harvest seagrass, and avoid wild beds.")
    a, b = st.columns(2)
    bio = a.number_input("Dry biomass (kg)", 0.0, 1e7, 1000.0, 100.0)
    days = b.number_input("Processing time (days)", 1, 365, 30)
    my = a.number_input("Methane yield (m³ per kg dry biomass), an assumption", 0.0, 1.0, 0.20, 0.01)
    eff = b.slider("Electrical efficiency, an assumption", 0.0, 1.0, 0.35, 0.01)
    try:
        r = energy_estimate(bio, my, eff, int(days))
    except ValueError as exc:
        st.error(str(exc))
        return
    c = st.columns(4)
    c[0].metric("Methane", f"{r['methane_m3']:,.0f} m³")
    c[1].metric("Gross energy", f"{r['gross_energy_kwh']:,.0f} kWh")
    c[2].metric("Electricity*", f"{r['electricity_kwh']:,.0f} kWh")
    c[3].metric("Average power*", f"{r['average_power_kw']:.2f} kW")
    st.caption("*Gross estimated electricity before parasitic loads. Uses 9.94 kWh/m³ as an "
               "illustrative energy content. The yield is not a measured or validated value.")
    rows = [{"Case": n, "Methane yield (m³/kg)": round(my * f, 3),
             "Electricity (kWh)": round(energy_estimate(bio, my * f, eff, int(days))["electricity_kwh"])}
            for n, f in (("Low (×0.5)", 0.5), ("Central", 1.0), ("High (×1.5)", 1.5))]
    st.table(pd.DataFrame(rows))


def page_carbon():
    head("carbon")
    st.info("An illustrative scenario for seagrass conservation, not a verified local carbon inventory.")
    unit = st.radio("Annual rate unit", ["tC", "tCO₂e"], horizontal=True)
    a, b, c = st.columns(3)
    area = a.number_input("Area (hectares)", 0.0, 1e6, 10.0, 1.0)
    rate = b.number_input(f"Rate ({unit} per hectare per year), an assumption", 0.0, 100.0, 1.0, 0.1)
    years = c.number_input("Years", 1, 100, 5)
    try:
        total = blue_carbon_estimate(area, rate, int(years))
    except ValueError as exc:
        st.error(str(exc))
        return
    st.metric(f"Scenario total ({unit})", f"{total:,.1f}")
    if unit == "tC":
        st.caption(f"Equivalent to about {tc_to_tco2e(total):,.1f} tCO₂e (× 44/12).")


def page_twin():
    head("twin")
    res = load("noaa")
    base = latest(res["df"], "CRW_SSTANOMALY") if res else None
    if res:
        passport(res)
    if base is None:
        base = st.number_input("No live anomaly. Enter a starting anomaly (°C)", -5.0, 5.0, 0.5, 0.1)
    st.caption(f"Starting anomaly: {base:.2f} °C. A user-controlled what-if, not an ocean forecast.")
    a, b, c = st.columns(3)
    warm = a.slider("Extra warming (°C)", 0.0, 4.0, 1.0, 0.25)
    hab = b.slider("Habitat pressure (0-100)", 0, 100, 20)
    pol = c.slider("Pollution pressure (0-100)", 0, 100, 10)
    now, then = ocean_risk_score(base, hab, pol), ocean_future_scenario(base, warm, hab, pol)
    x, y = st.columns(2)
    x.metric("Now", f"{now['score']} · {band(now['score'])}")
    y.metric("Scenario", f"{then['score']} · {band(then['score'])}", delta=then["score"] - now["score"],
             delta_color="inverse")
    sweep = pd.DataFrame({"Warming (°C)": [i / 4 for i in range(17)]})
    sweep["Score"] = [ocean_future_scenario(base, w, hab, pol)["score"] for w in sweep["Warming (°C)"]]
    st.plotly_chart(style(px.line(sweep, x="Warming (°C)", y="Score", markers=True)), width="stretch")


def page_warning():
    head("warning")
    res = load("noaa")
    if not res:
        return
    passport(res)
    dhw, anom = latest(res["df"], "CRW_DHW"), latest(res["df"], "CRW_SSTANOMALY")
    if dhw is None:
        level = "No data. This is not the same as no risk."
    elif dhw >= 8:
        level = "In the range NOAA labels Alert Level 2 (DHW 8 or more)"
    elif dhw >= 4:
        level = "In the range NOAA labels Alert Level 1 (DHW 4 to 8)"
    else:
        level = "Below the Alert Level 1 threshold (DHW under 4)"
    st.metric("Heat stress level", level)
    st.caption(f"Latest DHW: {fmt(dhw, '°C-weeks')}. Derived from NOAA's published 4 and 8 °C-week "
               "thresholds. It is not an official alert message: check coralreefwatch.noaa.gov.")
    risk = ocean_risk_score(anom)
    if risk:
        st.markdown(f"**Prototype flag:** monitoring priority {band(risk['score'])} "
                    f"({risk['score']}/100). Temperature only; not validated.")


def page_pollution():
    head("pollution")
    res = load("chl")
    if not res:
        return
    passport(res)
    df = res["df"]
    now, med = latest(df, "chlorophyll"), float(df["chlorophyll"].median())
    a, b, c = st.columns(3)
    a.metric("Latest chlorophyll-a", fmt(now, "mg/m³", 3))
    b.metric("Median of this period", fmt(med, "mg/m³", 3))
    c.metric("Latest vs median", "No data" if now is None else f"{(now / med - 1) * 100:+.0f}%")
    fig = px.line(df, x="time", y="chlorophyll", markers=True, labels={"time": "", "chlorophyll": "mg/m³"})
    fig.add_hline(y=med, line_dash="dash", line_color=PAL["pearl"], annotation_text="median",
                  annotation_font_color=PAL["ink"])
    st.plotly_chart(style(fig), width="stretch")
    st.caption("Chlorophyll-a tracks algal growth. A rise can follow nutrient runoff or sewage, but also "
               "natural blooms and upwelling, so treat it as a prompt to investigate, not proof of pollution.")


with st.container(key=f"page_{page}"):
    {"home": page_home, "overview": page_overview, "climate": page_climate, "life": page_life,
     "habitat": page_habitat, "energy": page_energy, "carbon": page_carbon, "twin": page_twin,
     "warning": page_warning, "pollution": page_pollution}[page]()
    st.markdown('<div class="foot">Neythal is a prototype decision-support tool, not an operational '
                'monitoring system.</div>', unsafe_allow_html=True)
