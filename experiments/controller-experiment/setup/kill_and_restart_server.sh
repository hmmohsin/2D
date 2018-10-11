#!/bin/bash

REMOTE_NODE=$1
ssh  -o "StrictHostKeyChecking no" $REMOTE_NODE 'sudo killall server'
ssh -o "StrictHostKeyChecking no" $REMOTE_NODE 'sudo nohup /tmp/2D/bin/server >& /dev/null &'
