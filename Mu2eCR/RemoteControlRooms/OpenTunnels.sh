#!/bin/bash

detector=$1
user=$2
gateway=$3

ssh -tt -Y $user@$gateway "xterm -e 'cd /home/novadaq/DAQ-gateway/NovaControlRoom/scripts; python VNCPortForwarding.py -i $1 -u $2 -v; python VNCPortForwarding.py -l all; bash' "
