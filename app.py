import os
import threading
import json
#from PIL import Image

from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue, Worker
from rq.registry import FinishedJobRegistry
import requests

from videogen import generate_video


app = Flask(__name__)
#export APP_SETTINGS="config.DevelopmentConfig"
#app.config.from_object(os.environ['APP_SETTINGS'])

IMAGE_PATH = "."
#background_image = Image.open("IMAGE_PATH + "/" + transp_edited.png")

redis_conn = Redis(port=5001)
videoq = Queue('videos', connection=redis_conn)
fin_registry = FinishedJobRegistry(connection=redis_conn, name='videos')

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
                videoq.enqueue(generate_video, jobid)
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
        except Exception as e:
            print "Connection error : Master unavailable"

    threading.Timer(5.0, pollresults).start()


if __name__ == '__main__':
    threading.Timer(5.0, pollresults).start()
    app.run(debug=False)
    #app.run(host='0.0.0.0')
