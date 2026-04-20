#!/bin/bash
source ~/.bashrc

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/SetupROCOptions.sh

#kinit -f -A -k -t <path-to-keytab>/nova-controlroom-indiana.keytab nova-controlroom-umn/nova/nova-daq-01.fnal.gov@FNAL.GOV
kinit -f -l 26h -A -k -t ~/.krb5/nova-principle.keytab novadaq/nova/novadaq-ctrl-master.fnal.gov@FNAL.GOV

# Graphic to show key was obtained
display $NOVARCRPATH/graphics/ticket.jpg &

# Pop up graphic
kvpid=$!

# Leave it up for 2 seconds
sleep 2

# Kill graphic
kill $kvpid >& /dev/null
