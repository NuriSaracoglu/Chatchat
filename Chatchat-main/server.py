# BEChat Server


import socket
import sys
import threading
import queue

from cluster import hosts, ports, receive_multicast, send_multicast, heartbeat

#TCP PART
#TCP Socket for Server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host_address = (hosts.myIP, ports.server_port)

# FIFO Queue
FIFO = queue.Queue()

#Display Server information
def display_server_info():
    print(f'\n[SERVER] Server List: {hosts.server_list} ==> Leader: {hosts.current_leader}'
          f'\n[SERVER] Client List: {hosts.client_list}'
          f'\n[SERVER] Neighbour: {hosts.current_neighbour}\n')
 
def create_and_start_thread(target, args):
    new_thread = threading.Thread(target=target, args=args)
    new_thread.daemon = True
    new_thread.start()

#Sending messages to the clients
def send_messages_to_all_clients():
    complete_message = ''
    while not FIFO.empty():
        complete_message += FIFO.get()
        complete_message += '\n' if not FIFO.empty() else ''
 
    
    if complete_message:
        #multicast_socket
        for member in hosts.client_list:
            member.send(complete_message.encode(hosts.unicode))

def handle_client_messages(client, client_address):
    while True:
        try:
            received_data = client.recv(hosts.buffer_size)
 
            if not received_data:
                print(f'{client_address} has disconnected')
                FIFO.put(f'\n{client_address} has disconnected\n')
                hosts.client_list.remove(client)
                client.close()
                break
 
           
            decoded_message = received_data.decode(hosts.unicode)
            FIFO.put(f'{client_address} sagte: {decoded_message}')
            print(f'Nachricht von {client_address} ==> {decoded_message}')
 
        except Exception as error:
            print(f'Error: {error}')
            break


def initialize_and_listen_server():
    sock.bind(host_address)
    sock.listen()
    print(f'\n[SERVER] it starts and listens on IP {hosts.myIP} with PORT {ports.server_port}',
          file=sys.stderr)
 
    while True:
        try:
            client, client_address = sock.accept()
            received_data = client.recv(hosts.buffer_size)
 
            
            if received_data:
                print(f'{client_address} connected')
                FIFO.put(f'\n{client_address} connected\n')
                hosts.client_list.append(client)
                create_and_start_thread(handle_client_messages, (client, client_address))
 
        except Exception as error:
            print(f'Error: {error}')
            break


if __name__ == '__main__':

    # trigger Multicast Sender 
    multicast_receiver_exist = send_multicast.send_update_to_multicast_group()

    # append the own IP to the Server List and assign the own IP as the Server Leader
    if not multicast_receiver_exist:
        hosts.server_list.append(hosts.myIP)
        hosts.current_leader = hosts.myIP

    # calling functions as Threads
    create_and_start_thread(receive_multicast.receive_multicast_message, ())
    create_and_start_thread(initialize_and_listen_server, ())
    create_and_start_thread(heartbeat.send_heartbeat, ())

    while True:
        try:
            # send Multicast Message to all Multicast Receivers (Servers)
            if hosts.current_leader == hosts.myIP and hosts.has_network_changed or hosts.is_replica_crashed:
                if hosts.is_leader_crashed:
                    hosts.client_list = []
                send_multicast.send_update_to_multicast_group()
                hosts.is_leader_crashed = False
                hosts.has_network_changed = False
                hosts.is_replica_crashed = ''
                display_server_info()

            if hosts.current_leader != hosts.myIP and hosts.has_network_changed:
                hosts.has_network_changed = False
                display_server_info()

            # function to send the FIFO Queue messages
            send_messages_to_all_clients()

        except KeyboardInterrupt:
            sock.close()
            print(f'\nClosing Server on IP {hosts.myIP} with PORT {ports.server_port}', file=sys.stderr)
            break