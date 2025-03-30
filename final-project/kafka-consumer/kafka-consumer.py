from kafka import KafkaConsumer
import json, time
from kafka.admin import KafkaAdminClient
from kafka.errors import NoBrokersAvailable
from peewee import *
import os

load_db = PostgresqlDatabase(
    "postgres",
    user=os.environ["LOAD_DB_USER"],
    password=os.environ["LOAD_DB_PWD"],
    host=os.environ["LOAD_DB_HOST"],
)


# defining the base model for load_db
class BaseModel(Model):
    class Meta:
        global load_db
        database = load_db


# defining the model for the health data
# Received event: {'EventType': 'emergency_incident', 'Timestamp': '2024-04-09 11:44:01', 'Location': 'New York', 'Severity': 'high', 'Details': 'This is a simulated emergency_incident event.'}
class HealthData(BaseModel):
    EventType = CharField()
    Timestamp = DateTimeField()
    Location = CharField()
    Severity = CharField()
    Details = TextField()

    class Meta:
        table_name = "health_data"


def dbConnectRetry(db):
    # connect to the database with retry
    max_retries = 20
    retry_delay = 10
    print(f"Attempting to connect to database.")
    for attempt in range(max_retries):
        try:
            db.connect()
            print(f"Connected to database.")
            return True  # Connection  successful
        except Exception as e:
            print(f"Connection attempt {attempt + 1} ; failed: {e}")
            time.sleep(retry_delay)  # Wait  retrying
    print("Failed to connect to the database after several attempts.")
    return False


def is_broker_reachable(bootstrap_servers):
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers, request_timeout_ms=500
        )
        admin_client.close()
        return True
    except NoBrokersAvailable:
        return False


# Source data
source_bootstrap_servers = ["44.201.154.178:9092"]
source_topic = "health_events"
# kafka consumer
print("Initializing consumer...")
source_consumer = KafkaConsumer(
    source_topic,
    bootstrap_servers=source_bootstrap_servers,
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

# Topics
EVENT_TYPES = {"hospital_admission", "emergency_incident", "vaccination"}
SEVERITY = {"low", "medium", "high"}

if not dbConnectRetry(load_db):
    print("Unable to connect to Load_db . Exiting the program.\n")
    raise SystemExit

load_db.create_tables([HealthData], safe=True)

load_db.execute_sql(
    """
CREATE OR REPLACE FUNCTION notify_health_data() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('health_data_insert_channel',CAST(row_to_json(NEW) AS TEXT));
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""
)

load_db.execute_sql(
    "CREATE TRIGGER notify_on_health_data_insert AFTER INSERT ON health_data FOR EACH ROW EXECUTE PROCEDURE notify_health_data();"
)

# Consume events from source
for message in source_consumer:
    event = message.value
    print(f"Received event: {event}")
    h_event = HealthData(**event)
    h_event.save()
    print(f"Ingested event: {event}")


# Received event: {'EventType': 'general_health_report', 'Timestamp': '2024-04-09 11:44:05', 'Location': 'Boston', 'Severity': 'medium', 'Details': 'This is a simulated general_health_report event.'}
