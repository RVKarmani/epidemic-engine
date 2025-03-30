import os
from flask import Flask, Response, render_template
import psycopg2
import psycopg2.extensions
import select, json, time
from collections import defaultdict

location_stats = defaultdict(int)
severity_stats = defaultdict(int)
event_type_stats = defaultdict(int)

def stream_loc_stats():
    while True:
        yield "data: " + json.dumps(location_stats) + "\n\n"
        time.sleep(5)

def stream_event_type_stats():
    while True:
        yield "data: " + json.dumps(event_type_stats) + "\n\n"
        time.sleep(5)

def stream_sev_stats():
    while True:
        yield "data: " + json.dumps(severity_stats) + "\n\n"
        time.sleep(5)

def updateStats(data):
    global location_stats, severity_stats, event_type_stats
    location_stats[data["Location"]] +=1
    severity_stats[data["Severity"]] +=1
    event_type_stats[data["EventType"]] +=1

def stream_messages():
    conn = psycopg2.connect(
        host=os.environ["LOAD_DB_HOST"],
        database="postgres",
        user=os.environ["LOAD_DB_USER"],
        password=os.environ["LOAD_DB_PWD"],
    )
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    curs = conn.cursor()
    curs.execute("LISTEN health_data_insert_channel;")

    while True:
        select.select([conn], [], [])
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop()
            updateStats(json.loads(notify.payload))
            yield "data: " + notify.payload + "\n\n"


app = Flask(__name__)

@app.route("/healthevents", methods=["GET"])
def get_messages():
    return Response(stream_messages(), mimetype="text/event-stream")

@app.route("/sevstats", methods=["GET"])
def get_sev_stats():
    return Response(stream_sev_stats(), mimetype="text/event-stream")

@app.route("/locstats", methods=["GET"])
def get_loc_stats():
    return Response(stream_loc_stats(), mimetype="text/event-stream")

@app.route("/eventtypestats", methods=["GET"])
def get_event_type_stats():
    return Response(stream_event_type_stats(), mimetype="text/event-stream")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

