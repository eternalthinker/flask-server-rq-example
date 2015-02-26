# Starting n rqworkers
for i in {1..5}
do
	rqworker --url redis://localhost:5001 videos &
done
