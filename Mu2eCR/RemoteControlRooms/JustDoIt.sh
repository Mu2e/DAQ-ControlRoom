#!/bin/bash
#set -x
#notify-send --expire-time=10000 ' Workin g...  Give it ten or twenty seconds to check for tunnels and open a VNC viewer session'  --icon=network-transmit
# 20170424 -- LMM
# Tested on MacOS.  Modified conditional to work better.
# 20170411 -- LMM
# Added lockfile checking and notifications.
# Notifications should work on SL and ubuntu with libnotify.
# Might work on MAC too, but untested use of notification facility there.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/SetupROCOptions.sh
export PYTHONPATH=${NOVACRSCRIPTSPATH}/

# Check for a lockfile
if [ -e $NOVARCRPATH/JustDoIt.lock ] ; then
    if [ `which notify-send` ] ; then
	notify-send " Lockfile Found in $NOVARCRPATH/JustDoit.lock belonging to PID `cat  $NOVARCRPATH/JustDoIt.lock` -- Another JustDoIt may be running. Wait for it to finish or remove the lockfile and try again if something went wrong. "
    elif [ `which osascript` ] ; then
	osascript -e 'display notification "JustDoIt.lock file found in $NOVARCRPATH -- Another JustDoIt may be running.  " with title "JustDoIt"'
	sleep 8
	osascript -e 'display notification "Wait for it to finish or remove the lockfile and try again if something went wrong" with title "JustDoIt"'
    fi
    exit
else
# Create lockfile
    echo $$ > $NOVARCRPATH/JustDoIt.lock
    if [ `which notify-send` ] ; then
	notify-send --expire-time=10000 ' Working... Give it ten or twenty seconds to check for tunnels and open a VNC viewer session -- Locking out other JustDoIt requests until it finishes ' --icon=network-transmit
    elif [ `which osascript` ] ; then
	osascript -e 'display notification "-- Locking out other JustDoIt requests until it finishes " with title "JustDoIt" '
	sleep 3
	osascript -e 'display notification " Working... Give it ten or twenty seconds to check for tunnels and open a VNC viewer session " with title "JustDoIt" '
    fi
fi

case "$1" in
    "FarDet-1")
	user="novacr01"
	gateway="novadaq-far-gateway-01.fnal.gov"
	;;
    "NearDet-1")
	user="novacr01"
	gateway="novadaq-near-gateway-01.fnal.gov"
	;;
    "FarDet-2")
	user="novacr02"
	gateway="novadaq-far-gateway-01.fnal.gov"
	;;
    "FarDet-3")
	user="novacr03"
	gateway="novadaq-far-gateway-01.fnal.gov"
	;;
    "NearDet-2")
	user="novacr02"
	gateway="novadaq-near-gateway-01.fnal.gov"
	;;
    "FermiCR-3")
	user="novacr03"
	gateway="novadaq-near-gateway-01.fnal.gov"
	;;
    "NearDet-3")
  user="novacr03"
  gateway="novadaq-near-gateway-01.fnal.gov"
  ;;
    "TestBeam-1")
  user="novacr01"
  gateway="novadaq-near-gateway-01.fnal.gov"
  ;;
    "TestBeam-2")
  user="novacr02"
  gateway="novadaq-near-gateway-01.fnal.gov"
  ;;
    "TestBeam-3")
  user="novacr03"
  gateway="novadaq-near-gateway-01.fnal.gov"
  ;;
    "TestBeam-4")
  user="novadaq"
  gateway="novadaq-near-gateway-01.fnal.gov"
  ;;
    *)
	user="novadaq"
	gateway="novadaq-near-gateway-01.fnal.gov"
	;;
esac

echo python ${NOVARCRPATH}/OneButton.py -i $1 -g $gateway -u $user -v
python ${NOVARCRPATH}/OneButton.py -i $1 -g $gateway -u $user -v

#check for a lockfile, remove if it exists
if [ -e $NOVARCRPATH/JustDoIt.lock ] ; then
    if [  `which notify-send` ] ; then
	notify-send ' Removing lockfile '
    elif [  `which osascript` ] ; then
	osascript -e
 'display notification " Removing Lockfile " with title "JustDoIt" '
    fi
    rm $NOVARCRPATH/JustDoIt.lock
fi
