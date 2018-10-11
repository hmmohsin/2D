cp ../bin/controller_client .

LOAD=800
NUMFLOWS=30000
SEED=7231

echo "Running 2D with controller"
./controller_client -b ${LOAD} -c cache_config.txt -n ${NUMFLOWS} -z 3 -seq 0 -l CACHE_Online -s ${SEED}
