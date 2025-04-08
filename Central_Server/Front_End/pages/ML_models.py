import os

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from plotly.subplots import make_subplots
from statsmodels.tsa.stattools import acf
from scipy import stats

db_name = 'plant_data.db'
def get_db_path(db_name):
    # get current path
    current_dir = os.path.dirname(__file__)

    # go up two dirs
    grandparent_dir = os.path.dirname(os.path.dirname(current_dir))

    #construct path
    dp_path = os.path.join(grandparent_dir, db_name)
    return dp_path

db_path = get_db_path(db_name)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
df = pd.read_sql_query("SELECT * FROM sensor_data", conn)
# Convert to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S.%f')
# Remove microseconds by truncating to seconds
df['timestamp'] = df['timestamp'].dt.floor('s')
st.title('Models & Machine Learning Service')

st.success(f"Recent watering event Moisture before: | 00 Moisture After: 10 | watering duration: 15 seconds. Please provide feedback below")
st.warning("Model is recommending irrigation. Confirm or adjust action")

with st.form("Model Feedback"):
    st.write("Please provide feebdack for predictions made ")
    user_set_water = st.selectbox(
        "Which plant?", ("Plant1", "Camomile", "BogGarden"),
    )
    st.toggle("Approve irrigation")
    st.toggle("Enable Auto approval")

    st.slider("watering duration", min_value=15, max_value=60, step=5)

    st.select_slider("Current Plant Health", options=("Healthy", "Dry", "Over watered", "More Sunlight", "Less Sunlight"))
    st.text_area("Notes")

    submitted = st.form_submit_button("Submit")
    if submitted:
        st.success("Model Feedback submitted")

col1, col2 = st.columns(2)
with col1:
    st.header("Concept Drift")
    # fig = create_rounded_chart(df, 'timestamp', 'moisture', "Moisture Levels")
    # st.plotly_chart(fig, use_container_width=True)
# Helper function for correlation matrix

def get_corr_matrix(df):
    corr = df[['moisture', 'temperature', 'humidity', 'light_level']].corr()
    return corr

with col2:
    corr_matrix = get_corr_matrix(df)

    st.header("Correlation Matrix")
    # fig = create_rounded_chart(corr_matrix, df['timestamp'], 'temperature', 'Temperature (°C)')
    fig = go.Figure(data=go.Heatmap(z=corr_matrix.values,
                                    x=corr_matrix.columns,
                                    y=corr_matrix.index,
                                    text= corr_matrix.values,
                                    texttemplate='%{text}', # Display text
                                    showscale=True, # Show Scale
                                    colorscale= 'tealgrn'
                                    ))
    fig.update_layout(title="Correlation Matrix",
                      width=800,
                      height=400,
                      xaxis_showgrid=False,
                      yaxis_showgrid=False,
                      yaxis_autorange= 'reversed')

    st.plotly_chart(fig, use_container_width=True, key="corr_matrix")
# Functions to create graphs
def create_qq_plot(df, sensor_column, plant_id=None):
    """
    Create a QQ Plot for a specific column in df
    :param df: - pd dataframe
    :param sensor_column: Column name of sensor
    :param plant_id: specific plant/arduino node
    :return: fig
    """
    # filter if plant_id is specificied.
    if plant_id:
        data = df[df['plant_id'] == plant_id][sensor_column].dropna()
    else:
        data = df[sensor_column].dropna()
    #Calculate Quantiles
    column_quantiles = np.linspace(0.01, 0.99, len(data))

    #sort the data
    sorted_data = np.sort(data)

    theoretical_values = stats.norm.ppf(column_quantiles, loc=np.mean(data), scale=np.std(data))
    #Create Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x= theoretical_values,
        y= sorted_data,
        mode='markers',
        name=sensor_column,
        marker=dict(color='blue', size=8)
    ))

    # Add diagnol line representing perfect normal distribution
    min_val= min(np.min(theoretical_values), np.min(sorted_data))
    max_val= max(np.max(theoretical_values), np.max(sorted_data))
    fig.add_trace(go.Scatter(
        x= [min_val, max_val],
        y= [min_val, max_val],
        mode='lines',
        name='Normal Distribution',
        line=dict(color='red', dash='dash')
    ))

    #Update layout
    title = f"Q-Q Plot for {sensor_column}"

    if plant_id:
        title = f" Plant ID: {plant_id}"

    fig.update_layout(
        height=400,
        width=1000,
        title=title,
        xaxis_title='Theoretical Quantiles',
        yaxis_title='Sample Quantiles',
        legend_title="Legend",
        template='plotly_dark'
    )
    return fig
# function to create seasonality plot
def create_seasonality_plot(df, sensor_column, max_lags=60, plant_id=None):
    """
    Create seasonality check plots using autocorrelation.

    Parameters:
    - df: Pandas DataFrame containing the sensor data
    - sensor_column: Column name of the sensor (e.g., 'temperature', 'humidity')
    - max_lags: Maximum number of lags to calculate for ACF
    - plant_id: Optional filter for specific plant_id

    Returns:
    - Plotly figure object with ACF and daily/weekly heatmaps
    """
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Filter data if plant_id is specified
    if plant_id:
        data = df[df['plant_id'] == plant_id].copy()
    else:
        data = df.copy()

    # Extract time components
    data['hour'] = data['timestamp'].dt.hour
    data['day_of_week'] = data['timestamp'].dt.dayofweek  # 0 = Monday, 6 = Sunday

    # Create figure with subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Autocorrelation Function", "Hourly Pattern",
                        "Day of Week Pattern", "Hour-Day Heatmap"),
        specs=[[{"type": "xy"}, {"type": "xy"}],
               [{"type": "xy"}, {"type": "xy"}]]
    )

    # 1. Autocorrelation plot
    # Resample to hourly data to handle irregular timestamps
    hourly_data = data.set_index('timestamp')[sensor_column].resample('H').mean().dropna()

    # Calculate ACF
    acf_values = acf(hourly_data, nlags=max_lags)
    confidence_interval = 1.96 / np.sqrt(len(hourly_data))

    # Add ACF plot
    fig.add_trace(
        go.Scatter(x=list(range(len(acf_values))), y=acf_values,
                   mode='lines+markers', name='ACF',
                   line=dict(color='blue')),
        row=1, col=1
    )

    # Add confidence intervals
    fig.add_trace(
        go.Scatter(x=list(range(len(acf_values))), y=[confidence_interval] * len(acf_values),
                   mode='lines', name='95% Confidence',
                   line=dict(color='red', dash='dash')),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=list(range(len(acf_values))), y=[-confidence_interval] * len(acf_values),
                   mode='lines', showlegend=False,
                   line=dict(color='red', dash='dash')),
        row=1, col=1
    )

    # 2. Hourly pattern - average by hour of day
    hourly_avg = data.groupby('hour')[sensor_column].mean().reset_index()

    fig.add_trace(
        go.Bar(x=hourly_avg['hour'], y=hourly_avg[sensor_column],
               name='Hourly Average',
               marker_color='teal'),
        row=1, col=2
    )

    # 3. Day of week pattern - average by day of week
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dow_avg = data.groupby('day_of_week')[sensor_column].mean().reset_index()

    fig.add_trace(
        go.Bar(x=[day_names[i] for i in dow_avg['day_of_week']],
               y=dow_avg[sensor_column],
               name='Day of Week Average',
               marker_color='orange'),
        row=2, col=1
    )

    # 4. Hour-Day heatmap
    hour_day_pivot = data.pivot_table(
        index='hour',
        columns='day_of_week',
        values=sensor_column,
        aggfunc='mean'
    )

    fig.add_trace(
        go.Heatmap(
            z=hour_day_pivot.values,
            x=[day_names[i] for i in range(7)],
            y=list(range(24)),
            colorscale='Viridis',
            name='Hour-Day Heatmap'
        ),
        row=2, col=2
    )

    # Update layout
    title = f"Seasonality Analysis for {sensor_column}"
    if plant_id:
        title += f" (Plant ID: {plant_id})"

    fig.update_layout(
        title=title,
        height=800,
        template="plotly_white"
    )

    fig.update_xaxes(title_text="Lag", row=1, col=1)
    fig.update_yaxes(title_text="Correlation", row=1, col=1)

    fig.update_xaxes(title_text="Hour of Day", row=1, col=2)
    fig.update_yaxes(title_text=f"Average {sensor_column}", row=1, col=2)

    fig.update_xaxes(title_text="Day of Week", row=2, col=1)
    fig.update_yaxes(title_text=f"Average {sensor_column}", row=2, col=1)

    fig.update_xaxes(title_text="Day of Week", row=2, col=2)
    fig.update_yaxes(title_text="Hour of Day", row=2, col=2)

    return fig


def create_concept_drift_plot(df, sensor_column, window_size=14, plant_id=None):
    """
    Create temporal stability plot to detect concept drift in sensor data.

    Parameters:
    - df: Pandas DataFrame containing the sensor data
    - sensor_column: Column name of the sensor (e.g., 'temperature', 'humidity')
    - window_size: Size of the rolling window (in days)
    - plant_id: Optional filter for specific plant_id

    Returns:
    - Plotly figure object
    """
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Filter data if plant_id is specified
    if plant_id:
        data = df[df['plant_id'] == plant_id].copy()
    else:
        data = df.copy()

    # Sort by timestamp
    data = data.sort_values('timestamp')

    # Set timestamp as index for resampling
    data.set_index('timestamp', inplace=True)

    # Resample to daily mean
    daily_data = data[sensor_column].resample('D').mean()

    # Calculate rolling statistics
    rolling_mean = daily_data.rolling(window=window_size).mean()
    rolling_std = daily_data.rolling(window=window_size).std()

    # Calculate upper and lower bounds (2 standard deviations)
    upper_bound = rolling_mean + 2 * rolling_std
    lower_bound = rolling_mean - 2 * rolling_std

    # Reset index for plotting
    daily_data = daily_data.reset_index()
    rolling_mean = rolling_mean.reset_index()
    upper_bound = upper_bound.reset_index()
    lower_bound = lower_bound.reset_index()

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(x=daily_data['timestamp'], y=daily_data[sensor_column],
                   mode='markers', name='Daily Mean',
                   marker=dict(color='blue', size=5)),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=rolling_mean['timestamp'], y=rolling_mean[sensor_column],
                   mode='lines', name=f'{window_size}-Day Moving Average',
                   line=dict(color='red', width=2)),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=upper_bound['timestamp'], y=upper_bound[sensor_column],
                   mode='lines', name='Upper Bound (2σ)',
                   line=dict(color='green', width=1, dash='dash')),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=lower_bound['timestamp'], y=lower_bound[sensor_column],
                   mode='lines', name='Lower Bound (2σ)',
                   line=dict(color='green', width=1, dash='dash')),
        secondary_y=False,
    )

    # Add rolling standard deviation on secondary axis
    fig.add_trace(
        go.Scatter(x=rolling_std.reset_index()['timestamp'],
                   y=rolling_std.reset_index()[sensor_column],
                   mode='lines', name=f'{window_size}-Day Rolling Std',
                   line=dict(color='purple', width=1)),
        secondary_y=True,
    )

    # Set titles
    title = f"Temporal Stability for {sensor_column}"
    if plant_id:
        title += f" (Plant ID: {plant_id})"

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        template="plotly_white"
    )

    fig.update_yaxes(title_text=f"{sensor_column} Value", secondary_y=False)
    fig.update_yaxes(title_text="Standard Deviation", secondary_y=True)

    return fig

col3, col4 = st.columns(2)
with col3:
    st.header("Q-Q Moisture")
    qq_fig = create_qq_plot(df, sensor_column='moisture')
    st.plotly_chart(qq_fig, use_container_width=False, key="qq_moisture")

with col4:
    st.header("Q-Q Temperature")
    qq_fig = create_qq_plot(df, sensor_column='temperature')
    st.plotly_chart(qq_fig, use_container_width=False, key="qq_temp")

# humidity and light level columns
col5, col6 = st.columns(2)
with col5:
    st.header("Q-Q Humidity")
    qq_fig = create_qq_plot(df, sensor_column='humidity')
    st.plotly_chart(qq_fig, use_container_width=False, key="qq_humidity")
with col6:
    st.header("Q-Q Light")
    qq_fig = create_qq_plot(df, sensor_column='light_level')
    st.plotly_chart(qq_fig, use_container_width=False, key="qq_light")
# Concept Drift
col7, col8 = st.columns(2)
with col7:
    st.header("Drift Moisture")
    drift_fig = create_concept_drift_plot(df, sensor_column='moisture')
    st.plotly_chart(drift_fig, use_container_width=False, key="drift_moisture")
with col8:
    st.header("Drift Temperature")
    drift_fig = create_concept_drift_plot(df, sensor_column='temperature')
    st.plotly_chart(drift_fig, use_container_width=False, key="drift_temp")
col9, col10 = st.columns(2)
with col9:
    st.header("Drift Humidity")
    drift_fig = create_concept_drift_plot(df, sensor_column='humidity')
    st.plotly_chart(drift_fig, use_container_width=False, key="drift_humidity")
with col10:
    st.header("Drift Light")
    drift_fig = create_concept_drift_plot(df, sensor_column='light_level')
    st.plotly_chart(drift_fig, use_container_width=False, key="drift_light")


conn.close()