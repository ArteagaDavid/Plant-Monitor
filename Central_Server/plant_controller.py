from datetime import datetime

class PlantController:

    def get_control_decisions(self, sensor_data, settings, ml_predictions =None):
        """ Calculate the automation actions based on sensor data, settings, and ML predictions."""
        if ml_predictions and settings["ml_enabled"]:
            return self.get_ml_based_automation(ml_predictions, settings)
        else:
            return self.get_rule_based_decisions(sensor_data, settings)

    def get_rule_based_decisions(self, sensor_data, settings):
        current_hour = datetime.now().hour

        #Check if water is needed
        needs_water = sensor_data["needs_water"] < settings["moisture_threshold"]

        #Light control
        schedule_active = (current_hour >= settings["schedule_start"]) and (current_hour < settings["schedule_end"])
        needs_light = schedule_active and sensor_data["light_level"] < settings["light_threshold"]

        return {
            'water_pump': {
                'active': needs_water,
                'duration': settings["watering_duration"] if needs_water else 0,
            },
            'grow_light': {
                'active': needs_light
            }
        }

    def get_ml_based_automation(self, ml_predictions, settings):
        return {
            'water_pump': {
                'active': ml_predictions["needs_water"],
                'duration': ml_predictions["watering_duration"]
            },
            'grow_light': {
                'active': ml_predictions["needs_light"]
            }
        }
