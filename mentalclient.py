import socket
import pandas as pd
import time
from mentalfatigue import assess
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = (socket.gethostname(), 10000)
print('connecting to {} port {}'.format(*server_address))
sock.connect(server_address)

test = pd.read_csv('trainlist.csv')
test = test.iloc[:, 1:-2]

try:
    for i in range(test.shape[0]):
        for j, val in enumerate(test.iloc[i].to_list()):
            message = "{}\t{}\n".format(j, val).encode('utf-8')
            sock.sendall(message)
            time.sleep(1/64)
        time.sleep(4)
        # Look for the response
        amount_received = 0
        amount_expected = len('Fatigued'.encode('utf-8'))

        while amount_received < amount_expected:
            data = sock.recv(32)
            amount_received += len(data)
            print("Results: {}".format(data.decode('utf-8')))
finally:
    print('closing socket')
    sock.close()