import socket

# get own IP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(("8.8.8.8", 80))
myIP = sock.getsockname()[0]

#Connection variables
buffer_size = 1024 
unicode = 'utf-8'
 