import unittest
import sqlite3
from datetime import datetime
from Central_Server.db_handler import DataBaseHandler
import os
class TestDB(unittest.TestCase):
    def setUp(self):
        """ Run before each test """
        self.test_db_name = "test_plant_data.db"
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)

        self.db_handler = DataBaseHandler(self.test_db_name)

    def tearDown(self):
        """ Run after each test """
        #Clean up the database after testing
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)

    def test_init_db(self):
        """ Test if database and tables are created correctly """
        conn = sqlite3.connect(self.test_db_name)
        cursor = conn.cursor()

        #Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]

        self.assertIn("sensor_data", table_names)
        self.assertIn("plant_settings", table_names)
        self.assertIn("default_plant_settings", table_names)

        conn.close()
    def test_init_default_plant_settings(self):
        """ Test if default plant settings are created correctly """
        conn = sqlite3.connect(self.test_db_name)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM default_plant_settings WHERE plant_type = 'herbs'")
        herb_settings = cursor.fetchone()
        self.assertIsNotNone(herb_settings)
        self.assertEqual(herb_settings[1], 0.6) # Moisture
        self.assertEqual(herb_settings[2], 800) # Light

        self.assertEqual(herb_settings[5], '06:00:00')  # light_schedule_start
        self.assertEqual(herb_settings[6], '18:00:00')  # light_schedule_end
        conn.close()

    def test_set_plant_settings_default(self):
        """Test setting plant settings with default values"""
        settings = self.db_handler.set_plant_settings('test_plant1')

        self.assertEqual(settings['plant_type'], 'default')
        self.assertEqual(settings['moisture_threshold'], 0.6)
        self.assertEqual(settings['light_threshold'], 800)

    def test_set_plant_settings_custom_type(self):
        """Test setting plant settings with a specific plant type"""
        settings = self.db_handler.set_plant_settings('test_plant2', 'tropical')

        self.assertEqual(settings['plant_type'], 'tropical')
        self.assertEqual(settings['moisture_threshold'], 0.8)
        self.assertEqual(settings['light_threshold'], 400)

    def test_set_plant_settings_custom_settings(self):
        """Test setting plant settings with custom overrides"""
        custom_settings = {
            'moisture_threshold': 0.9,
            'light_threshold': 1200
        }
        settings = self.db_handler.set_plant_settings('test_plant3', 'herbs', custom_settings)

        self.assertEqual(settings['moisture_threshold'], 0.9)
        self.assertEqual(settings['light_threshold'], 1200)

    def test_store_sensor_data(self):
        """Test storing sensor data"""
        test_data = {
            'moisture': 0.5,
            'temperature': 25.0,
            'humidity': 60.0,
            'light_level': 800
        }

        self.db_handler.store_sensor_data('test_plant1', test_data)

        conn = sqlite3.connect(self.test_db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensor_data WHERE plant_id = 'test_plant1'")
        result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result[1], 'test_plant1')
        self.assertEqual(result[2], 0.5)
        self.assertEqual(result[3], 25.0)

        conn.close()

    def test_get_plant_settings_existing(self):
        """Test getting settings for an existing plant"""
        # First set some settings
        self.db_handler.set_plant_settings('test_plant4', 'herbs')

        # Then retrieve them
        settings = self.db_handler.get_plant_settings('test_plant4')

        self.assertIsNotNone(settings)
        self.assertEqual(settings['plant_type'], 'herbs')
        self.assertEqual(settings['moisture_threshold'], 0.6)
        self.assertEqual(settings['light_threshold'], 800)

    def test_get_plant_settings_nonexistent(self):
        """Test getting settings for a non-existent plant"""
        settings = self.db_handler.get_plant_settings('nonexistent_plant')
        self.assertIsNone(settings)

if __name__ == '__main__':
    unittest.main()