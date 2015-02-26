from redis import Redis
from rq import Queue
from rq.registry import FinishedJobRegistry
from videogen import videogen
import time



redis_conn = Redis(port=5001)
videoq = Queue('medium', connection=redis_conn)
fin_registry = FinishedJobRegistry(connection=redis_conn, name='medium')

jobid = 1024
job = videoq.enqueue(videogen, jobid)

while not job.is_finished:
    time.sleep(2)
    print job.result



    
