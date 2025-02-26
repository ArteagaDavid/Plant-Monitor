from datetime import datetime


class PlantController:

    def get_control_decisions(self, sensor_data, settings, ml_predictions =None):
        """ Calculate the automation actions based on sensor data, settings, and ML predictions."""
        if ml_predictions and any(setting.get("ml_enabled", False) for setting in settings):
            return self.get_ml_based_automation(ml_predictions, settings)
        else:
            return self.get_rule_based_decisions(sensor_data, settings)

    def get_rule_based_decisions(self, sensor_data_list, settings_list):
        results = []
        current_time = datetime.now()

        for plant_data, plant_settings in zip(sensor_data_list, settings_list):
            # Extract the plant_id
            plant_id = plant_data.get("plant_id")

            plant_decisions = self._create_plant_decision(
                plant_id,
                self._needs_water(plant_data, plant_settings),
                self._needs_light(plant_data, plant_settings, current_time),
                plant_settings
            )


            results.append(plant_decisions)

        return results

    def _needs_water(self, plant_data, plant_settings):
        return plant_data.get("moisture", 0) <= plant_settings.get("moisture_threshold", 100)

    def _needs_light(self, plant_data, plant_settings, current_time):
        try:
            light_start = datetime.strptime(plant_settings.get("light_schedule_start", ""), "%Y-%m-%d %H:%M:%S")
            light_end = datetime.strptime(plant_settings.get("light_schedule_end", ""), "%Y-%m-%d %H:%M:%S")
            return (light_start <= current_time <= light_end and plant_data.get("light_level", 0) < plant_settings.get("light_threshold", 100))
        except ValueError:
            print("Error with datetime format")
            return False

    def _create_plant_decision(self, plant_id, needs_water, needs_light, plant_settings):
        return {
            "plant_id": plant_id,
            "water_pump": {
                "active": needs_water,
                "duration": plant_settings.get("watering_duration", 0) if needs_water else 0,

            },
            "grow_light": {
                "active": needs_light
            }
        }
    def get_ml_based_automation(self, ml_predictions, settings):
        #For future we want to be able to make ml predictions for plants at the same time
        results = []
        for plant_settings in settings:
            plant_id = plant_settings.get("plant_id")
            plant_predictions = ml_predictions.get(plant_id, {})

            decisions = {
                "plant_id": plant_id,
                "water_pump": {
                    "active": plant_settings.get("water_pump_active", False),
                    "duration": plant_settings.get("watering_duration", 0),
                },
                "grow_light": {
                    "active": plant_predictions.get("needs_light", False)
                }
            }
            results.append(decisions)
        return results
