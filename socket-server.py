# this is a server side script that listens for incoming TCP connection
# run with $ python3 socket-server.py

# with one work station, this creates a socket on localhost interface
# we can access from wlan0 terminal with netcat $ nc 127.0.0.1 33333

import socket

# inet = socket.gethostbyname(socket.gethostname()) # get inet IP addr
srv_addr = '127.0.0.1'
srv_port = 33333

# create a socket
# AF_INET: IPv4
# SOCK_STREAM: TCP
# AF_INET6: IPv6
# SOCK_DGRAM: UDP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((srv_addr, srv_port))
print("Socket bound to server",srv_addr,"port",srv_port)

s.listen(1)  # max num of queued connections
print("Server listening on port",srv_port,"....")

conn, addr = s.accept()
# conn is connection, which is a socket object
# addr is the client address bound to the socket 
print("Client",addr,"connected")

# print all msgs received from client
while 1:

    # reads at most 1024 bytes
    client_data = conn.recv(1024)

    # break when client disconnects
    if not client_data: break

    # send this to client; bytes-like object required for Python 3.x
    conn.sendall(b"Message Received by Server")

    # print the msg the client sent; decode bytes
    print(client_data.decode('utf-8'))

conn.close()
