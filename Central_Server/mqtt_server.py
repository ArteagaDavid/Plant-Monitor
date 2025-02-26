# Mosquitto server
'''
This will handle the communication of the Central Sever to the edge nodes (arduinos)
'''
import paho.mqtt.client as mqtt
import json
from datetime import datetime

from ipywidgets import Controller
from plant_controller import PlantController

from db_handler import DataBaseHandler

# from ml_predictor import MLPredictor
class MQTTServer:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
# Here we initialize the modules needed. Database, Plant control for the automation, and ML for future inference implementation
        self.db = DataBaseHandler()
        self.controller = PlantController()
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

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected with result code {rc}")
        if rc !=0:
            try:
                self.client.reconnect()
            except Exception as e:
                print(f"Failed to reconnect MQTT server {e}")

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # We only do sensor since we do not need control logic at this time
        client.subscribe(self.SENSOR_TOPIC)

    def validate_sensor_data(self,payload):
        # required_fields = ["temperature", "humidity", "light"]
        required_fields = ["moisture", "temperature", "humidity", "light_level"]
        return all(field in payload for field in required_fields
                   )

    def on_message(self, client, userdata, msg):
        """
        Collects data from sensors stores into the db, Then gets automation/control instructions
        and publishes it to MQTT server
        :param client: MQTT client
        :param msg: incoming message from Arduino(Plant)
        :return: Returns the automation/control instructions
        """
        try:
            #Extract plant_id from topic. Plant id identifies the plant or edge Arduino node.
            plant_id = int(msg.topic.split("/")[1]) # convert plant id to int
            payload = json.loads(msg.payload.decode())

            if not self.validate_sensor_data(payload):
                print("Invalid sensor data for plant id {plant_id}")
            # store sensor data
            self.db.store_sensor_data(plant_id, payload)
            # Get plant settings
            settings = self.db.get_plant_settings(plant_id)

            if not settings:
                print("No settings for plant id {plant_id}.")
                print("Setting for plant id {plant_id}: {settings}.")
                # Set the plant settings
                self.db.set_plant_settings(plant_id)
                return
            # Get ML predictions
            # ml_predictions = self.ml_predictor.predict(plant_id,payload)

            #Where we calculte the automation decisions for garden.
            #convert to lists since plant controller is expecting it as a list
            sensor_data_list = [payload]
            settings_list = [settings]


            # Future we will introduce ML model to start controlling
            automation_decisions = self.controller.get_control_decisions(
                sensor_data = sensor_data_list,
                settings = settings_list,
                # ml_predictions = ml_predictions
            )
            if not automation_decisions:
                print("No automation decisions for plant id {plant_id}")
                return
            plant_decision = automation_decisions[0]
            control_topic = self.CONTROL_TOPIC.format(plant_id)
            self.client.publish(control_topic, json.dumps(automation_decisions))

        except Exception as e:
            print(f"Error processing message: {e}")

if __name__ == "__main__":
    server = MQTTServer()
    server.start()

