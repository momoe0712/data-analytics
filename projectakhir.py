import calendar

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")

BASE_COLOR = "#4C78A8"
PEAK_COLOR = "#E45756"
SECOND_COLOR = "#F58518"


def show(fig):
    """Tampilkan figure Matplotlib selebar kontainer, sehingga ikut membesar/mengecil
    saat browser di-zoom atau ukuran jendela berubah."""
    try:
        st.pyplot(fig, width="stretch")  # Streamlit versi baru
    except TypeError:
        st.pyplot(fig, use_container_width=True)  # Streamlit versi lama
    plt.close(fig)


@st.cache_data
def load_data():
    base = "https://raw.githubusercontent.com/felixb177/analisisdata/main/data/"
    day = pd.read_csv(base + "day.csv", parse_dates=["dteday"])
    hour = pd.read_csv(base + "hour.csv", parse_dates=["dteday"])
    return day, hour


def hourly_bar(series, title, highlights):
    colors = [highlights.get(h, BASE_COLOR) for h in series.index]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.bar(series.index, series.values, color=colors)
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)], fontsize=8)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Average rentals per hour")
    ax.set_title(title)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    for h in highlights:
        ax.annotate(
            f"{h:02d}:00\n{series[h]:.0f}",
            xy=(h, series[h]),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            fontweight="bold",
        )
    ax.set_ylim(0, series.max() * 1.18)
    fig.tight_layout()
    return fig


day_df, hour_df = load_data()

st.title("Bike Sharing Dashboard")
st.caption("Rental patterns in 2011–2012, based on the Bike Sharing Dataset (day.csv and hour.csv).")

st.header("1. At what hour are bike rentals at their highest?")

hourly = hour_df.groupby(["workingday", "hr"])["cnt"].mean()
wd = hourly.loc[1]
nwd = hourly.loc[0]

wd_peak = wd.idxmax()
wd_morning = wd[wd.index < 12].idxmax()
nwd_peak = nwd.idxmax()

col1, col2 = st.columns(2)
with col1:
    fig = hourly_bar(
        wd,
        "Working Days: Average Rentals per Hour",
        {wd_peak: PEAK_COLOR, wd_morning: SECOND_COLOR},
    )
    show(fig)
with col2:
    fig = hourly_bar(
        nwd,
        "Non-working Days: Average Rentals per Hour",
        {nwd_peak: PEAK_COLOR},
    )
    show(fig)

st.caption("Red bar = highest hour; orange bar = morning peak on working days. "
           "Each chart has its own vertical scale.")
st.info(
    f"On working days, rentals peak at {wd_peak:02d}:00, with a second peak at "
    f"{wd_morning:02d}:00. On non-working days, rentals peak at {nwd_peak:02d}:00."
)

st.header("2. Which season has the highest average daily bike rentals?")

season_map = {1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"}
season_avg = day_df.groupby("season")["cnt"].mean().reset_index()
season_avg["season"] = season_avg["season"].map(season_map)
season_avg["change"] = season_avg["cnt"].pct_change() * 100

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
sns.barplot(data=season_avg, x="season", y="cnt", ax=ax)
ax.set_xlabel("Season")
ax.set_ylabel("Average rentals per day")
ax.set_title("Average Daily Bike Rentals by Season")
ax.grid(True, axis="y", linestyle="--", alpha=0.5)
fig.tight_layout()
show(fig)

best = season_avg.loc[season_avg["cnt"].idxmax()]
jump_idx = season_avg["change"].idxmax()
jump = season_avg.loc[jump_idx]
prev = season_avg.loc[jump_idx - 1, "season"]
st.info(
    f"{best['season']} has the highest average daily rentals ({best['cnt']:,.0f} bikes/day). "
    f"The largest increase is from {prev} to {jump['season']} (+{jump['change']:.0f}%)."
)

st.header("3. How much did rentals grow from 2011 to 2012, and when and for whom was growth highest?")

yearly = day_df.groupby("yr")["cnt"].sum()
total_growth = (yearly[1] / yearly[0] - 1) * 100

m1, m2 = st.columns(2)
m1.metric("Total rentals 2011", f"{yearly[0]:,}")
m2.metric("Total rentals 2012", f"{yearly[1]:,}", f"{total_growth:.1f}%")

monthly = day_df.pivot_table(index="mnth", columns="yr", values="cnt", aggfunc="sum")
monthly.columns = ["2011", "2012"]
monthly["yoy"] = (monthly["2012"] / monthly["2011"] - 1) * 100
monthly.index = [calendar.month_abbr[m] for m in monthly.index]

c1, c2 = st.columns(2)
with c1:
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.plot(monthly.index, monthly["2011"], marker="o", label="2011")
    ax.plot(monthly.index, monthly["2012"], marker="o", label="2012")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total rentals")
    ax.set_title("Monthly Bike Rentals: 2011 vs 2012")
    ax.legend(title="Year")
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    show(fig)
with c2:
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    sns.barplot(x=monthly.index, y=monthly["yoy"], ax=ax)
    ax.set_xlabel("Month")
    ax.set_ylabel("YoY growth (%)")
    ax.set_title("Year-over-Year Growth by Month")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    fig.tight_layout()
    show(fig)

seg = day_df.groupby("yr")[["casual", "registered"]].sum()
seg_growth = (seg.loc[1] / seg.loc[0] - 1) * 100
top_m, low_m = monthly["yoy"].idxmax(), monthly["yoy"].idxmin()
st.info(
    f"Total rentals grew by {total_growth:.1f}%. Growth was highest in {top_m} "
    f"(+{monthly['yoy'].max():.1f}%) and lowest in {low_m} (+{monthly['yoy'].min():.1f}%). "
    f"Registered users grew by {seg_growth['registered']:.1f}% and casual users by "
    f"{seg_growth['casual']:.1f}%. Growth in early 2012 is inflated by the low 2011 base."
)