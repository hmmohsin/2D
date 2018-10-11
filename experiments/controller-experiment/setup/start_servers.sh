#!/bin/bash

echo "Setting up servers.."

server_nodes=(s-1)

#File system is updated
#/tmp/DANS/setup/./update_fs.sh

for s in ${server_nodes[*]}; do
    ./kill_and_restart_server.sh "$s"
done

echo "Servers successfully restarted"
