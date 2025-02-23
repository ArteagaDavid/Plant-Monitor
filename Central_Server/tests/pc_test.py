import unittest
import sqlite3
from datetime import datetime
from Central_Server.plant_controller import PlantController
import os


# def get_control_decisions(self, sensor_data, settings, ml_predictions=None):
#     """ Calculate the automation actions based on sensor data, settings, and ML predictions."""
#     if ml_predictions and settings["ml_enabled"]:
#         return self.get_ml_based_automation(ml_predictions, settings)
#     else:
#         return self.get_rule_based_decisions(sensor_data, settings)
class PCTest(unittest.TestCase):
    def setUp(self):
        self.plant_controller = PlantController()
        self.sensor_data = [
            {
                "id": 1,
                "plant_id": 101,
                "moisture": 75,
                "temperature": 65,
                "humidity": 80,
                "light_level": 85,
                "timestamp": "2025-02-21 14:30:22"
            },
            {
                "id": 2,
                "plant_id": 102,
                "moisture": 55,
                "temperature": 40,
                "humidity": 70,
                "light_level": 90,
                "timestamp": "2025-02-21 14:30:22"
            }
        ]

        self.settings = [
            {
                "plant_id": 101,
                "moisture_threshold": 75,  # Fixed the space in key name
                "light_threshold": 85,
                "watering_duration": 5,
                "light_duration": 5,
                "light_schedule_start": "2025-02-21 14:30:22",
                "light_schedule_end": "2025-02-21 16:30:22",
                "plant_type": "herbs",
                "ml_enabled": False,
            },
            {
                "plant_id": 102,
                "moisture_threshold": 55,  # Fixed the space in key name
                "light_threshold": 90,
                "watering_duration": 3,
                "light_schedule_start": "2025-02-21 14:30:22",
                "light_schedule_end": "2025-02-21 16:30:22",
                "plant_type": "herbs",
                "ml_enabled": False,
            }
        ]

    def test_rule_based_decisions(self):
        decisions = self.plant_controller.get_rule_based_decisions(
            self.sensor_data,
            self.settings
        )

        # Test for first plant
        self.assertEqual(len(decisions), 2)
        first_plant = decisions[0]
        self.assertEqual(first_plant["plant_id"], 101)
        self.assertEqual(first_plant["water_pump"]["active"], True)
        self.assertEqual(first_plant["water_pump"]["duration"], 5)

        # Test for second plant
        second_plant = decisions[1]
        self.assertEqual(second_plant["plant_id"], 102)
        self.assertEqual(second_plant["water_pump"]["active"], True)
        self.assertEqual(second_plant["water_pump"]["duration"], 3)

    # def test_ml_based_automation(self):
    #     ml_predictions = {
    #         101: {"needs_light": True, "needs_water": True},
    #         102: {"needs_light": False, "needs_water": False}
    #     }
    #
    #     # Enable ML for both plants
    #     for setting in self.settings:
    #         setting["ml_enabled"] = True
    #
    #     decisions = self.plant_controller.get_control_decisions(
    #         self.sensor_data,
    #         self.settings,
    #         ml_predictions
    #     )
    #
    #     self.assertEqual(len(decisions), 2)
    #     # Check first plant decisions
    #     first_plant = decisions[0]
    #     self.assertEqual(first_plant[0]["plant_id"], 101)
    #     self.assertEqual(first_plant["water_pump"]["active"], False)  # Based on settings
    #     self.assertEqual(first_plant["water_pump"]["duration"], 5)  # From settings
    #     self.assertEqual(first_plant["grow_light"]["active"], True)  # From ML predictions
    #
    #     # Check second plant decisions
    #     second_plant = decisions[1]
    #     self.assertEqual(second_plant[1]["plant_id"], 102)
    #     self.assertEqual(second_plant["water_pump"]["active"], True)  # Based on settings
    #     self.assertEqual(second_plant["water_pump"]["duration"], 3)  # From settings
    #     self.assertEqual(second_plant["grow_light"]["active"], False)  # From ML predictions

    def test_needs_water(self):
        # Test case where moisture is below threshold
        plant_data = {"moisture": 70}
        plant_settings = {"moisture_threshold": 75}
        self.assertTrue(
            self.plant_controller._needs_water(plant_data, plant_settings)
        )

        # Test case where moisture is above threshold
        plant_data = {"moisture": 80}
        self.assertFalse(
            self.plant_controller._needs_water(plant_data, plant_settings)
        )

    def test_needs_light(self):
        current_time = datetime.strptime(
            "2025-02-21 15:30:22",
            "%Y-%m-%d %H:%M:%S"
        )
        plant_data = {"light_level": 80}
        plant_settings = {
            "light_threshold": 85,
            "light_schedule_start": "2025-02-21 14:30:22",
            "light_schedule_end": "2025-02-21 16:30:22"
        }

        # Test when within schedule and below threshold
        self.assertTrue(
            self.plant_controller._needs_light(
                plant_data,
                plant_settings,
                current_time
            )
        )

        # Test when light level is above threshold
        plant_data["light_level"] = 90
        self.assertFalse(
            self.plant_controller._needs_light(
                plant_data,
                plant_settings,
                current_time
            )
        )

    def test_invalid_datetime_format(self):
        current_time = datetime.now()
        plant_data = {"light_level": 80}
        plant_settings = {
            "light_threshold": 85,
            "light_schedule_start": "invalid_datetime",
            "light_schedule_end": "invalid_datetime"
        }

        # Should return False for invalid datetime format
        self.assertFalse(
            self.plant_controller._needs_light(
                plant_data,
                plant_settings,
                current_time
            )
        )


if __name__ == '__main__':
    unittest.main()
