#!/bin/bash

#used to copy files to all nodes
nodes=(s-1 s-2)
echo "Making Client-Server"
cd /users/hmmohsin/TrafficGenerator-master
make clean
make

#File system is updated
#/tmp/DANS/setup/./update_fs.sh

for n in ${nodes[*]}; do
    ssh -o StrictHostKeyChecking=no $n "/users/hmmohsin/TrafficGenerator-master/setup/./copy_all.sh"
    echo $n" done"
done
