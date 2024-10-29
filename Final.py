# import section
from datetime import date
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# options to select scale of time
TimeSelection ={
    "Daily": "d",
    "Weekly": "W",
    "2 weeks": "2W",
    "Monthly": "M",
    "3 months": "3M",
    "6 months": "6M",
}
# Loading the files and data to dataframes
sahko = "https://github.com/Heikki1980/Final_project/blob/main/Electricity_20-09-2024.csv"
hinta = "https://github.com/Heikki1980/Final_project/blob/main/sahkon-hinta-010121-240924.csv"


#file_path = os.getcwd() + "/data/Electricity_20-09-2024.csv"
#file_path2 = os.getcwd() + "/data/sahkon-hinta-010121-240924.csv"
df_elec = pd.read_csv(hinta, sep=";", decimal=",")
df_hinta = pd.read_csv(sahko, sep=",")

# Modifying data and merging dataframes
df_hinta.replace("/", "-")
df_hinta["Time"] = pd.to_datetime(df_hinta["Time"], format="%d-%m-%Y %H:%M:%S")
df_elec["Time"] = pd.to_datetime(df_elec["Time"], format=" %d.%m.%Y %H:%M")
df = pd.merge(df_elec, df_hinta,  on="Time", how="inner")

# Counting Bill
df["Bill"] = [0] * len(df)
df["Bill"] = df["Energy (kWh)"] * df["Price (cent/kWh)"]

# Selection box for time period and default is 1 week
default_W = 1
option = st.selectbox("Choose averaging period:", options=list(TimeSelection.keys()), index=default_W)
st.write("Averaging over:", option)
freq = TimeSelection[option]

# Counting required values
df_daily_consumption = (df.groupby(pd.Grouper(key="Time", freq=freq))[["Time", "Energy (kWh)"]].sum(numeric_only=True)).reset_index()
df_daily_bill = (df.groupby(pd.Grouper(key="Time", freq=freq, closed="right"))[["Time", "Bill"]].sum(numeric_only=True)/100).reset_index()
df_daily_avg_price = (df.groupby(pd.Grouper(key="Time", freq=freq, closed="right"))[["Time", "Price (cent/kWh)"]].mean(numeric_only=True/24)).reset_index()
df_daily_avg_temp = (df.groupby(pd.Grouper(key="Time", freq=freq, closed="right"))[["Time", "Temperature"]].mean(numeric_only=True)).reset_index()

# Merging dataframes and counting average paid price
df_visu = pd.merge(df_daily_bill, df_daily_consumption, on="Time", how="left")
df_visu = pd.merge(df_visu, df_daily_avg_price,  on="Time", how="left")
df_visu = pd.merge(df_visu, df_daily_avg_temp,  on="Time", how="left")
df_visu["avg_paid_price"] = (df_visu["Bill"]*100)/df_visu["Energy (kWh)"]

# Setting default date
default_start_date = date(2022, 1, 1)
default_end_date = date(2024, 6, 1)
start_date = st.date_input(label="Select start date", value=default_start_date, key="start_date_input", format="YYYY/MM/DD")
end_date = st.date_input(label="Select end date", value=default_end_date, key="end_date_input", format="YYYY/MM/DD")
filtered_df = df_visu[(df_visu["Time"] >= pd.to_datetime(start_date)) & (df_visu["Time"] <= pd.to_datetime(end_date))]

# Counting more values
total_consumption = filtered_df["Energy (kWh)"].sum()
sum_of_bill_price = filtered_df["Bill"].sum()
average_price = filtered_df["Price (cent/kWh)"].mean()
average_paid_price = filtered_df["avg_paid_price"].mean()

# Printing wanted values
st.write("Showing range:", start_date, " - ", end_date)
st.markdown(f"Total consumption over the period: <span style='color: green;'> {total_consumption:.2f} </span> kWh", unsafe_allow_html=True)
st.markdown(f"Total bill over the period: <span style='color: green;'> {sum_of_bill_price:.2f} </span> €", unsafe_allow_html=True)
st.markdown(f"Average hourly price: <span style='color: green;'> {average_price:.2f} </span> cents", unsafe_allow_html=True)
st.markdown(f"Average paid price: <span style='color: green;'> {average_paid_price:.2f} </span> cents", unsafe_allow_html=True)


if 'graph' not in st.session_state:
    st.session_state.graph = 0

# Checkbox to toggle graph version
toggle = st.checkbox("Switch to Beta version of graphs", value=st.session_state.graph == 1)
st.session_state.graph = 1 if toggle else 0



if st.session_state.graph == 0:
    fig, ax = plt.subplots()
    # Set the threshold for Energy consumption (kWh)
    if freq == "d":
        threshold_energy = 100
    elif freq == "W":
        threshold_energy = 200
    elif freq == "2W":
        threshold_energy = 300
    elif freq == "M":
        threshold_energy = 1000
    elif freq == "3M":
        threshold_energy = 3000
    elif freq == "6M":
        threshold_energy = 6000

    # Resample based on the selected time scale (daily, weekly, monthly, etc.)
    # This helped to make the figure properly filled with color.
    # Didn't do this to rest of the figures because I am no 100 % sure, how much this affects the result.
    # Figure shape looks like it should but I didn't have time to compare the data.
    filtered_df_resampled = filtered_df.set_index("Time").resample(freq).mean().reset_index()

    # Plot all points first with a base color (optional, already included by default in fill_between)
    ax.plot(filtered_df_resampled["Time"], filtered_df_resampled["Energy (kWh)"], color="gray", label="Energy (kWh)")

    # Fill the entire area from 0 to the energy value with green (low energy consumption)
    ax.fill_between(
        filtered_df_resampled["Time"],
        0,
        filtered_df_resampled["Energy (kWh)"],
        color="green",
        alpha=0.6,
        interpolate=True,
        label=f"Energy <= {threshold_energy} kWh"
    )

    # Overlay the red area only where the energy consumption exceeds the threshold
    ax.fill_between(
        filtered_df_resampled["Time"],
        threshold_energy,
        filtered_df_resampled["Energy (kWh)"],
        where=filtered_df_resampled["Energy (kWh)"] > threshold_energy,
        color="red",
        alpha=0.6,
        interpolate=True,
        label=f"Energy > {threshold_energy} kWh"
    )

    ax.grid(True, which="both", axis="y", linestyle="--", color="gray")
    ax.set_ylabel("Electricity consumption [kWh]")
    ax.set_xlabel("Time")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_xlim([filtered_df_resampled['Time'].min(), filtered_df_resampled["Time"].max()])
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.legend()
    st.pyplot(fig)


    fig, ax = plt.subplots()
    # Set the threshold for Price (cent/kWh)
    threshold_price = 30
    # Plot all prices first with a neutral color
    ax.plot(filtered_df["Time"], filtered_df["Price (cent/kWh)"], color="gray", label="Electricity price (cent/kWh)")
    # Fill the area below the red section (Price > threshold_price) with green
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Price (cent/kWh)"],
        0,  # Lower bound for the fill (from zero up to the price)
        where=filtered_df["Price (cent/kWh)"] > threshold_price,
        color="green",
        interpolate=True,
        alpha=0.6
    )

    # Highlight the points where the price goes above the threshold
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Price (cent/kWh)"],
        threshold_price,  # Baseline for the red fill
        where=filtered_df["Price (cent/kWh)"] > threshold_price,
        color="red",
        alpha=0.6,
        interpolate=True,
        label=f"Price > {threshold_price} cents"
    )

    # Highlight the points where the price is below the threshold
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Price (cent/kWh)"],
        0,  # Lower bound for the fill
        where=filtered_df["Price (cent/kWh)"] <= threshold_price,
        color="green",
        alpha=0.6,
        interpolate=True,
        label=f"Price <= {threshold_price} cents"
    )

    ax.grid(True, which="both", axis="y", linestyle="--", color="gray")
    ax.set_ylabel("Electricity price [cents]")
    ax.set_xlabel("Time")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_xlim([filtered_df["Time"].min(), filtered_df["Time"].max()])
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.legend()
    st.pyplot(fig)



    fig, ax = plt.subplots()
    threshold_bill = 100
    # Plot the bill amounts with a neutral color
    ax.plot(filtered_df["Time"], filtered_df["Bill"], color="gray", label="Electricity bill (€)")
    # Fill the area below red section (Bill > threshold_bill) with green
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Bill"],
        0,  # Fill from zero
        where=filtered_df["Bill"] > threshold_bill,
        color="green",
        interpolate=True,
        alpha=0.6
    )

    # Highlight high bills
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Bill"],
        threshold_bill,  # Baseline for red fill
        where=filtered_df["Bill"] > threshold_bill,
        color="red",
        alpha=0.6,
        interpolate=True,
        label=f"Bill > {threshold_bill}€"
    )

    # Highlight low bills
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Bill"],
        0,  # Fill from zero
        where=filtered_df["Bill"] <= threshold_bill,
        color="green",
        alpha=0.6,
        interpolate=True,
        label=f"Bill <= {threshold_bill}€"
    )

    ax.grid(True, which="both", axis="y", linestyle="--", color="gray")
    ax.set_ylabel("Electricity bill (€)")
    ax.set_xlabel("Time")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_xlim([filtered_df["Time"].min(), filtered_df["Time"].max()])
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.legend()
    st.pyplot(fig)


    fig, ax = plt.subplots()
    # Set temperature thresholds
    threshold_temp_high = 10
    threshold_temp_low = -10
    # Plot the temperature with a neutral color
    ax.plot(filtered_df["Time"], filtered_df["Temperature"], color="gray", label="Temperature")
    # Fill the area below the red section (Temperature > threshold_temp_high) with green
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Temperature"],
        threshold_temp_low,
        where=filtered_df["Temperature"] > threshold_temp_high,
        color="green",
        interpolate=True,
        alpha=0.6
    )

    # Highlight warm temperatures
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Temperature"],
        threshold_temp_high,
        where=filtered_df["Temperature"] > threshold_temp_high,
        color="red",
        alpha=0.6,
        interpolate=True,
        label=f"Temperature > {threshold_temp_high}°C"
    )

    # Highlight decent weather temperatures
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Temperature"],
        threshold_temp_low,  # Fill from lower threshold
        where=(filtered_df["Temperature"] <= threshold_temp_high) & (filtered_df["Temperature"] > threshold_temp_low),
        color="green",
        alpha=0.6,
        interpolate=True,
        label=f"Temperature between {threshold_temp_low}°C and {threshold_temp_high}°C"
    )

    # Highlight  cold temperatures
    ax.fill_between(
        filtered_df["Time"],
        filtered_df["Temperature"],
        threshold_temp_low,  # Fill from lower threshold
        where=filtered_df["Temperature"] <= threshold_temp_low,
        color="blue",
        alpha=0.6,
        interpolate=True,
        label=f"Temperature < {threshold_temp_low}°C"
    )

    ax.grid(True, which="both", axis="y", linestyle="--", color="gray")
    ax.set_ylabel("Temperature [°C]")
    ax.set_xlabel("Time")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_xlim([filtered_df["Time"].min(), filtered_df["Time"].max()])
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)

else:  # This is the default version of the graphs.
    fig, ax = plt.subplots()
    ax.plot(filtered_df["Time"], filtered_df["Energy (kWh)"], label="Energy (kWh)")
    ax.set_ylabel("Electricity consumption [kWh]")
    ax.set_xlabel("Time")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_xlim([filtered_df["Time"].min(), filtered_df["Time"].max()])
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)

    fig, ax = plt.subplots()
    ax.plot(filtered_df["Time"], filtered_df["Price (cent/kWh)"], label="Electricity price (cent/kWh)")
    ax.set_ylabel("Electricity price [cents]")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_xlim([filtered_df["Time"].min(), filtered_df["Time"].max()])
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

    fig, ax = plt.subplots()
    ax.plot(filtered_df["Time"], filtered_df["Bill"], label="Bill")
    ax.set_ylabel("Electricity bill")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_xlabel("Time")
    ax.set_xlim([filtered_df["Time"].min(), filtered_df["Time"].max()])
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

    fig, ax = plt.subplots()
    ax.plot(filtered_df["Time"], filtered_df["Temperature"], label="Temperature")
    ax.set_ylabel("Temperature (\N{DEGREE SIGN}C)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_xlim([filtered_df["Time"].min(), filtered_df["Time"].max()])
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)
