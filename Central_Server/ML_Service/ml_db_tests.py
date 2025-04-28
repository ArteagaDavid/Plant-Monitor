
from ml_db_handler import MLDataBaseHandler

db = MLDataBaseHandler()

plant_id = 101
moisture_before = 50
moisture_after = 80
watering_duration = 15

event = db.store_watering_event_initial(plant_id,moisture_before,watering_duration)
print(event)

event_2 = db.store_watering_event_final(event,moisture_after)
print(event_2)