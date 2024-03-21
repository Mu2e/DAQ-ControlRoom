#!/bin/bash
#source ~/.bashrc
#
# Set the principal name to use and the keytab
# that contains the principal
pname="dune-controlroom-fnal/dune/dune-cr-01@FNAL.GOV"
keytab="dune-controlroom-fnal.keytab"
keytabpath="$HOME/.krb5"
#
#
CRPATH="../Base/"
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#source ${DIR}/SetupROCOptions.sh

# Get the ticket using the keytab

# This is the Linux version
#kinit -5 -F -A -k -t $HOME/.krb5/$keytab $pname 2>/dev/null

# This is the OSX version
if [[ $TERM_PROGRAM == "Apple_Terminal" ]]; then
    echo "Using Apple Kerberos"
    kinit -f -A -k -t $keytabpath/$keytab $pname &> /dev/null
else
    # This is the Linux version 
    kinit -5 -F -A -k -t $keytabpath/$keytab $pname 2>/dev/null 
fi

#
# Verify that the ticket is in place
#klist

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
