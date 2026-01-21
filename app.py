# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Car Explorer", layout="wide")
st.title("🚗 Karoq vs Tiguan 🚘")
st.text("This is a comparison between the Karoq (Skoda) and the Tiguan (Volkswagen) cars.")

# ---- Data loading ----
@st.cache_data
def load_csv(uploaded_file) -> pd.DataFrame:
    return pd.read_csv(uploaded_file)


df = load_csv("data/processed/data.csv")

# ---- Validate required columns ----
required_cols = {"brand", "engineType", "engineVolume", "enginePower", "line", "model", "price", "km", "year", "gearbox", "gas", "label"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"Missing required columns: {sorted(missing)}")
    st.stop()

# ---- Normalize / coerce types ----
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["km"] = pd.to_numeric(df["km"], errors="coerce")
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
df["engineVolume"] = pd.to_numeric(df["engineVolume"], errors="coerce").astype("Float64")
df["enginePower"] = pd.to_numeric(df["enginePower"], errors="coerce").astype("Int64")

for c in ["brand", "line", "model", "gearbox", "gas", "label"]:
    df[c] = df[c].astype(str)

plot_df = df.dropna(subset=["price", "km", "year", "gearbox", "gas", "label"]).copy()

# ---- Sidebar filters ----
st.sidebar.header("Filters")

def multiselect_filter(col: str, preferred_defaults=None):
    preferred_defaults = preferred_defaults or []
    options = sorted(plot_df[col].dropna().unique().tolist())
    defaults = [v for v in preferred_defaults if v in options] or options
    selected = st.sidebar.multiselect(col, options=options, default=defaults)
    return selected

selected_brand = multiselect_filter("brand")
selected_model = multiselect_filter("model")
selected_gearboxes = multiselect_filter("gearbox", preferred_defaults=["Manuelle", "Auto"])
selected_gas = multiselect_filter("gas")
selected_label = multiselect_filter("label")
selected_engine_type = multiselect_filter("engineType")

filtered = plot_df.copy()

# Apply categorical filters (if user clears all, show none rather than everything)

if selected_brand:
    filtered = filtered[filtered["brand"].isin(selected_brand)]

if selected_model:
    filtered = filtered[filtered["model"].isin(selected_model)]

if selected_gearboxes:
    filtered = filtered[filtered["gearbox"].isin(selected_gearboxes)]

if selected_gas:
    filtered = filtered[filtered["gas"].isin(selected_gas)]

if selected_label:
    filtered = filtered[filtered["label"].isin(selected_label)]

if selected_engine_type:
    filtered = filtered[filtered["engineType"].isin(selected_engine_type)]


# Color selector
st.sidebar.header("Chart")
color_by = st.sidebar.selectbox(
    "Color by",
    options=["brand", "model", "year", "gas", "label", "gearbox", "engineVolume", "enginePower", "engineType"],
    index=0,
)

# Optional numeric ranges
with st.sidebar.expander("Optional ranges", expanded=False):
    if not filtered.empty:
        km_min, km_max = float(filtered["km"].min()), float(filtered["km"].max())
        price_min, price_max = float(filtered["price"].min()), float(filtered["price"].max())
        year_min, year_max = int(filtered["year"].min()), int(filtered["year"].max())
        enginePower_min, enginePower_max = int(filtered["enginePower"].min()), int(filtered["enginePower"].max())
        engineVolume_min, engineVolume_max = int(filtered["engineVolume"].min()), int(filtered["engineVolume"].max())
    else:
        km_min = km_max = 0.0
        price_min = price_max = 0.0
        year_min = year_max = 0
        enginePower_min = enginePower_max = 0
        engineVolume_min = engineVolume_max = 0

    km_range = st.slider("km", km_min, km_max, (km_min, km_max))
    price_range = st.slider("price", price_min, price_max, (price_min, price_max))
    year_range = st.slider("year", year_min, year_max, (year_min, year_max))
    enginePower_range = st.slider("engine power", enginePower_min, enginePower_max, (enginePower_min, enginePower_max))
    engineVolume_range = st.slider("engine volume", engineVolume_min, engineVolume_max, (engineVolume_min, engineVolume_max))
    

if not filtered.empty:
    filtered = filtered[
        (filtered["km"].between(km_range[0], km_range[1]))
        & (filtered["price"].between(price_range[0], price_range[1]))
        & (filtered["year"].between(year_range[0], year_range[1]))
        & (filtered["enginePower"].between(enginePower_range[0], enginePower_range[1]))
        & (filtered["engineVolume"].between(engineVolume_range[0], engineVolume_range[1]))
    ]

# ---- Main view ----
left, right = st.columns([2, 1], gap="large")

with left:
    st.subheader("Scatter: price = f(km)")

    if filtered.empty:
        st.warning("No rows match your filters.")
    else:
        # Hover: show all non-(x,y,color) columns (keeps it useful without being too noisy)
        base_exclude = {"price", "km"}
        hover_cols = [c for c in filtered.columns if c not in base_exclude]

        # Better ordering: put the most relevant fields first if they exist
        preferred_hover_order = ["brand", "model", "year", "gearbox", "gas", "label", "price", "km"]
        hover_cols_sorted = []
        for c in preferred_hover_order:
            if c in hover_cols:
                hover_cols_sorted.append(c)
        hover_cols_sorted += [c for c in hover_cols if c not in hover_cols_sorted]

        fig = px.scatter(
            filtered,
            x="km",
            y="price",
            color=color_by,
            hover_data=hover_cols_sorted,
            opacity=0.8,
        )
        fig.update_layout(
            height=650,
            xaxis_title="km",
            yaxis_title="price €",
            legend_title=color_by,
        )
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Data preview")
    st.caption(f"{len(filtered):,} rows shown (out of {len(plot_df):,})")
    st.dataframe(filtered.drop("idx", axis=1).drop("title", axis=1), use_container_width=True, height=650)

