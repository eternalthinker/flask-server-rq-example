
# flask-server-rq-example  
A flask server, which uses RQ, to perform video editing jobs with moviepy and PIL

**Notes:**
- The videogen module expects ./images/ directory and a ./BaseVideo.flv
- The RQ implementation in the server expects a Redis instance running at port 5001
- Works with the (Finagle + Java) master server implementation at: https://github.com/eternalthinker/finagle-java-example-master-slave

