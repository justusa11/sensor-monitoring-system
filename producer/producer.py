# Load Libra
import requests
import random
import time

#API_URL = "http://127.0.0.1:8000/sensor"
API_URL = "http://backend:8000/sensor"

def generate_sensor_data(sensor_id: int) -> dict[str, float | int]:
    return {
        "sensor_id": sensor_id,
        "temp_in": round(random.uniform(50, 70), 2),
        "temp_out": round(random.uniform(30, 50), 2),
        "flow_rate": round(random.uniform(0.8, 2.5), 2)
    }

def run_producer():
    while True:
        for sensor_id in range(1, 4): # Simulate 3 sensors
            data = generate_sensor_data(sensor_id)
            try:
                response = requests.post(API_URL, json=data)
                print(f"Sensor {sensor_id} -> {response.status_code} | {response.json()}")
            except Exception as e:
                print("Error:", e)
        time.sleep(5)

if __name__ == "__main__":
    run_producer()