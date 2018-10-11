#!/bin/bash

echo "Setting up sequencers.."

sequencer_nodes=(s-1)

#File system is updated
#/tmp/DANS/setup/./update_fs.sh

for s in ${sequencer_nodes[*]}; do
    ./kill_and_start_sequencers.sh "$s"
done

echo "Sequencers successfully setup"
