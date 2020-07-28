import socket
from mentalfatigue import assess
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = (socket.gethostname(), 10000)
print('Starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the data in small chunks and retransmit it
        while True:
            i = 0
            sample = []
            while i != 63:
                data = connection.recv(32)
                if data:
                    # connection.sendall(data)

                    pkg = data.decode('utf-8').split()
                    [i, feat] = int(pkg[0]), float(pkg[1])
                    sample.append(feat)
            connection.sendall(assess(sample).encode('utf-8'))


    finally:
        # Clean up the connection
        print("Closing current connection")
        connection.close()