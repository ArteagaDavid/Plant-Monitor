import sqlite3
from datetime import datetime

class DataBaseHandler:
    def __init__(self, db_name = 'plant_data.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
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
        light_schedule_start TEXT,
        light_schedule_end TEXT,
        plant_type TEXT,
        ml_enabled boolean
        )
    ''')

        conn.commit()
        conn.close()
        # Add this line to call the init_default_settings method
        self.init_default_settings()

    def init_default_settings(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        #Create a default plant settings to consider case where its a new plant or no settings exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS default_plant_settings (
            plant_type TEXT PRIMARY KEY,
            moisture_threshold REAL,
            light_threshold REAL,
            watering_duration INTEGER,
            lighting_duration INTEGER,
            light_schedule_start TEXT,
            light_schedule_end TEXT,
            ml_enabled BOOLEAN
            )
        ''')

        default_settings = [
            ('herbs', 0.6, 800, 30, 120, '06:00:00', '18:00:00', False),
            ('vegetables', 0.7, 1000, 45, 180, '08:00:00', '18:00:00', False),
            ('succulents', 0.3, 600, 15, 240, '08:00:00', '18:00:00', False),
            ('tropical', 0.8, 400, 60, 120, '08:00:00', '18:00:00', False),
            ('default', 0.6, 800, 30, 120, '08:00:00', '18:00:00', False)  # Generic default
        ]

        cursor.executemany('''
            INSERT OR REPLACE INTO default_plant_settings
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_settings)
        conn.commit()
        conn.close()
    def set_plant_settings(self, plant_id, plant_type='default', custom_settings=None):
        """
        This should be called to set the settings for a plant, by default it will start with generic settings.
        or a customized approach.
        :param plant_id: The id of the plant we need settings for
        :param plant_type: The type of the plant we need settings for herbes, tropical, succulents etc...
        :param custom_settings: If we have specific settings we want for a plant. (I plan to add carnivorous plants.
        That require custom settings)
        :return:
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM default_plant_settings
            WHERE plant_type = ?
        ''', (plant_type,))
        defaults = cursor.fetchone()

        if not defaults:
            # Edge case when entering a type that is not found
            cursor.execute('''
                SELECT * FROM default_plant_settings
                WHERE plant_type = 'default'
            ''')
            defaults = cursor.fetchone()
        # Prepare the settings dict
        #Setting up new plant set datetime correctly
        today = datetime.now().strftime("%Y-%m-%d")
        settings = {
            'plant_id': plant_id,
            'moisture_threshold': defaults[1],
            'light_threshold': defaults[2],
            'watering_duration': defaults[3],
            'lighting_duration': defaults[4],
            'light_schedule_start': f"{today} {defaults[5]}",
            'light_schedule_end': f"{today} {defaults[6]}",
            'plant_type': plant_type,
            'ml_enabled': defaults[7],
        }
        # If there are custom settings entered introduce those. Optimization thought, i could check this at the beginning to avoid fetching for uneccessary
        # settings, but i realize the custom settings is not going to be used frequently.
        if custom_settings:
            settings.update(custom_settings)
        #now we insert settings into the plant_settings table
        cursor.execute('''
            INSERT OR REPLACE INTO plant_settings
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            settings['plant_id'],
            settings['moisture_threshold'],
            settings['light_threshold'],
            settings['watering_duration'],
            settings['lighting_duration'],
            settings['light_schedule_start'],
            settings['light_schedule_end'],
            settings['plant_type'],
            settings['ml_enabled']
        ))

        conn.commit()
        conn.close()
        return settings

    def store_sensor_data(self, plant_id,data):
        conn = sqlite3.connect(self.db_name)
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
        conn.commit()
        conn.close()

    def get_plant_settings(self, plant_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM plant_settings WHERE plant_id = ?
        ''', (plant_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'plant_id': result[0],
                'moisture_threshold': result[1],
                'light_threshold': result[2],
                'watering_duration': result[3],
                'lighting_duration': result[4],
                'lighting_schedule_start': result[5],
                'lighting_schedule_end': result[6],
                'plant_type': result[7],
                'ml_enabled': result[8]
            }
        return None

