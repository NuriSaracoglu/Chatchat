import socket
import json
from cluster import hosts, ports

def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    return sorted_ip_ring

def get_neighbour(members, current_member_ip, direction='left'):
    current_member_index = members.index(current_member_ip) if current_member_ip in members else -1
    if current_member_index != -1:
        if direction == 'left':
            if current_member_index == len(members) - 1:
                return members[0]
            else:
                return members[current_member_index + 1]
        else:
            if current_member_index == 0:
                return members[-1]
            else:
                return members[current_member_index - 1]
    else:
        return None

def start_leader_election(server_list, leader_server):
    ring = form_ring(server_list)
    ring_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ring_socket.bind((leader_server, ports.multicast_port))
    print(f"Node is up and running at {leader_server}:{ports.multicast_port}\nWaiting to receive election message...\n")
    
    leader_uid = ''
    participant = False

    while True:
        data, address = ring_socket.recvfrom(1024)
        election_message = json.loads(data.decode())

        if election_message['isLeader']:
            leader_uid = election_message['mid']
            election_message['isLeader'] = False  # reset isLeader for forwarding
            ring_socket.sendto(json.dumps(election_message).encode(), get_neighbour(ring, leader_server, 'right'))
        
        elif election_message['mid'] < hosts.my_uid and not participant:
            new_election_message = {
                "mid": hosts.my_uid,
                "isLeader": False
            }
            participant = True
            ring_socket.sendto(json.dumps(new_election_message).encode(), get_neighbour(ring, leader_server, 'left'))
        
        elif election_message['mid'] > hosts.my_uid:
            participant = True
            ring_socket.sendto(json.dumps(election_message).encode(), get_neighbour(ring, leader_server, 'left'))
        
        elif election_message['mid'] == hosts.my_uid:
            leader_uid = hosts.my_uid
            new_election_message = {
                "mid": hosts.my_uid,
                "isLeader": True
            }
            participant = False
            ring_socket.sendto(json.dumps(new_election_message).encode(), get_neighbour(ring, leader_server, 'left'))
            
    ring_socket.close()
    return leader_uid if leader_uid != '' else None
