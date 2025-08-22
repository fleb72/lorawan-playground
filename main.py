from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from datetime import datetime
from zoneinfo import ZoneInfo

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException

#import logging
#from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv
import os


## Connfiguration logger
#logger = logging.getLogger("mon_logger")
#logger.setLevel(logging.INFO)

#handler = TimedRotatingFileHandler("log.txt", when="midnight", interval=1, backupCount=7)
#formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
#handler.setFormatter(formatter)

#logger.addHandler(handler)


load_dotenv('/home/ubuntu/lora-ttn/.env')
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Configuration et connexion influxDB
bucket = os.getenv("INFLUXDB_BUCKET")
org = os.getenv("INFLUXDB_ORG")
token = os.getenv("INFLUXDB_TOKEN")
url = os.getenv("INFLUXDB_URL")

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def update_latest():
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -1h)
      |> filter(fn: (r) => r["_measurement"] == "lora_data")
      |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity")
      |> last()
    '''
    result = client.query_api().query(org=org, query=query)

    values = {}
    timestamp = None
    for table in result:
        for record in table.records:
            values[record.get_field()] = record.get_value()
            timestamp = record.get_time()  # récupère le timestamp

    local_time = timestamp.astimezone(ZoneInfo("Europe/Paris"))
    formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"
    last_temperature = values.get("temperature", "N/A")
    last_humidity = values.get("humidity", "N/A")

    return formatted_time, last_temperature, last_humidity

def update_graphes():
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -12h)
      |> filter(fn: (r) => r._measurement == "lora_data")
      |> filter(fn: (r) => r._field == "temperature" or r._field == "humidity")
      |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
      |> keep(columns: ["_time", "_field", "_value"])
   '''

    result = client.query_api().query(org=org, query=query)

    points_temperature = []
    points_humidity = []

    for table in result:
        for record in table.records:
            local_time = record.get_time().astimezone(ZoneInfo("Europe/Paris"))
            point = {
                "x": local_time.isoformat(),
                "y": record.get_value()
            }
            if record.get_field() == "temperature":
                points_temperature.append(point)
            elif record.get_field() == "humidity":
                points_humidity.append(point)

    return points_temperature, points_humidity


# page HTML pour dernières mesures
@app.get("/latest", response_class=HTMLResponse)
def latest_data(request: Request):
    token = request.query_params.get("access")
    if token != ACCESS_TOKEN:
        raise HTTPException(status_code=403, detail="Accès refusé")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "interval" : (12 * 60)	 #  Mise à jour toutes les 12 minutes
    })

@app.get("/api/latest-data")
def get_latest_data():
    last_formatted_time, last_temperature, last_humidity = update_latest()
    points_temperature, points_humidity = update_graphes()

    return {
        "temperature": last_temperature,
        "humidity": last_humidity,
        "formatted_time": last_formatted_time,
        "points_temperature": points_temperature,
        "points_humidity": points_humidity
    }
