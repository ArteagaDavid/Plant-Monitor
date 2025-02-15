# Mosquitto server
'''
This will handle the communication of the Central Sever to the edge nodes (arduinos)
'''
import paho.mqtt.client as mqtt
import json
from datetime import datetime

from ipywidgets import Controller


# from database_handler import DatabaseHandler
# from ml_predictor import MLPredictor
class MQTTServer:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # self.db = DatabaseHandler()
        # self.controller = PlantController(self.db)
        # self.ml_predictor = MLPredictor()

        # Topics
        self.SENSOR_TOPIC = "garden/+/sensors"  # + is wildcard for plant_id
        self.CONTROL_TOPIC = "garden/{}/control"
    def start(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_forever()
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # We only do sensor since we do not need control logic at this time
        client.subscribe(self.SENSOR_TOPIC)

    def on_message(self, client, userdata, msg):
        try:
            #Extract plant_id from topic
            plant_id = msg.topic.split("/")[1]
            payload = json.loads(msg.payload.decode())

            # store sensor data
            self.db.store_sensor_data(plant_id, payload)

            # Get plant settings
            settings = self.db.get_plant_settings(plant_id)

            # Get ML predictions
            # ml_predictions = self.ml_predictor.predict(plant_id,payload)

            #Where we calculte the automation decisions for garden
            automation_decisions = self.controller.get_control_decisions(
                sensor_data = payload,
                settings = settings
                # ml_predictions = ml_predictions
            )

            control_topic = self.CONTROL_TOPIC.format(plant_id)
            self.client.publish(control_topic, json.dumps(automation_decisions))

        except Exception as e:
            print(f"Error processing message: {e}")
if __name__ == "__main__":
    server = MQTTServer()
    server.start()

