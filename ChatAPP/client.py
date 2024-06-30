import socket
import threading
import os
from time import sleep
import hosts, ports, send_multicast

#Create Thread function
def create_and_start_thread(target, args):
    threading.Thread(target=target, args=args, daemon=True).start()  

def send_messages_to_server():
    global sock 
    print("[INFO] Write your message to Client X: ")
    while True:
        message = input("")
        
        try:
            if message != '':
             sock.send(message.encode(hosts.unicode))
 
        except Exception as error:
            print(f"Error while sending message: {error}")
            break


def receive_messages_from_server():
    global sock  
    while True:

        try:
            received_data = sock.recv(hosts.buffer_size)
            print(received_data.decode(hosts.unicode))   
            if not received_data:
                print("\n[ERROR] The server is currently unavailable."
                      "Please wait 5 sec. to reconnect to Server Leader!")
                sock.close()
                sleep(5)
                establish_connection_to_server_leader()
 
        except Exception as error:
            print(f" Error receiving the message {error}")
            break


def establish_connection_to_server_leader():
    global sock
 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_exists = send_multicast.send_join_request_to_chat_server()
 
    if server_exists:
        
        server_leader_address = (hosts.current_leader, ports.server_port)
        print(f'[SERVER] {server_leader_address}')
 
        sock.connect(server_leader_address)
        sock.send('JOIN'.encode(hosts.unicode))
        print("[INFO] Welcome to the Chatroom")
 

    else:
        print("[WARN] Please try joining the Chatroom again later.")
        os._exit(0)


if __name__ == '__main__':
    try:
        print("[INFO] You try to join the Chatroom.")

        # Connect to Server Leader
        establish_connection_to_server_leader()

        # Start Threads for sending and receiving messages
        create_and_start_thread(send_messages_to_server, ())
        create_and_start_thread(receive_messages_from_server, ())

        while True:
            pass

    except KeyboardInterrupt:
        sock.close()
        print("\nYou left the Chatroom")

