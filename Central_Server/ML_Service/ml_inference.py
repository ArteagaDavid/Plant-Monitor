import joblib

class MLInference:
    def __init__(self):
        self.models = {}

    def predict(self, plant_id, sensor_data):
        """
        placeholder for now
        :param plant_id:
        :param sensor_data:
        :return:
        """
        results = {}
        prediction_moisture = 40
        prediction_duration = 30
        prediction_needs_water = True
        return None

    def confidence(self, plant_id, sensor_data):
        """
        placeholder for now, return confidence to maybe create some logic based ontop?
        or for later implementation of model health analytics
        :param plant_id:
        :param sensor_data:
        :return:
        """
        return None