from pathlib import Path
import json

import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns


st.set_page_config(
    page_title="Visualisasi Data Malaysia",
    page_icon="📊",
    layout="wide"
)

BASE = Path(__file__).resolve().parent


@st.cache_data
def load_files():
    income = pd.read_csv(BASE / "income_clean_2024.csv")
    poverty = pd.read_csv(BASE / "poverty_clean_2024.csv")
    population = pd.read_csv(BASE / "population_clean_2024.csv")

    boundaries = gpd.read_file(BASE / "sempadan_daerah.geojson")

    with open(BASE / "padanan_nama.json", encoding="utf-8") as f:
        aliases = json.load(f)

    return income, poverty, population, boundaries, aliases


income, poverty, population, boundaries, aliases = load_files()

settings = {
    "Pendapatan Isi Rumah": {
        "data": income,
        "value": "income_median",
        "label": "Pendapatan Median Isi Rumah (RM)",
        "unit": "RM",
        "color": "steelblue",
        "cmap": "YlGnBu",
        "objective": (
            "Membandingkan pendapatan median isi rumah antara "
            "daerah di Malaysia dan mengenal pasti perbezaan "
            "tahap pendapatan pada tahun 2024."
        )
    },
    "Kemiskinan Isi Rumah": {
        "data": poverty,
        "value": "poverty_relative",
        "label": "Kadar Kemiskinan Relatif (%)",
        "unit": "%",
        "color": "coral",
        "cmap": "YlOrRd",
        "objective": (
            "Membandingkan kadar kemiskinan relatif antara "
            "daerah di Malaysia dan mengenal pasti daerah "
            "dengan kadar tertinggi dan terendah pada tahun 2024."
        )
    },
    "Taburan Penduduk": {
        "data": population,
        "value": "population",
        "label": "Populasi (ribu orang)",
        "unit": "ribu orang",
        "color": "seagreen",
        "cmap": "YlGn",
        "objective": (
            "Menganalisis taburan penduduk mengikut daerah "
            "di Malaysia dan mengenal pasti perbezaan jumlah "
            "penduduk antara daerah pada tahun 2024."
        )
    }
}

st.sidebar.title("Navigasi")
page = st.sidebar.radio("Pilih halaman", list(settings))
cfg = settings[page]
value = cfg["value"]

states = sorted(cfg["data"]["state"].unique())
state = st.sidebar.selectbox(
    "Pilih negeri",
    ["Semua negeri"] + states
)

ranking = st.sidebar.radio(
    "Paparan carta bar",
    ["Tertinggi", "Terendah"]
)

number = st.sidebar.slider(
    "Bilangan daerah dalam carta bar",
    min_value=5,
    max_value=20,
    value=10
)

df = cfg["data"].copy()

if state != "Semua negeri":
    df = df[df["state"] == state].copy()

if df.empty:
    st.warning("Tiada data untuk pilihan ini.")
    st.stop()

df["Kawasan"] = df["district"] + " — " + df["state"]

st.title(page)
st.caption(f"Tahun 2024 | Skop: {state}")
st.info("Objektif: " + cfg["objective"])


def format_value(x):
    if cfg["unit"] == "RM":
        return f"RM{x:,.0f}"
    if cfg["unit"] == "%":
        return f"{x:,.1f}%"
    return f"{x:,.1f} ribu orang"


# SUMMARY BOX
maximum = df[value].max()
minimum = df[value].min()

highest = df.loc[df[value] == maximum, "Kawasan"].tolist()
lowest = df.loc[df[value] == minimum, "Kawasan"].tolist()

col1, col2, col3 = st.columns(3)

col1.metric("Bilangan daerah", len(df))
col2.metric("Nilai tertinggi", format_value(maximum))
col3.metric("Nilai terendah", format_value(minimum))

st.write("**Daerah tertinggi:** " + "; ".join(highest))
st.write("**Daerah terendah:** " + "; ".join(lowest))

# PILIH REKOD UNTUK GRAF
ascending = ranking == "Terendah"

selected = df.sort_values(
    [value, "state", "district"],
    ascending=[ascending, True, True]
).head(number)

st.caption(
    "Summary box, histogram dan peta menggunakan semua daerah "
    "dalam skop negeri yang dipilih. Carta bar menggunakan "
    "bilangan daerah yang dipilih di sidebar. Jika nilai seri "
    "pada had paparan, susunan nama menentukan rekod yang dipaparkan."
)

# GRAF 1: CARTA BAR
st.subheader("1. Perbandingan Antara Daerah")

bar_data = selected.sort_values(value)

fig, ax = plt.subplots(figsize=(11, 7))

bars = ax.barh(
    bar_data["Kawasan"],
    bar_data[value],
    color=cfg["color"]
)

labels = [
    f"{x:,.0f}" if cfg["unit"] == "RM" else f"{x:,.1f}"
    for x in bar_data[value]
]

ax.bar_label(bars, labels=labels, padding=4)
ax.set_xlim(0, max(float(bar_data[value].max()) * 1.2, 1))
ax.set_xlabel(cfg["label"])
ax.set_ylabel("Daerah")
ax.set_title(
    f"{len(selected)} Daerah {ranking}, 2024"
)
ax.grid(axis="x", alpha=0.3)
ax.set_axisbelow(True)
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)

# GRAF 2: HISTOGRAM
st.subheader("2. Taburan Nilai Antara Daerah")

# Gunakan semua daerah dalam skop negeri yang dipilih
nilai_histogram = df[value].dropna()

fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(
    nilai_histogram,
    bins="auto",
    color=cfg["color"],
    edgecolor="white"
)

ax.set_title(
    f"Taburan {cfg['label']} Mengikut Daerah, 2024"
)
ax.set_xlabel(cfg["label"])
ax.set_ylabel("Bilangan Daerah")

# Bilangan daerah dipaparkan sebagai nombor bulat
from matplotlib.ticker import MaxNLocator
ax.yaxis.set_major_locator(MaxNLocator(integer=True))

ax.grid(axis="y", alpha=0.3)
ax.set_axisbelow(True)

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.caption(
    "Histogram menggunakan semua daerah dalam skop negeri "
    "yang dipilih. Setiap bar menunjukkan bilangan daerah "
    "dalam sesuatu julat nilai. Pilihan tertinggi/terendah "
    "dan slider bilangan daerah hanya mempengaruhi carta bar."
)

# GRAF 3: PETA
st.subheader("3. Taburan Geografi")

map_data = df[["state", "district", value]].copy()

for item in aliases:
    mask = (
        (map_data["state"] == item["state"])
        & (map_data["district"] == item["nama_asal"])
    )
    map_data.loc[mask, "district"] = item["nama_peta"]

boundary_scope = boundaries.copy()

if state != "Semua negeri":
    boundary_scope = boundary_scope[
        boundary_scope["state"] == state
    ].copy()

keys = boundary_scope[["state", "district"]].drop_duplicates()

check = map_data.merge(
    keys,
    on=["state", "district"],
    how="left",
    indicator=True,
    validate="one_to_one"
)

unmatched = check[check["_merge"] == "left_only"]

map_df = boundary_scope.merge(
    map_data,
    on=["state", "district"],
    how="left",
    validate="many_to_one"
)

if boundary_scope.empty:
    st.warning("Tiada sempadan untuk negeri yang dipilih.")

elif map_df[value].notna().sum() == 0:
    st.warning("Tiada data yang dapat dipadankan pada peta.")

else:
    fig, ax = plt.subplots(figsize=(14, 7))

    map_df.plot(
        column=value,
        cmap=cfg["cmap"],
        vmin=0,
        vmax=max(float(df[value].max()), 1),
        edgecolor="white",
        linewidth=0.3,
        legend=True,
        legend_kwds={
            "label": cfg["label"],
            "shrink": 0.7
        },
        missing_kwds={
            "color": "lightgrey",
            "edgecolor": "white"
        },
        ax=ax
    )

    ax.set_title(f"{page} Mengikut Daerah, 2024")
    ax.set_axis_off()
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

st.caption(
    "Kelabu: kawasan tanpa padanan data. "
    "Padanan nama tidak menjamin sempadan fail peta "
    "sama sepenuhnya dengan sempadan daerah tahun 2024."
)

if not unmatched.empty:
    st.warning(
        f"{len(unmatched)} daerah tiada padanan sempadan. "
        "Daerah ini kekal dalam analisis, tetapi tidak "
        "dipetakan secara berasingan."
    )

    st.dataframe(
        unmatched[["state", "district", value]],
        hide_index=True
    )

if page == "Taburan Penduduk":
    st.caption(
        "Unit populasi ialah ribu orang. "
        "Peta menunjukkan jumlah penduduk, bukan kepadatan."
    )

# INTERPRETASI
st.subheader("Interpretasi")

st.write(
    f"Dalam skop {state}, sebanyak {len(df)} daerah dianalisis. "
    f"Nilai tertinggi ialah {format_value(maximum)}, "
    f"dicatatkan oleh {'; '.join(highest)}. "
    f"Nilai terendah ialah {format_value(minimum)}, "
    f"dicatatkan oleh {'; '.join(lowest)}. "
    f"Jurang antara nilai tertinggi dan terendah ialah "
    f"{maximum - minimum:,.1f} "
    f"{'mata peratusan' if cfg['unit'] == '%' else cfg['unit']}."
)

st.write(
    "Carta bar membandingkan nilai daerah yang dipilih. "
    "Histogram menunjukkan taburan nilai antara semua daerah "
    "dalam skop pilihan, dengan ketinggian bar mewakili bilangan "
    "daerah dalam setiap julat nilai. Peta menunjukkan taburan "
    "geografi bagi daerah yang mempunyai padanan sempadan. "
    "Visualisasi ini bersifat deskriptif dan tidak membuktikan "
    "sebab perbezaan antara daerah."
)

with st.expander("Lihat semua data dalam skop pilihan"):
    st.dataframe(
        df[["state", "district", value]].sort_values(
            value, ascending=False
        ),
        hide_index=True
    )

st.download_button(
    "Muat turun data pilihan",
    data=df[["state", "district", value]].to_csv(
        index=False
    ).encode("utf-8"),
    file_name=f"{value}_2024.csv",
    mime="text/csv"
)

st.caption(
    "Sumber: Jabatan Perangkaan Malaysia (DOSM). "
    "Data analisis ditapis kepada tahun 2024."
)
