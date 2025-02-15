import sqlite3
from datetime import datetime

class DataBaseHandler:
    def __init__(self):
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect('plant_data.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id TEXT,
                moisture REAL,
                temperature REAL,
                humidity REAL,
                light_level REAL,
                timestamp DATETIME
            )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plant_settings(
        plant_id TEXT PRIMARY KEY,
        moisture_threshold REAL,
        light_threshold REAL,
        watering_duration INTEGER,
        lighting_duration INTEGER,
        light_schedule_start INTEGER,
        light_schedule_end INTEGER,
        plant_type TEXT,
        ml_enabled boolean
        )
    ''')

        conn.commit()
        conn.close()

    def store_sensor_data(self, plant_id,data):
        conn = sqlite3.connect('plant_data.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sensor_data
            (plant_id, moisture, temperature, humidity, light_level,timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            plant_id,
            data['moisture'],
            data['temperature'],
            data['humidity'],
            data['light_level'],
            datetime.now()
        ))

    def get_plant_settings(self, plant_id):
        conn = sqlite3.connect('plant_data.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM plant_settings WHERE plant_id = ?
        ''', (plant_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'moisture_threshold': result[1],
                'light_threshold': result[2],
                'watering_duration': result[3],
                'lighting_schedule_start': result[4],
                'lighting_schedule_end': result[5],
                'plant_type': result[6],
                'ml_enabled': result[7]
            }
        return None

