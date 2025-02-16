# Mosquitto server
'''
This will handle the communication of the Central Sever to the edge nodes (arduinos)
'''
import paho.mqtt.client as mqtt
import json
from datetime import datetime

from ipywidgets import Controller
# from plant_controller import PlantController

from db_handler import DataBaseHandler

# from ml_predictor import MLPredictor
class MQTTServer:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
# Here we initialize the modules needed. Database, Plant controll for the automation, and ML for future inference implementation
        self.db = DataBaseHandler()
        # self.controller = PlantController(self.db)
        # self.ml_predictor = MLPredictor()

        # Topics are what we subscribe to. (Central server Pi) sensors for data collection. Control watering and light control
        self.SENSOR_TOPIC = "garden/+/sensors"  # + is wildcard for plant_id
        self.CONTROL_TOPIC = "garden/{}/control"


    def start(self):
        try:
            # This port is the Pi's server port.
            self.client.connect("localhost", 1883, 60)
            #logic in case of disconnect try to reconnect
            self.client.on_disconnect = self.on_disconnect
            self.client.loop_forever()
        except Exception as e:
            print(f"Failed to start MQTT server {e}")

    def on_disconnect(self, client, rc):
        print(f"Disconnected with result code {rc}")
        if rc !=0:
            try:
                self.client.reconnect()
            except Exception as e:
                print(f"Failed to reconnect MQTT server {e}")

    def on_connect(self, client, flags, rc):
        print("Connected with result code "+str(rc))
        # We only do sensor since we do not need control logic at this time
        client.subscribe(self.SENSOR_TOPIC)

    def validate_sensor_data(self,payload):
        required_fields = ["temperature", "humidity", "light"]
        return all(field in payload for field in required_fields)

    def on_message(self, client, msg):
        """
        Collects data from sensors stores into the db, Then gets automation/control instructions
        and publishes it to MQTT server
        :param client: MQTT client
        :param msg: incoming message from Arduino(Plant)
        :return: Returns the automation/control instructions
        """
        try:
            #Extract plant_id from topic. Plant id identifies the plant or edge Arduino node.
            plant_id = msg.topic.split("/")[1]
            payload = json.loads(msg.payload.decode())
            if not self.validate_sensor_data(payload):
                print("Invalid sensor data for plant id {plant_id}")
            # store sensor data
            self.db.store_sensor_data(plant_id, payload)

            # Get plant settings
            settings = self.db.get_plant_settings(plant_id)

            # Get ML predictions
            # ml_predictions = self.ml_predictor.predict(plant_id,payload)

            #Where we calculte the automation decisions for garden.
            # Future we will introduce ML model to start controlling
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

