################################## Imports
import Tools
import sys, cPickle, subprocess, time, os, getpass
################################## Options
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-i", "--initalise",      help="first time port forwarding setup",    action="store",      type=str,  dest="init",    default=False)
parser.add_option("-r", "--reset",          help="reset all ssh tunnels",               action="store_true",            dest="reset",   default=False)
parser.add_option("-l", "--list",           help="list all open ssh tunnels",           action="store",      type=str,  dest="list",    default=False)
parser.add_option("-f", "--find_open_port", help="find an open port",                   action="store_true",            dest="find",    default=False)
parser.add_option("-p", "--port",           help="local port to spawn process on",      action="store",      type=int,  dest="port",    default=False)
parser.add_option("-u", "--username",       help="User name for use with ssh",          action="store",      type=str,  dest="username",default=False)
parser.add_option("-v", "--verbose_mode",   help="turn on verbose mode",                action="store_true",            dest="verbose", default=False)
(options, args) = parser.parse_args()
if options.verbose:
    print "VNCPF: --- VNCPortForwarding"
    print "VNCPF:     Configuration options:"
    print "VNCPF:         initalise mode:    ",options.init
    print "VNCPF:         port:              ",options.port
    print "VNCPF:         reset mode:        ",options.reset
    print "VNCPF:         list mode:         ",options.list
    print "VNCPF:         find mode:         ",options.find
    print "VNCPF:         username:          ",options.username
    print "VNCPF:         verbose mode:      ",options.verbose
if not (options.init or options.reset or options.list or options.find):
    print "VNCPF: No valid run mode given: exiting, use -h option for usage instructions and help"
    sys.exit()
################################## Configurations
# A dictionary of connections
#   the key is the detector-station 
#   the value is (the host, the port on the CR machine)
# want this to be specified in a configuration file
# can be extended later on.
from Connections import connections, displays
################################## Reset mode
#if options.reset or options.init:
if options.reset:
    # this will detect all open ssh tunnels and kill them
    if options.verbose: print "VNCPF: --- Resetting"
    Tools.ResetSSHTunnels(verbose=options.verbose)
################################## Initalise mode
if options.init:
    if options.verbose: print "VNCPF: --- Initalising, connection: %s"%options.init
    if ((options.init != "all") and (options.init not in connections.keys())):
        print "No configuration data available for given connection: %s, available connections: all,"%options.init
        for con in connections.keys():
            print "\t%s"%con
        sys.exit()
    if (options.init == "all"):
        to_establish = connections.keys()
    else:
        to_establish = [options.init]
    for connection in to_establish:
        host,port = connections[connection]
        if not options.username: username = displays[connection]
        else:                    username = options.username
        if options.verbose: print "VNCPF:     setting up connection %s, for host %s, username: %s, remote port: %i"%(connection, host, username, port)
        try:
            mapped_port = Tools.EstablishSSHTunnel(host, port, username, local_port=options.port, verbose=options.verbose)
            if options.verbose: print "VNCPF:     connection for host %s, remote port: %i, mapped to local port: %i"%(host, port, mapped_port)
            else:               print "%02d"%(mapped_port-5900)
        except:
            print "VNCPF: FAILED connection for host %s, remote port: %i"%(host, port)
################################## List mode
if options.list:
    if options.verbose: print "VNCPF: --- Listing, connection: %s"%options.list
    if ((options.list != "all") and (options.list not in connections.keys())):
        print "No configuration data available for given connection: %s, available connections:\n\tall"%options.list
        for con in connections.keys():
            print "\t%s"%con
        sys.exit()
    if options.list == "all":
        # this will detect and list all open ssh tunnels
        Tools.ListSSHTunnels(verbose=options.verbose)
    else:
        # this will detect and list the configuration for a given connection
        local_port = Tools.ListSSHTunnels(connection=connections[options.list],verbose=options.verbose)
        if options.verbose: print "VNCPF:     local port: %i"%local_port
        else:               print local_port
################################# Find mode
if options.find:
    # this will detect an open port
    if options.verbose: print "VNCPF: --- Find"
    free_port = Tools.FindFreePorts(5900,6000)
    if options.verbose: print "VNCPF:     found an open port: %i"%free_port
    else: print free_port

if options.verbose: print "VNCPF: done"
