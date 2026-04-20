#!/usr/bin/env python

import sys
import os
import platform
import json
import subprocess
import krb5

#from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QComboBox, QLabel,QVBoxLayout, QCheckBox
#from PyQt6.QtCore import QSize, QTimer
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# Figure out what OS we are on
print(os.name,platform.system(),platform.release())

# Default Renewal Time (in msec)
# Set a 1 hour ticket renew time
renewTime = 1000 * 3600

# Search paths: current working directory, then script's own directory
_script_dir = os.path.dirname(os.path.abspath(__file__))
_search_path = [os.getcwd(), _script_dir]

def find_config(filename):
    for directory in _search_path:
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            return path
    return None

# Look for a default config file in the search path
_defaultConfig_path = find_config('ticket-config.json')
defaultConfig = _defaultConfig_path if _defaultConfig_path else 'ticket-config.json'

# Load the Kerberos principal information from kerb_princ.json
_kerb_princ_path = find_config('kerb_princ.json')
if _kerb_princ_path is None:
    print("Error: kerb_princ.json not found in search path:", _search_path, file=sys.stderr)
    sys.exit(1)
theData = json.load(open(_kerb_princ_path, 'r'))

# Initialize the lists of principals
currentPrincipal ='none'
principalList=[]

# First the current primiary principal (the one that is set)
kerb_context = krb5.init_context()
kerb_cache = krb5.cc_default(kerb_context)

#results = subprocess.run(["klist","--json"],capture_output=True, text=True)
#out = results.stdout
#primeticket = json.loads(out)

# Try and pull the default principal out of the cache list
# it should be listed under the 'principal' key
try:
    cur_princ=krb5.cc_get_principal(kerb_context,kerb_cache)
    currentPrincipal=cur_princ.name.decode()
    # currentPrincipal=primeticket['principal']
except:
    currentPrincipal='none'
    print('Unable to parse initial principal')

# Next we get the full list of Credential Caches that are available
cc_list = krb5.cccol_iter(kerb_context)
for cc in cc_list:
    try:
        p = krb5.cc_get_principal(kerb_context,cc)
        principalList.append(p.name.decode())
        print(p.name)
    except:
        pass
# First get a snapshot of the current state of the ticket
#results = subprocess.run(["klist","-A","--json"],capture_output=True, text=True)
#out = results.stdout

# Use the Json output
#tickets = json.loads(out)
#for t in tickets["tickets"]:
#    try:        
#        principalList.append(t['principal'])
#    except:
#        print(t)

#print(tickets["tickets"][0]['principal'])
#print("------")
#print(tickets["tickets"][1])
#exit()
# Read in the json config file to override defaults
if os.path.isfile(defaultConfig):    
    f = open(defaultConfig)
    data = json.load(f)
    # hostlist = data['hostlist']
    # userlist = data['userlist']
    # portStart = data['portStart']
    # portEnd = data['portEnd']
else:
    print("No config found\nUsing Defaults")
 

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        bar = self.menuBar()
        fileMenu = bar.addMenu("File")
        edit = bar.addMenu("Edit")

        save = QAction("Save",self)
        save.setShortcut("Ctrl+S")
        fileMenu.addAction(save)

        renew = QAction("Renew",self)
        renew.setShortcut("Ctrl+r")
        renew.triggered.connect(self.renewprincipal)
        fileMenu.addAction(renew)

        quit = QAction("Quit",self)
        fileMenu.addAction(quit)
        quit.setShortcut("Ctrl+q")
        quit.triggered.connect(QCoreApplication.quit)

        edit.addAction("copy")
        edit.addAction("paste")

        fileMenu.triggered[QAction].connect(self.processMenuTrigger)

        self.resize(300,50)
        self.setWindowTitle("DAQ Ticket Manager")

        # Create the different widgets
        self.currentprinc = QLabel(currentPrincipal)
        self.button = QPushButton("Switch Tickets")
        self.getnewbutton = QPushButton("Get New Ticket")
        self.renewbutton = QPushButton("Renew Tickets")
        self.renewallbutton = QPushButton("Renew All Tickets")

        self.princBox = QComboBox()
        self.princBox.addItems(principalList)

# Make a set of times to automate ticket renewals
        self.RenewTimer = QTimer()
        self.RenewTimer.setInterval(renewTime)
        self.RenewTimer.start()


# Add the different widgets for the window to the layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Current Kerberos Principal"))
        layout.addWidget(self.currentprinc)
        layout.addWidget(QLabel("Available Principals:"))
        layout.addWidget(self.princBox)
        layout.addWidget(self.button)
        layout.addWidget(self.getnewbutton)
        layout.addWidget(self.renewbutton)
        layout.addWidget(self.renewallbutton)
        # Set the layout for the main window
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connect the signals
        self.button.pressed.connect(self.switchprincipal)
        self.renewbutton.pressed.connect(self.renewprincipal)
        self.RenewTimer.timeout.connect(self.renewprincipal)       
        self.getnewbutton.pressed.connect(self.getnewticket)
        self.renewallbutton.pressed.connect(self.renewallprincipals)
        
    def processMenuTrigger(self,q):
        print(q.text()+" is triggered")

    # This function switches the default gssapi ccache
    # to the one that is selected.
    def switchprincipal(self):
        # Switch the kerb principal
        print("switching to: ",self.princBox.currentText())
        subprocess.run(["kswitch","-p",self.princBox.currentText()])
        subprocess.run(["klist","-A"])
        self.currentprinc.setText(self.princBox.currentText()) 

    # This function renews all principals that are in the
    # current cache list.
    def renewallprincipals(self):
        for p in principalList:
            print("Renewing Principals: ",p)
            try:    
                subprocess.run(["kinit","-R",p])
                print("Renewed:", p)
            except subprocess.CalledProcessError as e:
                print(f"Error renewing Kerberos ticket: {e}", file=sys.stderr)
            except FileNotFoundError:
                print("Error: kinit command not found", file=sys.stderr)
        return
    
    def renewprincipal(self):
        print("Renewing Principals: ",self.princBox.currentText())
        try:
            subprocess.run(["kinit","-R",self.princBox.currentText()])
            print("Renewed:", self.princBox.currentText())
        except subprocess.CalledProcessError as e:
            print(f"Error renewing Kerberos ticket: {e}", file=sys.stderr)
        except FileNotFoundError:
            print("Error: kinit command not found", file=sys.stderr)    
        return

    # This function gets a new ticket for the selected principal
    def getnewticket(self):
        print("Getting new ticket for: ",self.princBox.currentText())
        # Look up the keytab for the selected principal and get a new ticket
        for k in theData["principal"]:
            found = False
            v = theData["principal"][k]
            if v == self.princBox.currentText():
                print("Found principal in config file:", v)
                myuser = k 
                #theData["principal"][k]
                keytab = theData["keytab"][k]
                keytab = theData["keytab-master"]
                keypath = theData["keypath"]
                keytab_file = f"{keypath}/{keytab}"
                print(f"{myuser} {keytab_file}")
                get_kerberos_ticket(myuser)
                return

        if found == False:
            print("Failed to find keytab for:", self.princBox.currentText())
            subprocess.run(["kinit",self.princBox.currentText()])
            print("Got new ticket for:", self.princBox.currentText())

def get_kerberos_ticket(user):
    """
    Read the Kerberos principal information from kerb_princ.json and return it as a dictionary
    Returns:
        A dictionary containing the Kerberos principal information
    """
    try:
        principal = theData["principal"][user]
        keytab = theData["keytab"][user]
        keytab = theData["keytab-master"]
        keypath = theData["keypath"]
        keytab_file = f"{keypath}/{keytab}"
        print(f"{principal} {keytab_file}")
        try:
            subprocess.run(["kinit", "-kt", keytab_file, principal], check=True)
            print(f"Successfully obtained Kerberos ticket for {principal}")
        except subprocess.CalledProcessError as e:
            print(f"Error obtaining Kerberos ticket: {e}", file=sys.stderr)
        except FileNotFoundError:
            print("Error: kinit command not found", file=sys.stderr)
        return
    
    except FileNotFoundError:
        print("Error: kerb_princ.json file not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    # Create the main application
    app = QApplication(sys.argv)

    # Create the main window
    window = MainWindow()
    window.show()

    # Run the main event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()