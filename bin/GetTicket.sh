#!/bin/bash
source ~/.bashrc
#
# Set the principal name to use and the keytab
# that contains the principal
pname="dune-controlroom-fnal/dune/dune-cr-01@FNAL.GOV"
keytab="dune-controlroom-fnal.keytab"
#
#
CRPATH="../Base/"
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/SetupROCOptions.sh

# Get the ticket using the keytab
kinit -5 -F -A -k -t $HOME/.krb5/$keytab $pname 2>/dev/null

#
# Verify that the ticket is in place
klist

# Dipslay a graphic to show key was obtained
#display $CRPATH/graphics/ticket.jpg &
#kvpid=$!

# Leave it up for 2 seconds
#sleep 2

# Kill graphic
#kill $kvpid >& /dev/null
#
# 
########################
