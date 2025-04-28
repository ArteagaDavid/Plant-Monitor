from typing import Union
from fastapi import FastAPI

from Central_Server.ML_Service.ml_db_tests import plant_id
from Central_Server.mqtt_server import MQTTServer

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/irrigate")
def read_root():
    plant_id = 'plant1'
    payload = {'plant_id': plant_id}
    MQTTServer.process_ios_command()

    return {"Hello": "World"}

@app.get("/feedback")
def read_root():
    return {"Hello": "World"}