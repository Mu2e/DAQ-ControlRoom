#!/bin/sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/SetupROCOptions.sh

kill `ps aux | grep 'ssh -[L]' | awk '{print $2}'`

# Graphic to show key was obtained
display $NOVARCRPATH/graphics/PortsReset.png &

# Pop up graphic
kvpid=$!

# Leave it up for 2 seconds
sleep 2

# Kill graphic
kill $kvpid >& /dev/null
