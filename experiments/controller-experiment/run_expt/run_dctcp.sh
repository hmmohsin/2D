cp ../bin/controller_client .
cp ../bin/new_client .

LOAD=800
NUMFLOWS=5000
SEED=7231

echo "Running 2D with controller"
./controller_client -b ${LOAD} -c dctcp_config.txt -n ${NUMFLOWS} -z 3 -seq 0 -l dctcp_fct -s ${SEED}
