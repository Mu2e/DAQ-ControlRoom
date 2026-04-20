################################## Imports
import Tools
import sys, cPickle, subprocess, getpass
################################## Options
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-d", "--detector",       help="Detector to connect to",      action="store",      type=str, dest="detector", default=False)
parser.add_option("-D", "--dynamic_mode",   help="Make a new gateway tunnel",   action="store_true",           dest="dynamic",  default=False)
parser.add_option("-b", "--batch_mode",     help="Establish ssh tunnels, but do not launch VNCViewer",\
                                                                                action="store_true",           dest="batch",    default=False)
parser.add_option("-u", "--username",       help="User name for use with ssh",  action="store",      type=str, dest="username", default="novadaq")
parser.add_option("-g", "--gateway",        help="Gateway machine",             action="store",      type=str, dest="gateway",  default="novatest01.fnal.gov")
parser.add_option("-V", "--view_only",      help="Attach vnc in view only mode",action="store_true",           dest="view",     default=False)
parser.add_option("-v", "--verbose_mode",   help="Turn on verbose mode",        action="store_true",           dest="verbose",  default=False)
(options, args) = parser.parse_args()
if options.verbose:
    print "AVNCS: --- AttachVNCSession:"
    print "AVNCS:     Configuration options:"
    print "AVNCS:         detector:          ",options.detector
    print "AVNCS:         dynamic mode:      ",options.dynamic
    print "AVNCS:         batch mode:        ",options.batch
    print "AVNCS:         username:          ",options.username
    print "AVNCS:         gateway:           ",options.gateway
    print "AVNCS:         view only:         ",options.view
    print "AVNCS:         verbose mode:      ",options.verbose
if not options.detector:
    print "AVNCS: No detector given: exiting, use -d option to provide this. for usage instructions use -h"
    sys.exit()
################################## Configurations, needed for static connection mode
# A dictionary of connections
#   the key is the detector-station 
#   the value is (the host, the port on the CR machine)
# want this to be specified in a configuration file
# can be extended later on.
from Connections import connections
################################## attach mode
if options.detector:
    # this will attach the requested VNC session
    if options.verbose: print "AVNCS: --- Attaching VNC session for detector: %s, gateway: %s, user: %s"%(options.detector,options.gateway,options.username)
    # setup gateway
    if options.dynamic:
        if options.verbose: print "AVNCS:     dynamic mode, asking gateway to set up a new tunnel"
        gateway_port   = Tools.SetupGatewayTunnel(options.gateway, options.detector, options.username, verbose=options.verbose)
    else:
        if options.verbose: print "AVNCS:     static mode, asking gateway for static tunnel port"
        gateway_port   = Tools.FindGatewayTunnel(options.gateway, options.detector, options.username, verbose=options.verbose)
        if gateway_port is False: sys.exit()
    # setup local ssh tunnel
    if options.verbose: print "AVNCS:     creating local ssh tunnel to gateway port: %i"%gateway_port
    local_port     = Tools.EstablishSSHTunnel(options.gateway, gateway_port, options.username, starting_port=gateway_port+1, verbose=options.verbose)
    if options.verbose: print "AVNCS:     connection for gateway %s, remote port: %i, mapped to local port: %i"%\
                            (options.gateway, gateway_port, local_port)
    # start VNC
    if not options.batch:
        if options.verbose: print "AVNCS:     Initalising VNC viewer"
        attach_vnc     = Tools.AttachVNC(local_port,view_only=options.view) 
    else:
        print local_port
    
if options.verbose: print "AVNCS: done"
