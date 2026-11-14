from pathlib import Path
import json

import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm, Normalize
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
    "Summary box, histogram dan box plot menggunakan semua daerah "
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

# GRAF 3: BOX PLOT
st.subheader("3. Taburan Nilai Mengikut Negeri")

# Gunakan semua rekod dalam skop negeri yang dipilih
box_data = df[["state", "district", value]].dropna(
    subset=[value]
).copy()

# Susun negeri berdasarkan median nilai daerah
susunan_negeri = (
    box_data.groupby("state")[value]
    .median()
    .sort_values()
    .index
    .tolist()
)

tinggi_graf = max(4, len(susunan_negeri) * 0.5)

fig, ax = plt.subplots(figsize=(11, tinggi_graf))

sns.boxplot(
    data=box_data,
    x=value,
    y="state",
    order=susunan_negeri,
    color=cfg["color"],
    showfliers=False,
    ax=ax
)

# Paparkan setiap daerah sebagai satu titik.
# Titik turut menunjukkan daerah di luar whisker.
sns.stripplot(
    data=box_data,
    x=value,
    y="state",
    order=susunan_negeri,
    color="black",
    alpha=0.5,
    size=4,
    jitter=0.15,
    ax=ax
)

ax.set_title(
    f"Taburan {cfg['label']} Daerah Mengikut Negeri, 2024"
)
ax.set_xlabel(cfg["label"])
ax.set_ylabel("Negeri")
ax.grid(axis="x", alpha=0.3)
ax.set_axisbelow(True)

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.caption(
    "Setiap titik mewakili satu daerah. Garis dalam kotak "
    "menunjukkan median nilai daerah, manakala kotak merangkumi "
    "50% nilai tengah. Whisker menggunakan had 1.5 kali julat "
    "antara kuartil (IQR); titik di luar whisker ialah nilai "
    "luar biasa mengikut kaedah ini, bukan semestinya ralat data. "
    "Bagi negeri yang hanya mempunyai satu rekod, kotak "
    "tidak dapat menunjukkan variasi."
)

st.caption(
    "Median dalam box plot dikira daripada nilai daerah "
    "tanpa pemberat. Ia bukan ukuran agregat rasmi negeri. "
    "Box plot menggunakan semua daerah dalam skop pilihan; "
    "pilihan tertinggi/terendah dan slider hanya mempengaruhi "
    "carta bar."
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
    "Histogram menunjukkan bilangan daerah dalam setiap julat "
    "nilai bagi skop pilihan. Box plot menunjukkan median, "
    "variasi dan nilai luar biasa dalam kalangan daerah "
    "mengikut negeri. Ketiga-tiga graf menyokong perbandingan "
    "dan analisis taburan, tetapi tidak membuktikan sebab "
    "perbezaan antara daerah."
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
