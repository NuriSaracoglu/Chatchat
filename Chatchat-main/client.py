import socket
import threading
import os
from time import sleep
from cluster import hosts, ports, send_multicast

#Thread function
def create_and_start_thread(target, args):
    thread = threading.Thread(target=target, daemon=True, args=args)  
    thread.start()

# establish connection to server leader
def request_to_the_server_leader():
    global sock
 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_exists = send_multicast.send_join_request_to_chat_server()
 
    if server_exists:
        
        server_leader_address = (hosts.current_leader, ports.server_port)
        print(f'[INFO] The Server Leader is: {server_leader_address}')
        sock.connect(server_leader_address)
        sock.send('JOIN'.encode(hosts.unicode))
        print("\nYour request has been approved. You have entered the chat room. Now you can start chatting\n")
 
    else:
        print("\nPlease try entering the chat Room again later.")
        os._exit(0)
 
 
def send_messages_to_server():
    global sock 
    while True: 
        username = input('Hi there, nice to see you here! \nPlease enter your username before you start chatting: ')
        if username:
            try:      
                sock.send(username.encode(hosts.unicode))
                print(f'\nWelcome to NG {username}!\nThank you for choosing us.')
                break   

            except Exception as error:
                print(f'Error sending message: {error}. \nPlease try it again.')
        else: 
            print('Username cannot be empty. Please enter your username')

    while True:
        message = input("\nPlease enter your message: ")
 
        try:
            sock.send(message.encode(hosts.unicode))
 
        except Exception as error:
            # Text muss angepasst werden.
            print(f"Error Message has not been sent: {error}")
            break

# receive message from server 
def receive_messages_from_server():
    global sock 

    while True:

        try:
            received_data = sock.recv(hosts.buffer_size)
            print(received_data.decode(hosts.unicode))   
            if not received_data:
                print("\nUnfortunately, the chat server is currently unreachable."
                      "We will try to reconnect you to the server in a few seconds!")
                sock.close()
                sleep(5)
                request_to_the_server_leader()
 
        except Exception as error:
            print(f" Error receiving the message {error}")
            break

if __name__ == '__main__':
    try:
        print("Your chat access request is being processed.")

        # Connect to Server Leader
        request_to_the_server_leader()

        # Start Threads for sending and receiving messages
        create_and_start_thread(send_messages_to_server, ())
        create_and_start_thread(receive_messages_from_server, ())

        while True:
            pass

    except KeyboardInterrupt:
        # Umsetzungsidee:  Hier könnte wieder der Username erscheinen.
        print(f"\nYou have left the chat room. See you soon!")
