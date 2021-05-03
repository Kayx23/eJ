# this script takes an IP address and a port range to check for open ports
# connect_ex() returns 0 if the operation succeeds; else, returns 106

import socket

target = input('IP address to scan (e.g. 127.0.0.1):') 
lport_bound = int(input('lower port bound:'))
uport_bound = int(input('upper port bound:')) 

print("\nScanning host",target,"from port",lport_bound,"to",uport_bound,"\n")

for port in range(lport_bound,uport_bound):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    status = s.connect_ex((target,port))
    if status == 0:
        print("*** port",port,"is open")

s.close()