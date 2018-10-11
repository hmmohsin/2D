#!/bin/bash

if [ ! -d "/tmp/2D" ]; then
    mkdir -p /tmp/2D
fi

sudo killall server
sudo killall sequencer
sudo killall exp_client
sudo killall client
sudo killall new_client
sudo killall baraat_client

cp /users/hmmohsin/TrafficGenerator-master/bin -r /tmp/2D
cp /users/hmmohsin/TrafficGenerator-master/setup -r /tmp/2D
cp /users/hmmohsin/TrafficGenerator-master/conf -r /tmp/2D
cp /users/hmmohsin/TrafficGenerator-master/run_expt -r /tmp/2D
