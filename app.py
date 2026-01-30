import pandas as pd
import plotly.express as px
import requests
import streamlit as st

url = "https://n8n.yrieix.com/webhook/0ef9d95d-4576-445d-9d6c-3fc371fc9cfc?from=streamlit-cars-selfhosted"

st.set_page_config(page_title="Car Explorer", layout="wide", page_icon="🚘")

_, right, right_right = st.columns([8, 2, 2])
if right.button("Balloons", icon="🎈"):
    requests.get(f"{url}&type=like&section=manual")
    st.balloons()

with right_right.popover("Contact", icon="📬"):
    st.markdown("""
    ### Hello!
    I'm [**Yrieix Leprince**](https://www.linkedin.com/in/yrieixleprince/), creator of this page 😃

    You can contact me right here!

    ---
    """)
    name = st.text_input("Name", placeholder="John Doe")
    contact = st.text_input("Contact ✉️/📞/📯", placeholder="john.doe@gmail.com")
    content = st.text_area("Object") 
    if st.button("Send", icon="📩"):
        contactPayload = {"from": "streamlit-cars-selfhosted", "name": name, "contact": contact, "content": content}
        response = requests.get(f"https://n8n.yrieix.com/webhook/4d9ac11b-8c8a-4108-ac78-a57279b363b9", data=contactPayload)
        st.toast(response.json()['content'], icon="😍")
        

st.title("🚗 Skoda vs Volkswagen vs Toyota 🚘")
st.text(
    "This is a tool to explore some cars models: Karoq vs Tiguan vs Octavia vs T-Roc vs RAV."
)


_, exp_col, _ = st.columns([1, 3, 1])
with exp_col:
    with st.expander("**📖 How to Use This Page**"):
        requests.get(f"{url}&type=expand&section=manual")
        st.markdown("""
                    However you like! 🤷🏻

                    But here's my recommendation:

                    On the scatter graph below you can explore the data through clicking on
                    the legend to select a category (double click to unselect),
                    you can also zoom and hover the data to show more information!

                    👈 On the left hand side you have also a tab where you can play with
                    advanced features. Just try them all and see what knowledge
                    you can learn from raw data exploration!
                    """)

        st.info("""
                This page's content has been extracted from lacentrale.fr around January, 20th.
                This was a specific project to help a friend, and I had no intent to
                frequently update the data.
                """)
    with st.expander("**🧠 What does the data tell?**"):
        requests.get(f"{url}&type=expand&section=explanation")
        st.markdown("""
            Here are three points to get started with this page:
            1. There is a **big trend**: the more the car goes on the road, the lower its value.
            """)
        st.image(
            "./docs/price_f_kilometers.png",
            caption="The more a car goes on the road, the lower its value.",
        )
        st.markdown("""
            2. Then we can picture ourself two areas of the scatter plot:
            **the new cars and the old ones**.
            """)
        st.image("./docs/big-trends.png", caption="New cars and the old ones.")
        st.markdown("""
            3. Once done we can deduct the place where the second hand offer has
            the most value: **the bottom left** part of the plot.
            """)
        st.image(
            "./docs/high-vs-low-value.png",
            caption="High value opportunities vs low values",
        )


# Color selector
st.sidebar.header("Chart")
color_by = st.sidebar.selectbox(
    "Color by",
    options=[
        "brand",
        "model",
        "year",
        "gas",
        "label",
        "gearbox",
        "engineVolume",
        "enginePower",
        "engineType",
    ],
    index=0,
)


# ---- Data loading ----
@st.cache_data
def load_csv(uploaded_file) -> pd.DataFrame:
    return pd.read_csv(uploaded_file)


df = load_csv("data/processed/data.csv")

# ---- Validate required columns ----
required_cols = {
    "brand",
    "engineType",
    "engineVolume",
    "enginePower",
    "line",
    "model",
    "price",
    "km",
    "year",
    "gearbox",
    "gas",
    "label",
}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"Missing required columns: {sorted(missing)}")
    st.stop()

# ---- Normalize / coerce types ----
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["km"] = pd.to_numeric(df["km"], errors="coerce")
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
df["engineVolume"] = pd.to_numeric(df["engineVolume"], errors="coerce").astype(
    "Float64"
)
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
    selected = st.sidebar.multiselect(col, options=options, default=defaults, key=col)
    return selected


selected_brand = multiselect_filter("brand")
selected_model = multiselect_filter("model")
selected_gearboxes = multiselect_filter(
    "gearbox", preferred_defaults=["Manuelle", "Auto"]
)
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

# Optional numeric ranges
with st.sidebar.expander("Optional ranges", expanded=False):
    if not filtered.empty:
        km_min, km_max = float(filtered["km"].min()), float(filtered["km"].max())
        price_min, price_max = float(filtered["price"].min()), float(
            filtered["price"].max()
        )
        year_min, year_max = int(filtered["year"].min()), int(filtered["year"].max())
        enginePower_min, enginePower_max = int(filtered["enginePower"].min()), int(
            filtered["enginePower"].max()
        )
    else:
        km_min = km_max = 0.0
        price_min = price_max = 0.0
        year_min = year_max = 0
        enginePower_min = enginePower_max = 0

    km_range = st.slider("km", km_min, km_max, (km_min, km_max), key="km_range")
    price_range = st.slider(
        "price", price_min, price_max, (price_min, price_max), key="price_range"
    )
    year_range = st.slider(
        "year", year_min, year_max, (year_min, year_max), key="year_range"
    )
    enginePower_range = st.slider(
        "engine power",
        enginePower_min,
        enginePower_max,
        (enginePower_min, enginePower_max),
        key="engine_power_range",
    )


if not filtered.empty:
    filtered = filtered[
        (filtered["km"].between(km_range[0], km_range[1]))
        & (filtered["price"].between(price_range[0], price_range[1]))
        & (filtered["year"].between(year_range[0], year_range[1]))
        & (filtered["enginePower"].between(enginePower_range[0], enginePower_range[1]))
    ]

# ---- Main view ----
left, right = st.columns([2, 1], gap="large")

with left:
    st.subheader("Price = f(km)")

    if filtered.empty:
        st.warning("No rows match your filters.")
    else:
        # Hover: show all non-(x,y,color) columns (keeps it useful without being too noisy)
        base_exclude = {"price", "km"}
        hover_cols = [c for c in filtered.columns if c not in base_exclude]

        # Better ordering: put the most relevant fields first if they exist
        preferred_hover_order = [
            "brand",
            "model",
            "year",
            "gearbox",
            "gas",
            "label",
            "price",
            "km",
        ]
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
        st.plotly_chart(fig, width="stretch")

st.subheader("Data preview")
st.caption(f"{len(filtered):,} rows shown (out of {len(plot_df):,})")
st.dataframe(
    filtered.drop("idx", axis=1).drop("title", axis=1), width="stretch", height=650
)

requests.get(f"{url}&type=view&section=home", data=st.session_state)
