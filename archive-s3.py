import json
from collections import defaultdict
import boto3
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv
import os

load_dotenv('/perso/lora-ttn/.env')

# Connexion OVHcloud S3 (à adapter)
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

s3 = boto3.client("s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

# Connexion  InfluxDB (à adapter)
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_MEASUREMENT = "lora_data"
client = InfluxDBClient(
    url = INFLUXDB_URL,
    token = INFLUXDB_TOKEN,
    org = INFLUXDB_ORG
)

# Requête Flux
query = f'''
from(bucket: "{INFLUXDB_BUCKET}")
  |> range(start: -1d)
  |> filter(fn: (r) => r._measurement == "{INFLUXDB_MEASUREMENT}")
'''

# Extraction des données
tables = client.query_api().query(query)
raw_data = []

for table in tables:
    for record in table.records:
        raw_data.append({
            "time": record.get_time().isoformat(),
            "field": record.get_field(),
            "value": record.get_value(),
            "device": record.values.get("device")
        })

# Regroupement par time + device
grouped = defaultdict(dict)

for entry in raw_data:
    key = (entry["time"], entry["device"])
    grouped[key]["time"] = entry["time"]
    grouped[key]["device"] = entry["device"]
    grouped[key][entry["field"]] = entry["value"]

# Résultat final
result = list(grouped.values())

# Export JSON
json_data = json.dumps(result, indent=2)
#print(json_data)

# Nom du fichier avec timestamp
filename = f"lora_data_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
# Envoi vers S3
s3.put_object(
    Bucket=S3_BUCKET,
    Key=f"archives/{filename}",
    Body=json_data,
    ContentType='application/json'
)

#print(f"JSON archivé dans S3 : {filename}")

