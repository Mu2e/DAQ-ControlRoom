import subprocess
import os
import sys
import time
import getpass
import socket

local_path = "/home/novadaq/DAQ-gateway/NovaControlRoom/scripts"

def FindGatewayTunnel(host, detectorID, username, verbose=False):
    if verbose: print "tools: --- FindGatewayTunnel, on host: %s to detector: %s"%(host, detectorID)
    to_run = ["ssh", "%s@%s"%(username, host), "python %s/VNCPortForwarding.py -l %s"%(local_path,detectorID)]
    #if verbose: to_run[2] = to_run[2]+" -v"
    #print to_run    
    #print "tools: beginning process"
    process = subprocess.Popen(to_run, stdout=subprocess.PIPE)
    #print "tools:     comminicating"
    process.wait()
    exitcode = process.returncode
    if exitcode:
        print "tools: gateway ssh tunnel finding threw an error, check stdout/stderr, exiting"
        sys.exit()
    #print "tools:     done: %i"%process.returncode
    output = process.stdout.read()
    if verbose: print "tools:     got remote port: ",output.strip("\n")
    #print output.strip("\n")
    remote_port = output.strip("\n")
    if remote_port == "None":
        # if we got here then there is no open connection
        # therefore we return an error code or throw an exception
        print "tools:     No open connection to machine: %s, on gateway: %s found.\n\tIf you are trying to connect to static tunnels on the gateway, check that these have been started.\n\tIf you wish to dynamically establish tunnels on the gateway (not recommended) use the option -D"%(detectorID,host)
        return False
    return int(remote_port)

def AttachVNC(local_port, view_only=False):
    to_run = ["vncviewer", "-Shared", ":%02d"%(local_port-5900)]
    if view_only: to_run.insert(2, "-ViewOnly")
    #print to_run
    process = subprocess.Popen(to_run)

def SetupGatewayTunnel(host, detectorID, username, verbose=True):
    if verbose: print "tools: --- SetupGatewayTunnel"
    remote_port = FindRemoteFreePort(host, username, verbose=verbose)
    if verbose: print "tools:     remote free port found: %i"%remote_port
    EstablishRemoteSSHTunnel(host, detectorID, remote_port, username, verbose=verbose)
    return remote_port

def EstablishRemoteSSHTunnel(host, detectorID, remote_port, username, verbose=False):
    if verbose: print "tools: --- EstabishRemoteSSHTunnel, host: %s, detectorID: %s, remote port: %i"%(host,detectorID,remote_port)
    to_run = ["ssh", "-f","%s@%s"%(username, host), "python ~/DAQ/VNCPortForwarding.py -i %s -p %i"%(detectorID,remote_port)]
    #if verbose: to_run[2] = to_run[2]+" -v"
    process = subprocess.Popen(to_run)
    if verbose: print "tools: -------- spawned process, waiting for it to complete"
    time.sleep(10)
    if verbose: print "tools: -------- confirming process spawned"
    if (not ConfirmRemoteSSHTunnel(host, remote_port, detectorID, username, verbose=verbose)):
        print "tools: Confirmation of remote ssh tunnel failed, exiting"
        raise
        #sys.exit()
    
def ConfirmRemoteSSHTunnel(host, remote_port, detectorID, username, verbose=False):
    if verbose: print "tools: --- ConfirmRemoteSSHTunnel: %s:%i"%(host,remote_port)
    to_run = ["ssh", "%s@%s"%(username,host), "python ~/DAQ/VNCPortForwarding.py -l %s"%detectorID]
    if verbose: to_run[2] = to_run[2]+" -v"
    #print to_run    
    #print "tools: beginning process"
    process = subprocess.Popen(to_run, stdout=subprocess.PIPE)
    for i_t,tunnel in enumerate(process.stdout.read().split("\n")):
        if verbose: print "tools:     tunnel[%i]: "%i_t,tunnel
        if "%s"%remote_port in tunnel:
            if verbose: print "tools:     confirmed"
            return True
    return False
        
def FindRemoteFreePort(host,username,verbose=False):
    if verbose: print "tools: --- FindRemoteFreePort, host: %s"%host
    #### Find a remote open port
    to_run = ["ssh", "%s@%s"%(username, host), "python ~/DAQ/VNCPortForwarding.py -f"]
    #if verbose: to_run[2] = to_run[2]+" -v"
    #print to_run    
    #print "tools: beginning process"
    process = subprocess.Popen(to_run, stdout=subprocess.PIPE)
    #print "tools:     comminicating"
    process.wait()
    #print "tools:     done: %i"%process.returncode
    output = process.stdout.read()
    return int(output.strip("\n"))

def FindFreePorts(start,end,verbose=True):
    for i in range(start,end):
        try:
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = soc.connect_ex(("", i))
            if(result == 0):
                soc.close()
            else:
                soc.close()
                return i
        except :
            print "ERROR: Failed to scan in range specified"

def ListSSHTunnels(connection=False, verbose=True):
    if verbose: print "tools: --- List SSH Tunnels, specific connection: ",connection
    process = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    for line in (process.stdout.read().split("\n")):
        if "ssh -L" not in line: continue
        if "localhost" not in line: continue
        #if (line.split()[0] != "novadaq"): continue
        if verbose: print "tools:     OpenSSHTunnel:\n",line
        pid = line.split()[1]
        local_port = line.split()[12].split(":")[0]
        remote_port = line.split()[12].split(":")[2]
        user = line.split()[16]
        machine = line.split()[17]
        if connection:
            if (machine != connection[0]):          continue
            if (int(remote_port) != connection[1]): continue
            if ((len(connection)==3) and (int(local_port) != connection[2])): continue
            if verbose: print "tools:     Matching SSHTunnel:\n\t\tlocal port:  %s\n\t\tremote port: %s\n\t\tuser:        %s\n\t\tmachine:     %s"%\
                (local_port, remote_port, user, machine)
            return int(local_port)
        if verbose:
            print "tools:     SSHTunnel:\n\tlocal port:  %s\n\tremote port: %s\n\tuser:        %s\n\tmachine:     %s"%\
            (local_port, remote_port, user, machine)
        else:
            print "%s %s %s %s"%(local_port, remote_port, user, machine)
    if connection:
        # if we got here then there is no open connection
        # therefore we could return an error code or throw an exception
        if verbose: print "tools: No open connection to machine: %s, port: %i found"%(connection[0],connection[1])

def ResetSSHTunnels(verbose=True):
    if verbose: print "tools: --- Reset SSH Tunnels"
    open_tunnels = DetectOpenSSHTunnels(verbose=verbose)
    if verbose: print "tools:     %i open tunnels found"%len(open_tunnels)
    for open_tunnel in open_tunnels:
        #print "kill %s"%open_tunnel
        os.system("kill %s"%open_tunnel)
        pass
    if verbose: print "tools:     %i open tunnels closed"%len(open_tunnels)

def DetectOpenSSHTunnels(verbose=True):
    process = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    pids = []
    for line in (process.stdout.read().split("\n")):
        if "ssh -L" not in line: continue
        if "localhost" not in line: continue
        #if (line.split()[0] != "novadaq"): continue
        if verbose: print "tools:     OpenSSHTunnel:\n",line
        pid = line.split()[1]
        pids.append(pid)
    return pids
    
def EstablishSSHTunnel(target_host, target_port, username, local_port=False, starting_port=5900, ending_port=6000,verbose=True):
    if verbose:
        print "tools: --- Establish SSH Tunnel"
        print "tools:     target host:   %s"%target_host
        print "tools:     target port:   %i"%target_port
        print "tools:     local port:    %i"%local_port
        print "tools:     starting port: %i"%starting_port
        print "tools:     user:          %s"%username
    established = False
    if local_port: starting_port = local_port
    while not established:
        if verbose: print "tools:        - checking status of port %i"%starting_port
        #free_port = CheckPort(starting_port, verbose=verbose)
        free_port = FindFreePorts(starting_port, ending_port, verbose=verbose)
        if free_port:
            if verbose: print "tools:        - free port found: %i"%free_port
            if verbose: print "tools:        - establishing ssh tunnel"
            process = subprocess.Popen(["ssh", "-L", 
                                        "%i:localhost:%i"%(free_port,target_port),
                                        "-N", "-f", "-l", username, target_host],
                                        )
            process.communicate()
            if verbose: print "tools:        - confirming tunnel established"
            exitcode = process.returncode
            if exitcode:
                print "tools: ssh tunnel creation threw an error, check stdout/stderr, exiting"
                sys.exit()
            # confirm tunnel creation
            confirmed_port = ListSSHTunnels((target_host,target_port,free_port), verbose=verbose)
            if confirmed_port != free_port:
                print "tools: Failure to open tunnel on identified free port %i to target host: %s, target port: %i"%\
                        (free_port, target_host, target_port)
                print "tools: Attempted confirmation got port: ",confirmed_port
                print "tools: exiting"
                sys.exit()
            if verbose: print "tools:        - established ssh tunnel, pid: %i"%process.pid
            established = True
        if (starting_port >= ending_port):
            print "tools: No open ports found in defined range (%i-%i), exiting"%(starting_port,ending_port)
            sys.exit()
        starting_port+=1           
    
    return free_port

def CheckPort(port_number, verbose=False):
    if verbose: print "tools: --- Check Port: %i"%port_number
    process = subprocess.Popen(["netstat","-na"], stdout=subprocess.PIPE)
    if "%i "%port_number in process.stdout.read():
        if verbose: print "tools:     port in use"
        return False
    else:
        if verbose: print "tools:     port free"
        return port_number
