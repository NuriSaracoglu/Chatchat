import socket
import sys
import threading
import queue
from time import sleep
import hosts, ports, receive_multicast, send_multicast

# TCP PART
# TCP Socket for Server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_host = (hosts.myIP, ports.server_port)

# FIFO Queue
FIFO = queue.Queue()

# Display Server information
def display_server_info():
    print(f'\n[SERVER] Server List: {hosts.server_list} ==> Leader: {hosts.current_leader}'
          f'\n[SERVER] Client List: {hosts.client_list}'
          f'\n[SERVER] Neighbour: {hosts.current_neighbour}\n')

def create_and_start_thread(target, args):
    threading.Thread(target=target, args=args, daemon=True).start()

# Sending messages to the clients
def send_messages_to_all_clients():
    complete_message = ''
    while not FIFO.empty():
        complete_message += FIFO.get()
        complete_message += '\n' if not FIFO.empty() else ''

    if complete_message:
        # Multicast socket
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
            FIFO.put(f'{client_address}: {decoded_message}')
            print(f'The message from the client {client_address} is {decoded_message}')
        except Exception as error:
            print(f'Error: {error}')
            break

#------------------------------------------- Leader Election ------------------------------------------------------------------------------------------------

def start_leader_election():
    if hosts.server_list:
        # Wähle den Server mit der höchsten IP-Adresse als Leader
        hosts.current_leader = max(hosts.server_list)
        print(f'[LEADER ELECTION] New Leader elected: {hosts.current_leader}')
    else:
        hosts.current_leader = None

#-------------------------------------------- Heartbeat to servers --------------------------------------------------------------------------------------------------
def send_heartbeat():
    while True:
        # create Socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.5)

        if hosts.current_leader != hosts.myIP:
            hosts.current_neighbour = hosts.current_leader
        else:
            # Finde den nächsten Server im Ring
            sorted_servers = sorted(hosts.server_list)
            current_index = sorted_servers.index(hosts.myIP)
            hosts.current_neighbour = sorted_servers[(current_index + 1) % len(sorted_servers)]

        server_host = (hosts.current_neighbour, ports.server_port)

        # Überprüfung, ob ein benachbarter Server vorhanden ist
        if hosts.current_neighbour:
            # Warte 5 Sekunden vor dem Senden des Heartbeat-Signals
            sleep(5)

            # Versuch, eine Verbindung zum benachbarten Server herzustellen, um das Heartbeat-Signal zu senden
            try:
                sock.connect(server_host)
                print(f'[HEARTBEAT] Reply from Neighbours {hosts.current_neighbour}', file=sys.stderr)
            except:
                hosts.server_list.remove(hosts.current_neighbour)

                # Check the crashed Server
                if hosts.current_leader == hosts.current_neighbour:
                    print(f'[HEARTBEAT] Server Leader {hosts.current_neighbour} failed', file=sys.stderr)
                    hosts.is_leader_crashed = True
                    start_leader_election()
                    hosts.has_network_changed = True
                else:
                    print(f'[HEARTBEAT] Server Replica {hosts.current_neighbour} failed', file=sys.stderr)
                    hosts.is_replica_crashed = True
            finally:
                sock.close()

def initialize_and_listen_server():
    sock.bind(server_host)
    sock.listen()
    print(f'\n[SERVER] It starts and listens on IP {hosts.myIP} with PORT {ports.server_port}', file=sys.stderr)
    
    while True:
        try:
            client, client_address = sock.accept()
            received_data = client.recv(hosts.buffer_size)
            if received_data:
                FIFO.put(f'\n{client_address} connected\n')
                hosts.client_list.append(client)
                create_and_start_thread(handle_client_messages, (client, client_address))
        except Exception as error:
            print(f'Error: {error}')
            break

if __name__ == '__main__':
    multicast_receiver_exist = send_multicast.send_update_to_multicast_group()

    if not multicast_receiver_exist:
        hosts.server_list.append(hosts.myIP)
        start_leader_election()

    create_and_start_thread(receive_multicast.receive_multicast_message, ())
    create_and_start_thread(initialize_and_listen_server, ())
    create_and_start_thread(send_heartbeat, ())

    while True:
        try:
            if hosts.current_leader == hosts.myIP and (hosts.has_network_changed or hosts.is_replica_crashed):
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

            send_messages_to_all_clients()
        except KeyboardInterrupt:
            sock.close()
            print(f'\nClosing Server on IP {hosts.myIP} with PORT {ports.server_port}', file=sys.stderr)
            break
