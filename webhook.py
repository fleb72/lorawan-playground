from fastapi import FastAPI, Request, HTTPException

from datetime import datetime
from zoneinfo import ZoneInfo

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException

import logging
from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv
import os


# Connfiguration logger
logger = logging.getLogger("mon_logger-webhook")
logger.setLevel(logging.INFO)

handler = TimedRotatingFileHandler("log-webhook.txt", when="midnight", interval=1, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)


load_dotenv('/home/perso/lora-ttn/.env')
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Configuration et connexion influxDB
bucket = os.getenv("INFLUXDB_BUCKET")
org = os.getenv("INFLUXDB_ORG")
token = os.getenv("INFLUXDB_TOKEN")
url = os.getenv("INFLUXDB_URL")

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

app = FastAPI()


# Route FastAPI pour recevoir le webhook TTN
@app.post("/ttn-uplink")
async def receive_uplink(request: Request):
    raw = await request.json()

    # Authentification du device
    AUTHORIZED_DEVICES = os.getenv("AUTHORIZED_DEVICES", "").split(",")

    dev_eui = raw.get("end_device_ids", {}).get("dev_eui")

    if not dev_eui or dev_eui not in AUTHORIZED_DEVICES:
        logger.exception(f"Unauthorized device: {dev_eui}")
        raise HTTPException(status_code=403, detail=f"Unauthorized device: {dev_eui}")


    logger.info("Authorized device")

    # Extraire la température&humidité
    temperature = raw.get("uplink_message", {}).get("decoded_payload", {}).get("temperature")
    humidity = raw.get("uplink_message", {}).get("decoded_payload", {}).get("humidity")
    if temperature is None or humidity is None:
        logger.warning("Skipped, No temperature or humidity in payload!")
        raise HTTPException(status_code=403, detail=f"Skipped, No temperature or humidity in payload!")


    # Création du point
    point = Point("lora_data") \
        .tag("device", "heltec-v3-perso") \
        .field("temperature", round(float(temperature), 1)) \
        .field("humidity", round(float(humidity), 1))

    # Écriture
    try:
        write_api.write(bucket=bucket, org=org, record=point)
        logger.info("Data upload complete.")
    except ApiException as e:
        logger.error(f"Failed to send: {e.status} - {e.reason}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")

