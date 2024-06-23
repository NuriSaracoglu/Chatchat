import socket
from cluster import hosts, ports

def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    return sorted_ip_ring

def get_neighbour(members, current_member_ip, direction='left'):
    current_member_index = members.index(current_member_ip) if current_member_ip in members else -1
    if current_member_index != -1:
        if direction == 'left':
            if current_member_index + 1 == len(members):
                return members[0]
            else:
                return members[current_member_index + 1]
        else:
            if current_member_index - 1 == -1:
                return members[-1]
            else:
                return members[current_member_index - 1]
    else:
        return None

def send_election_message(sender_ip, message_id, election_active):
    n = len(hosts.server_list)
    current_node = sender_ip

    while True:
        next_node_ip = get_neighbour(hosts.server_list, current_node, 'right')
        if not next_node_ip:
            break
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(1.5)
                sock.connect((next_node_ip, ports.server_port))
                sock.sendall(f'ELECTION {message_id} {election_active}'.encode(hosts.unicode))

                response = sock.recv(hosts.buffer_size).decode(hosts.unicode)
                response_parts = response.split()
                if response_parts[0] == 'ELECTION':
                    received_id = response_parts[1]
                    received_active = response_parts[2] == 'True'

                    if not received_active:  # Election phase
                        if int(received_id) < int(hosts.myIP):
                            current_node = next_node_ip
                        elif int(received_id) > int(hosts.myIP):
                            message_id = received_id
                            current_node = next_node_ip
                        elif received_id == hosts.myIP:
                            print(f"Node {hosts.myIP} declares itself as leader")
                            hosts.current_leader = hosts.myIP
                            announce_leader()
                            return
                    else:  # Announcement phase
                        hosts.current_leader = received_id
                        if received_id == hosts.myIP:
                            return
        except Exception as e:
            print(f"Error sending election message: {e}")
            break

def announce_leader():
    current_node = hosts.myIP
    while True:
        next_node_ip = get_neighbour(hosts.server_list, current_node, 'right')
        if not next_node_ip:
            break
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(1.5)
                sock.connect((next_node_ip, ports.server_port))
                sock.sendall(f'ELECTION {hosts.current_leader} True'.encode(hosts.unicode))
        except Exception as e:
            print(f"Error announcing leader: {e}")
            break

def start_leader_election(server_list, leader_server):
    hosts.server_list = form_ring(server_list)
    hosts.myIP = leader_server
    hosts.current_neighbour = get_neighbour(hosts.server_list, leader_server, 'right')
    if hosts.current_neighbour != leader_server:
        send_election_message(leader_server, leader_server, False)
    return hosts.current_leader
