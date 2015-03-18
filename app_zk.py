#!/usr/bin/env python

import threading
import json
#from PIL import Image

from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
from rq.registry import FinishedJobRegistry
import requests
from kazoo.client import KazooClient
from kazoo.client import KazooState
from kazoo.protocol.states import EventType

from videogen import generate_video


app = Flask(__name__)
#export APP_SETTINGS="config.DevelopmentConfig"
#app.config.from_object(os.environ['APP_SETTINGS'])

redis_conn = Redis(port=5001)
videoq = Queue('videos', connection=redis_conn)
fin_registry = FinishedJobRegistry(connection=redis_conn, name='videos')


# === ZooKeeper definitions
def self_listener(state):
    pass


def watch_master(event):
    pass


SERVER_PORT = 5010

zk = KazooClient(hosts='localhost:2181')
zk.start()
zk.add_listener(self_listener)
data = {}
data["serviceEndpoint"] = { "host": "localhost", "port": SERVER_PORT }
data["status"] = "ALIVE"
data["shard"] = 1
data["additionalEndPoints"] = []
jdata = json.dumps(data)
zk.create(path="/videogen/slaves/member_", value=jdata, sequence=True, makepath=True)
# Put a watch on znode
#children = zk.get_children("/videogen/master", watch=watch_master)
# === End of ZooKeeper definitions


@app.route('/genvid/', methods=['GET', 'POST'])
def genvid():
    """Handler for video generation commands from master"""
    error = None
    results = {}

    if request.method == "GET":
        # Get url that the user has entered
        try:
            cid = request.args.get('cid', 1)
            pid = request.args.get('pid', 1)
            results['cid']=cid
            results['pid']=pid
        except:
            error =  "Unable to get URL. Please make sure it's valid and try again." 

    if request.method == "POST":
        # Parse JSON request
        jreq = request.json
        print "Request received: %s" % jreq
        if jreq.has_key("type"):
            reqtype = jreq["type"]
            # Parse job command and queue video generation
            if reqtype == "command":
                jobid = jreq["job_id"]
                #videoq.enqueue(generate_video, jobid)
                results["job_id"] = jobid
                results["type"] = "ack"

    if error is not None: 
        return error 
    return jsonify(results)


def pollresults():
    """Periodically retrieve finished jobs and notify master"""
    print "Polling for job results.."
    fin_ids = fin_registry.get_job_ids()
    if len(fin_ids) > 0:
        result = {}
        reports = []
        for jid in fin_ids:
            job = videoq.fetch_job(jid)
            reports.append(job.result)
            fin_registry.remove(job)
        result["reports"] = reports
        result["type"] = "reports"
        url = "http://localhost:8000/"
        headers = {'content-type': 'application/json'}
        try:
            response = requests.post(url, data=json.dumps(result), headers=headers)
            print response.json()
        except:
            print "Connection error : Master unavailable"

    threading.Timer(5.0, pollresults).start()


if __name__ == '__main__':
    #threading.Timer(5.0, pollresults).start()
    app.run(port=SERVER_PORT, debug=False)
    #app.run(host='0.0.0.0')
