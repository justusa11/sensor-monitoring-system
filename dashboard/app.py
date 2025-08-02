####################################################
# Import necessary libraries
####################################################
import streamlit as st
import pandas as pd
import requests
import plotly.express as px # type: ignore
from sklearn.ensemble import IsolationForest

st.set_page_config(layout="wide", page_title="Sensor Dashboard")

# Define API URL
API_URL = "http://backend:8000/sensor"
st.title("Sensor Dashboard")



####################################################
# Get data from FastAPI
####################################################
try:
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        if len(data) > 0:
            df: pd.DataFrame = pd.DataFrame(data)
            #st.write("First 5 rows of data:", df.head())  # Debug: Show data
            ####################################################
            # Summary Statistics
            ####################################################
            if not df.empty:
                st.subheader("📊 System Summary Statistics")

                total_sensors = df['sensor_id'].nunique()
                total_records = len(df)
                avg_temp_in = df['temp_in'].mean()
                avg_temp_out = df['temp_out'].mean()
                avg_flow = df['flow_rate'].mean()
                last_timestamp = df['timestamp'].max()

                col1, col2, col3 = st.columns(3)
                col1.metric("Total Sensors", total_sensors)
                col2.metric("Total Records", total_records)
                col3.metric("Last Timestamp", last_timestamp)

                col4, col5, col6 = st.columns(3)
                col4.metric("Avg. Temp In (°C)", f"{avg_temp_in:.2f}")
                col5.metric("Avg. Temp Out (°C)", f"{avg_temp_out:.2f}")
                col6.metric("Avg. Flow Rate", f"{avg_flow:.2f}")

            # Check for required columns
            required_cols = {"timestamp", "sensor_id", "temp_in", "temp_out", "flow_rate"}
            if not required_cols.issubset(df.columns):
                st.error(f"Missing columns in data: {required_cols - set(df.columns)}")
            else:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                df = df.dropna(subset=["timestamp"])
                df = df.sort_values("timestamp")

                # Unique sensors IDs
                sensor_ids = df["sensor_id"].unique().tolist()
                selected_sensor = st.selectbox("Select Sensor ID", options=sensor_ids)

                # Filter data for selected sensor
                df = df[df["sensor_id"] == selected_sensor]

                # Time range filter
                start_ts = df["timestamp"].min()
                end_ts = df["timestamp"].max()

                if pd.isnull(start_ts) or pd.isnull(end_ts):
                    st.warning("No valid timestamps for this sensor.")
                else:
                    time_range = st.slider(
                        "Select Time Range",
                        min_value=start_ts.to_pydatetime(),
                        max_value=end_ts.to_pydatetime(),
                        value=(start_ts.to_pydatetime(), end_ts.to_pydatetime()),
                        format="YYYY-MM-DD HH:mm:ss"
                    )

                    # Unpack start and end times
                    start_time, end_time = time_range
                    
                    # Filter the Dataframe
                    df = df[(df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)]

                    # Layout for display
                    st.markdown(
                        f"**Duration:** `{end_time - start_time}`")
                    
                    st.subheader("Raw Sensor Data")
                    #st.dataframe(df.tail(10))

                    #######################################
                    # Isolation Forest Anomaly Detection
                    #######################################
                    st.subheader("ML-based Anomaly Detection (Isolation Forest)")

                    # Prepare features
                    features = df[["temp_in", "temp_out", "flow_rate"]].copy()
                    features = features.dropna()

                    # Fit Isolation forest model
                    iso_model = IsolationForest(contamination=0.05, random_state=42)
                    df["anomaly_ml"] = -1 # Default: not an anomaly
                    if not features.empty:
                        df.loc[features.index, "anomaly_ml"] = iso_model.fit_predict(features)

                    # Highlight anomalies (ML-based)
                    ml_anomalies = df[df["anomaly_ml"] == -1]

                    st.write(f"Anomalies Detected by Model: {len(ml_anomalies)}")
                    if not ml_anomalies.empty:
                        st.dataframe(ml_anomalies.tail(5))

                    #######################################
                    # Plot: Temperature In and Out + Anoms
                    #######################################
                    # Line plot: Temperature In and Out
                    fig_temp = px.line(
                        df, x="timestamp", y=["temp_in", "temp_out"],
                        title="Temperature In and Out Over Time",
                        color_discrete_sequence=["red", "blue"]
                    )

                    if not ml_anomalies.empty:
                        fig_temp.add_scatter(
                            x=ml_anomalies["timestamp"],
                            y=ml_anomalies["temp_out"],
                            mode="markers",
                            name="ML Anomalies (Temp out)",
                            marker=dict(color="black", size=8, symbol="x"))
                        
                        fig_temp.add_scatter(
                            x=ml_anomalies["timestamp"],
                            y=ml_anomalies["temp_in"],
                            mode="markers",
                            name="ML Anomalies (Temp In)",
                            marker=dict(color="orange", size=10, symbol="x"))
                        
                    st.plotly_chart(fig_temp, use_container_width=True)

                    #######################################
                    # Plot: Flow Rate
                    #######################################
                    # Line plot: Flow Rate
                    fig_flow = px.line(
                        df, x="timestamp", y="flow_rate",
                        title="Flow Rate Over Time"
                    )

                    st.plotly_chart(fig_flow, use_container_width=True)

                    #######################################
                    # Rule-based anomalies
                    #######################################
                    st.subheader("Rule-Based Anomaly Detection")

                    cooling_penalty = df[df["temp_out"] > 45]
                    zero_flow_issue = df[(df["flow_rate"] == 0) & (df["temp_in"] < 40)]

                    st.write(f"Cooling Penalty (Tout >45°C): {len(cooling_penalty)} records")
                    st.write(f"Zero flow with low Tin (< 40°C): {len(zero_flow_issue)} records")

                    if not cooling_penalty.empty:
                        st.dataframe(cooling_penalty.tail(5))

                    if not zero_flow_issue.empty:
                        st.dataframe(zero_flow_issue.tail(5))

                    #######################################
                    # Sensor Health Status (Last Seen)
                    #######################################
                    st.subheader("Sensor Health Status (Last Seen)")

                    try:
                        status_response = requests.get("http://backend:8000/sensor/status")
                        if status_response.status_code == 200:
                            offline_data = status_response.json()["offline_sensors"]
                            if offline_data:
                                st.error(f"{len(offline_data)} sensor(s) offline!")
                                st.dataframe(offline_data)
                            else:
                                st.success("All sensor are online")
                        else:
                            st.warning("Could not fetch sensor status")
                    except Exception as e:
                        st.error(f"Error checking sensor status: {e}")
                                       
        else:
            st.warning("No sensor data available.") # Triggers when API responds with 200 ok
    else:
        st.error(f"Failed to fetch data. Status code: {response.status_code}") # Handles errors like 404. 500. 403
except Exception as e:
    st.error(f"Error connecting to API: {e}") # Catches connection or runtime errors- Network down or FastAPI not running
