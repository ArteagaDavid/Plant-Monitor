import os

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3

# Connect to database
db_name = 'plant_data.db'
def get_db_path(db_name):
    # get current path
    current_dir = os.path.dirname(__file__)

    # go up one dir
    parent_dir = os.path.dirname(current_dir)
    #construct path
    dp_path = os.path.join(parent_dir, db_name)
    return dp_path

db_path = get_db_path(db_name)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
df = pd.read_sql_query("SELECT * FROM sensor_data", conn)
# Convert to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S.%f')
# Remove microseconds by truncating to seconds
df['timestamp'] = df['timestamp'].dt.floor('s')

# Page and title
st.set_page_config(
    page_title="Smart Garden Analytics",
    page_icon="plant",
    layout="wide"
)

# Apply custom theme with CSS
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #00ABAB;  /* Dark Forest Green background */
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1A374D;  /* banana yellow for sidebar */
    }

    /* Buttons */
    .stButton > button {
        background-color: #668a84;  /* Changed to teal-gray to match theme */
        color: white;
        border: none;
        border-radius: 10px;  /* Rounded button corners */
    }

    /* Slider */
    .stSlider > div > div > div {
        background-color: #668a84;  /* Changed to teal-gray */
    }

    /* Text inputs */
    .stTextInput > div > div > input {
        border-color: #668a84;
        border-radius: 10px;  /* Rounded input corners */
    }

    /* Headers styling */
    h1, h2, h3, h4, h5, h6 {
        color: #f9cb9c !important;  /* Peach for headers */
    }

    /* Regular text color */
    p, div:not([class^="st-"]) {
        color: #f9cb9c !important;  /* Teal-gray for regular text */
    }

    /* Chart text and labels */
    .stMarkdown, .css-10trblm, .css-1x8cf1d {
        color: #668a84 !important;  /* Ensure consistent color for more text elements */
    }

    /* Make sure subheaders are visible */
    .css-10trblm, .css-1x8cf1d {
        font-weight: 600 !important;  /* Make headers more visible on dark background */
    }

    /* Plotly chart container - enhanced rounded corners */
    .stPlotlyChart {
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
        background-color: #3B6255 !important; /* Match plot background */
        padding: 5px !important;
        margin-bottom: 15px !important;
    }

    /* Style for the info box */
    .stAlert {
        border-radius: 15px !important;
    }

    /* Widget labels */
    label {
        color: #668a84 !important;
    }

    /* Fix chart alignment */
    [data-testid="column"] {
        padding: 0 5px !important;
    }

    /* Make charts same height */
    .element-container {
        margin-bottom: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# Add a title
st.title("Smart Garden Dashboard")
last_row = df.iloc[-1]
# Text
st.info(
    f"LATEST SENSOR READING: Moisture: {last_row['moisture']:.2f} | Temp: {last_row['temperature']:.1f}°C | Humidity: {last_row['humidity']:.1f}% | Light: {last_row['light_level']} | Time: {last_row['timestamp']}")

# Side Bar
with st.sidebar:
    st.header("Debug Controls")
    with st.form("plant_settings_form"):
        #plant id
        plant_id = st.number_input("Plant ID", min_value=101, max_value=999, step=1, help="Enter the plant/edge node identifier (101-999)")

        #Moisture threshold
        moisture_threshold = st.slider("Moisture Threshold (%)",
                                       min_value=0.0, max_value=100.0, value=60.0, step=5.0,
                                       help="Set moisture level below current reading to trigger irrigation")
        #Watering duration selection
        duration_options = [5, 10, 15, 20, 25, 30]
        watering_duration = st.selectbox("Watering Duration(seconds)", options=duration_options,
                                         help="Enter the duration that the pump will run for (in seconds)")
        submit_button = st.form_submit_button(label="Update Settings in db")

        if submit_button:
            try:
            # WE are using the existing database connection idk if good practice :D
                cursor.execute("""
                UPDATE plant_settings
                SET moisture_threshold = ?, watering_duration = ?
                 WHERE plant_id = ?
                 """, (moisture_threshold, watering_duration, plant_id))
                conn.commit()
                #Show success message
                st.success(f"Updated settings for Plant #{plant_id}: Moisture Threshold = {moisture_threshold}%, Watering Duration = {watering_duration}s")
            except Exception as e:
                st.error("Failed to update settings: {str(e)}")

    st.subheader("Current Plant Settings")
    try:
        #Query settings using existing connection
        settings_df = pd.read_sql_query("""
        SELECT plant_id, moisture_threshold, watering_duration
        FROM plant_settings
        ORDER BY plant_id
        """, conn)
        # display data frame
        st.dataframe(settings_df, hide_index=True)
    except Exception as e:
        st.error("Failed to load settings: {str(e)}")


# Create rounded chart function for consistent styling
def create_rounded_chart(data, x_col, y_col, title):
    fig = px.line(data, x=x_col, y=y_col)
    fig.update_layout(
        title=title,
        plot_bgcolor='#3B6255',
        paper_bgcolor='#3B6255',
        font_color='#668a84',
        margin=dict(l=10, r=10, t=30, b=10),
        height=300,  # Consistent height
    )
    fig.update_traces(line=dict(color='#D2C49E', width=2.5))

    # Add rounded corners to the plot area
    fig.update_layout(
        shapes=[
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                line=dict(width=0),
                fillcolor='rgba(0,0,0,0)',
                layer="below"
            )
        ]
    )
    return fig


# Main Content - First row
col1, col2 = st.columns(2)

with col1:
    st.header("Moisture")
    fig = create_rounded_chart(df, 'timestamp', 'moisture', "Moisture Levels")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.header("Temperature")
    fig = create_rounded_chart(df, 'timestamp', 'temperature', "Temperature (°C)")
    st.plotly_chart(fig, use_container_width=True, key= 'temp_chart')

# Second row Humidity and Moisture
col3, col4 = st.columns(2)

with col3:
    st.header("Humidity")
    fig = create_rounded_chart(df, 'timestamp', 'humidity', "Humidity (%)")
    st.plotly_chart(fig, use_container_width=True, key= 'humidity_chart')

with col4:
    st.header("Light Intensity & UV")
    light_df = df[['timestamp', 'light_level']].copy()

    #place holder for UV data
    light_df['uv_placeholder'] = light_df['light_level'] * 0.4


    #Create figure using go
    fig = go.Figure()

    #Add each Trace
    fig.add_trace(go.Scatter(
        x=light_df['timestamp'],
        y=light_df['light_level'],
        mode='lines',
        name='Light Intensity',

    ))

    fig.add_trace(go.Scatter(
        x=light_df['timestamp'],
        y=light_df['uv_placeholder'],
        mode='lines',
        name='UV',
        line=dict(color='#8A2BE2')

    ))

    fig.update_layout(
        title="Light Intensity & UV",
        plot_bgcolor='#3B6255',
        paper_bgcolor='#3B6255',
        font_color='#668a84',
        margin=dict(l=10, r=10, t=30, b=10),
        height=300,  # Consistent height
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Update line width for both traces
    fig.update_traces(line=dict(width=2.5))

    # Set specific color for Light Intensity (first trace)
    fig.data[0].line.color = '#D2C49E'  # Light intensity color



    # Add rounded corners to the plot area
    fig.update_layout(
        shapes=[
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                line=dict(width=0),
                fillcolor='rgba(0,0,0,0)',
                layer="below"
            )
        ]
    )
    st.plotly_chart(fig, use_container_width=True, key= 'light_chart')


# Close the database connection when done
conn.close()

