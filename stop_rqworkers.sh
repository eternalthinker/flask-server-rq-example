# Stopping rqworkers

for i in `pgrep worker`
do
	kill -9 $i
done