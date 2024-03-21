#!/bin/zsh
#
# This script sets up the tunnels for the control room
# to connect to VNC sessions running on different hosts
# within the DAQ environment 
defaultuser="mu2eshift"
defaulthost="mu2edaq-gateway.fnal.gov"
defaultportstart=5951
defaultports=5
killflag=0

# Start with some default port numbers
start_port=${defaultportstart}
numports=${defaultports}
end_port=$((start_port + $numports))

# Set the host and user that are hosting the VNC Servers
vnchost=$defaulthost
vncuser=$defaultuser

##################################
# Check command line for options
while getopts 'h:u:p:n:k' flag
do
    case "${flag}" in
        h) vnchost=${OPTARG};;
        u) vncuser=${OPTARG};;
        p) start_port=${OPTARG};;
        n) numports=${OPTARG};;
        k) killflag=1;;
    esac
done

##########################
# If the number of ports was set we need
# to reset the port range
end_port=$((start_port + $numports))

#echo "Host: $vnchost"
#echo "User: $vncuser"
#echo "Port: $start_port"
#echo "End Port: $end_port"
#echo "Num: $num"

###################################
# Check for a valid Kerberos ticket
# 
echo "Checking for Kerberos Ticket"
`klist --test`
ticket=$?
if [ $ticket -ne 0 ]; then 
   echo "No Kerberos Ticket found -- Please obtain a valid ticket"
   # We bail out since we don't have a valid ticket
   exit 1
else
   echo "Ticket Found"
fi
#################################

#################################
# If we are killing off tunnels
# we execute this block

#################################

#################################
# Loop over the port range and open the SSH tunnels 
# for the forwarded ports for VNC
for i in {$start_port..$end_port}
do
    echo -n  "Starting Tunnel to $vnchost on port $i"
    ssh -S /tmp/ssh-ctrl-${vnchost}-${i} -L ${i}:localhost:${i} -N -f -l $vncuser $vnchost
    if [ $? -eq 0 ]; then
        echo " - Done"
    else
        echo "- Fail"
    fi
done
#
##################################
