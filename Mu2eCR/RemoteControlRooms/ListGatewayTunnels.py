import subprocess
import sys
from Connections import connections as conns

def ListOpenConn(user, host):

  print "ssh","%s@%s"%(user,host),"/usr/bin/python","/home/novadaq/DAQ-gateway/NovaControlRoom/scripts/VNCPortForwarding.py","-l","all"
  # Could be the case that you don't have permissions to ssh
  try:
    return_val = subprocess.check_output(["ssh","%s@%s"%(user,host),"/usr/bin/python","/home/novadaq/DAQ-gateway/NovaControlRoom/scripts/VNCPortForwarding.py","-l","all"])
  except:
    sys.exit()
  
  # Turn the result into a list and remove any empty elements
  return_list = filter(None, return_val.split('\n'))
  
  formatted_list = []
  for tunnel in return_list:
      formatted_list.append((tunnel.split()[3], int(tunnel.split()[1])))
  
  # Now check which Tunnels are active
  openconns = []
  for con in conns.keys():
      if conns[con] in formatted_list:
        openconns.append(con)
  
  if openconns:
    print "Tunnels exist on %s for"%(host)
    for con in openconns:
      print con
  else:
    print "There are no open tunnels on %s"%(host)
  return openconns


if __name__ == "__main__":
  ListOpenConn("novadaq", "novadaq-far-gateway-01")
