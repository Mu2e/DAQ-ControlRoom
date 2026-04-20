#!/bin/sh
# setup of local options and paths for ROC script functions
#
# location of hashed passwordfile for control room VNC sessions
export NOVACRPWDFILE=/home/novashift/.vnc/novacrpwdfile
# location of NovaRemoteControlRooms package (where installed from CVS)
export NOVARCRPATH=/home/novashift/NovaCR/NovaRemoteControlRooms
# location of NovaControlRoom package (separate package installed from CVS)
export NOVACRSCRIPTSPATH=/home/novashift/NovaCR/NovaControlRoom/scripts
# List of VNC options for you local control room's taste.  Just space 
# delimit list of vnc options for your version of the VNC viewer.
export NOVARCRVNCOPTIONS="-geometry=1200x1350 RemoteResize=0"
# where to find your kerberos config.  (Needed in GetTickets, probably)
#export KRB5_CONFIG=~/.krb5/krb5.conf
