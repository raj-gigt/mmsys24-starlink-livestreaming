from pprint import pprint
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from pymongo import MongoClient
from dataclasses import dataclass
import subprocess
import os
import re
import time
import threading
import schedule
import sys
# from typing import List
import socket


app = Flask(__name__)
methods = ["POST"]

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin'

client = MongoClient("mongodb://starlink:starlink@mongo:27017/")
db = client["starlink"]


@dataclass
class PingMetric:
    timestamp: float
    seq_no: float
    rtt: float = 0.0

INTERFACE = os.getenv("INTERFACE")
PING_INTERVAL = os.getenv("LATENCY_TEST_INTERVAL_SECONDS", "1")


ping_metric = list[PingMetric]()
count = 0
ping_thread = None
last_value = -1
current_experiment_id = None
probe_health = {'ok': False, 'probe_at_s': None, 'success_at_s': None, 'rtt_ms': None}


def py_ping(hostname: str) -> None:
    global count
    global last_value
    global probe_health
    count += 1
    probe_ok = False
    observed_rtt = None
    upper_bound = False

    try:
        if not INTERFACE:
            output = subprocess.check_output(["ping", "-W", "1", "-c", "1", hostname])
        else:
            output = subprocess.check_output(["ping", "-I", INTERFACE, "-W", "1", "-c", "1", hostname])
        line = output.decode("utf-8")
        # Typed health accepts all iputils precision formats. Keep the legacy
        # decimal-only scalar path below unchanged for original-CMAB control.
        observed = re.search(r"icmp_seq=(\d+).*time\s*([=<])\s*(\d+(?:\.\d+)?)", line)
        if observed:
            observed_rtt = float(observed.group(3))
            upper_bound = observed.group(2) == '<'
            probe_ok = True
        match = re.search(r"icmp_seq=(\d+).*time=(\d+\.\d+)", line)
        if match:
            rtt = float(match.group(2))
            pm = PingMetric(time.time(), count, rtt)
            last_value = rtt
            ping_metric.append(pm)
            probe_ok = True
    
    except subprocess.CalledProcessError as e:
        print(e.output)
        pm = PingMetric(time.time(), count, last_value)
        ping_metric.append(pm)
    # Preserve legacy scalar semantics; publish health separately for new policies.
    now = time.time()
    probe_health = {'ok': probe_ok, 'probe_at_s': now,
                    'success_at_s': now if probe_ok else probe_health['success_at_s'],
                    'rtt_ms': observed_rtt if probe_ok else probe_health['rtt_ms'],
                    'rtt_is_upper_bound': upper_bound if probe_ok else probe_health.get('rtt_is_upper_bound', False)}


@app.route("/qoe/", methods=methods)
@cross_origin()
def qoe():
    event = request.get_json()
    collection = "qoe-{}".format(current_experiment_id)
    db[collection].insert_one(event)

    return jsonify("Succeed")


@app.route("/event/<experimentID>", methods=methods)
@cross_origin()
def playback_event(experimentID):
    global current_experiment_id

    event = request.get_json()
    collection = "events-{}".format(experimentID)
    db[collection].insert_one(event)
    current_experiment_id = experimentID

    return jsonify("Succeed")


@app.route("/metric/<experimentID>", methods=methods)
@cross_origin()
def playback_metric(experimentID):
    global current_experiment_id
    
    metric = request.get_json()
    collection = "metric-{}".format(experimentID)
    db[collection].insert_one(metric)
    current_experiment_id = experimentID

    return jsonify("Succeed")


class StoppableThread(threading.Thread):
    def __init__(self, hostname):
        super().__init__()
        self.hostname = hostname
        self.stop_flag = False

    def run(self):
        addrs = [ str(i[4][0]) for i in socket.getaddrinfo(self.hostname, 80) ]
        if len(addrs) > 0:
            HOST = addrs[0]
        else:
            HOST = self.hostname

        while not self.stop_flag:
            py_ping(hostname=HOST)
            time.sleep(0.1)

    def stop(self):
        self.stop_flag = True


@app.route("/ping/<hostname>", methods=methods)
@cross_origin()
def start_ping(hostname):
    global ping_thread
    ping_thread = StoppableThread(hostname)
    ping_thread.start()
    return jsonify("Succeed")


@app.route("/ping/stop", methods=methods)
@cross_origin()
def stop_ping():
    global ping_metric
    global count
    if ping_thread:
        ping_thread.stop()
        ping_thread.join()
        ping_metric.clear()
        count = 0
        print("stopped")
    
    return jsonify("Succeed")


@app.route("/ping", methods=["GET"])
@cross_origin()
def get_ping_stats():
    if len(ping_metric) > 0:
        return jsonify(ping_metric[-1].rtt)
    else:
        return jsonify(0)


@app.route('/ping/details', methods=['GET'])
@cross_origin()
def get_ping_details():
    snapshot = dict(probe_health)
    now = time.time()
    snapshot['server_at_s'] = now
    snapshot['age_s'] = None if snapshot['success_at_s'] is None else max(0, now-snapshot['success_at_s'])
    snapshot['valid'] = bool(snapshot['ok'] and snapshot['age_s'] is not None and snapshot['age_s'] < 3)
    return jsonify(snapshot)
    

def print_ping_stats():
    print("Latest 10 latency tests results:")
    pprint(ping_metric[-10:])


schedule.every(10).seconds.do(print_ping_stats)


def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(0.1)


if __name__ == "__main__":
    if not INTERFACE:
        print("Environment variable INTERFACE is empty, default interface will be used for latency tests")

    print("Latency tests interval: {}s".format(PING_INTERVAL))

    p = threading.Thread(target=schedule_thread)
    p.start()

    app.run(host="0.0.0.0", port=8000)
