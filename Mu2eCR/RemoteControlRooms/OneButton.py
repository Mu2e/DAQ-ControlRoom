# This python script should be the one button solution for any shifter in a 
# remote control room.  It will figure out if there is an Open Tunnel on a 
# gateway machine for the vncserver the shifter is trying to connect to.  
# If there is, great connect to that one, if there isn't create a new one.
# 
# An extension could be checking local tunnels too, but that requires more of a rewrite

import Tools
from Connections import connections
#import ListGatewayTunnels as OT
from optparse import OptionParser
import subprocess, sys

# Setup a parser, overkill here, but the right thing to do
parser = OptionParser()
parser.add_option("-i", "--initalise",      
                  help="Which display to connect to",    
                  action="store",      
                  type=str,  
                  dest="init",    
                  default=False)
parser.add_option("-v", "--verbose_mode",   
                  help="turn on verbose mode",           
                  action="store_true",            
                  dest="verbose", 
                  default=False)
parser.add_option("-u", "--username",       
                  help="User name for use with ssh",  
                  action="store",      
                  type=str, dest="username", 
                  default="novadaq")
parser.add_option("-g", "--gateway",        
                  help="Gateway machine",             
                  action="store",      
                  type=str, 
                  dest="gateway", 
                  default="novatest01.fnal.gov")
parser.add_option("-V", "--view_only",      
                  help="Attach vnc in view only mode",
                  action="store_true",           
                  dest="view",     
                  default=True)
(options, args) = parser.parse_args()

if options.verbose:
  print "OneButton: --- JustDoIt ---"
  print "OneButton:     Configuration options:"
  print "OneButton:	initalise mode:    ",options.init
  print "OneButton:	username:          ",options.username
  print "OneButton:     gateway:           ",options.gateway
  print "OneButton:     view only:         ",options.view
  print "OneButton:	verbose mode:      ",options.verbose

# Bail if a user is passing funny arguments
if not options.init:
  print "OneButton: No valid run mode given: exiting, use -h option for usage instructions and help"
  sys.exit()

# Check that the connection requested is supported
if (options.init not in connections.keys()):
  print "No configuration data available for given connection: %s, available connections: all,"%options.init
  for con in connections.keys():
    print "\t%s"%con
  sys.exit()

# Get the currently open gateway tunnels by running VNCPortForwarding.py on gateway node
#OpenTunnels = OT.ListOpenConn(options.username, options.gateway)

# Get port number for connection from gateway
if options.verbose: print "OneButton:	Asking gateway for static tunnel port"
gateway_port   = Tools.FindGatewayTunnel(options.gateway, options.init, options.username, verbose=options.verbose)

# If the gateway tunnel doesn't exist create Open Tunnel
#if options.init not in OpenTunnels:
if not gateway_port:
  to_run = "$NOVARCRPATH/OpenTunnels.sh %s %s %s"%(options.init,options.username,options.gateway)
  print "OneButton: trying " 
  print to_run
  try:
    subprocess.call(to_run,shell=True)
  except:
    print "Remote command failed"
    print to_run
    sys.exit()
  gateway_port   = Tools.FindGatewayTunnel(options.gateway, options.init, options.username, verbose=options.verbose)


# setup local ssh tunnel
# Checks if local to remote port with correct user is already existing
# If it exists, use that port. If not, it will create a new one.
if options.verbose: print "OneButton:     creating local ssh tunnel to gateway port: %i"%gateway_port
local_port     = Tools.EstablishSSHTunnel(options.gateway, gateway_port, options.username, starting_port=gateway_port+1, verbose=options.verbose)
if options.verbose: print "OneButton:     connection for gateway %s, remote port: %i, mapped to local port: %i"%(options.gateway, gateway_port, local_port)

# start VNC
if options.verbose: print "OneButton:     Initalising VNC viewer"
attach_vnc     = Tools.AttachVNC(local_port,view_only=options.view)
