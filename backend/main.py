# Load Libraries
from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import pandas as pd
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta, timezone
from functools import lru_cache

# Logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

####################################################
# Define app and startup logic
# Main purpose is to set up the sensor_data table 
# and avoid repeating the create table
#http://127.0.0.1:8000/docs
####################################################
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect("/data/sensor_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT,
            temp_in REAL,
            temp_out REAL,
            flow_rate REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    yield

app = FastAPI(lifespan=lifespan)

####################################################
# Define data model
####################################################
class SensorData(BaseModel):
    sensor_id: int
    temp_in: float 
    temp_out: float
    flow_rate: float

####################################################
# POST endpoint to receive sensor data
####################################################

@app.post("/sensor")
def receive_data(data: SensorData):
    logging.info(f"Recieve data from sensor {data.sensor_id}")
    conn = sqlite3.connect("/data/sensor_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensor_data (sensor_id, temp_in, temp_out, flow_rate)
        VALUES (?, ?, ?, ?)
    """, (data.sensor_id, data.temp_in, data.temp_out, data.flow_rate))
    conn.commit()
    conn.close()
    return {"message": "Data received successfully"}

####################################################
# GET endpoint to retrieve sensor data
####################################################
@app.get("/sensor")
def get_data():
    try:
        conn = sqlite3.connect("/data/sensor_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT sensor_id, temp_in, temp_out, flow_rate, timestamp FROM sensor_data ORDER BY timestamp")
        rows = cursor.fetchall()
        conn.close()
        return JSONResponse(content=[
            {
                "sensor_id": row[0],
                "temp_in": row[1],
                "temp_out": row[2],
                "flow_rate": row[3],
                "timestamp": row[4]
            }
            for row in rows
        ])
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
####################################################
# Checks for sensors - last 10 minutes
####################################################
@app.get("/sensor/status")
def get_sensor_status():
    conn = sqlite3.connect("/data/sensor_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sensor_id, MAX(timestamp) 
        FROM sensor_data 
        GROUP BY sensor_id
    """)
    rows = cursor.fetchall()
    conn.close()

    offline_sensors = []
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=10)

    for sensor_id, last_seen in rows:
        try:
            last_seen_dt = pd.to_datetime(last_seen)
            if last_seen_dt.tzinfo is None:
                last_seen_dt = last_seen_dt.tz_localize('UTC')
            if last_seen_dt < threshold:
                offline_sensors.append({
                    "sensor_id": sensor_id,
                    "last_seen": last_seen
                })
                logging.warning(f"Sensor {sensor_id} is offline. Last seen: {last_seen}")
        except Exception as e:
            logging.error(f"Failed to parse timestamp for sensor {sensor_id}: {e}")

    return {"offline_sensors": offline_sensors}

# Cache
def get_connection():
    return sqlite3.connect("/data/sensor_data.db", check_same_thread=False)