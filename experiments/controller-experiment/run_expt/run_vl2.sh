cp ../bin/controller_client .

LOAD=800
NUMFLOWS=20000
SEED=7231

echo "Running 2D with controller"
./controller_client -b ${LOAD} -c vl2_config.txt -n ${NUMFLOWS} -z 3 -seq 0 -s 7231 -l VL2_Online
