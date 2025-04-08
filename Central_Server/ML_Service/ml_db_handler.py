import sqlite3
from datetime import datetime

class MLDataBaseHandler:
    def __init__(self, db_name = 'plant_data.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watering_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER NOT NULL,
                plant_id TEXT NOT NULL,
                user_adjusted_moisture_threshold REAL,
                user_adjusted_watering_duration INTEGER,
                user_adjusted_next_watering_time DATETIME,
                user_notes TEXT,
                
                FOREIGN KEY (plant_id) REFERENCES plant_settings(id)
                FOREIGN KEY (prediction_id) REFERENCES watering_predictions(id)
            )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS watering_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT
        )''')

        # For the the watering events capture
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS watering_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_id TEXT NOT NULL,
        watering_duration INTEGER,
        moisture_before INTEGER,
        moisture_after INTEGER,
        timestamp DATETIME,
        prediction_id INTEGER,
        FOREIGN KEY (prediction_id) REFERENCES watering_predictions(id),
        FOREIGN KEY (plant_id) REFERENCES plant_settings(id)
        
        
        )''')




        conn.commit()
        conn.close()
        # Add this line to call the init_default_settings method

    def store_watering_feedback(self, plant_id, data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
 # TODO - Create db table for storing these values. possibly "watering_feedback.db"
 #        cursor.execute('''
 #                            INSERT INTO sensor_data
 #                            (prediction_id, plant_id, user_adjusted_watering_duration, user_adjusted_next_watering_time, user_notes)
 #                            VALUES (?, ?, ?, ?, ?, ?)
 #                        ''', (
 #            data['prediction_id'],
 #            data['plant_id'],
 #            data['user_adjusted_watering_duration'],
 #            data['user_adjusted_next_watering_time'],
 #            data['user_notes']
 #        ))
        conn.commit()
        conn.close()

    def store_watering_prediction(self, plant_id, predicted_moisture_threshold, predicted_duration, predicted_time):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

    def store_watering_event_initial(self, plant_id, moisture_before, watering_duration):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        #TODO add the insert of prediction_id when that becomes available.
        cursor.execute('''
                    INSERT INTO watering_events
                    (plant_id, watering_duration, moisture_before, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
            plant_id,
            watering_duration,
            moisture_before,
            datetime.now()
        ))
        #Save the event to store moisture after
        event_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return event_id

    def store_watering_event_final(self, event_id, moisture_after):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE watering_events
            SET moisture_after = ?
            WHERE id = ?
        ''', (moisture_after, event_id))
        conn.commit()
        conn.close()
