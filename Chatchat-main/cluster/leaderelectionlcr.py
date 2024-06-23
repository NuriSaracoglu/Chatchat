import socket
import json
import uuid
from cluster import hosts

def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    return sorted_ip_ring

def get_neighbour(members, current_member_ip, direction='left'):
    current_member_index = members.index(current_member_ip) if current_member_ip in members else -1
    if current_member_index != -1:
        if direction == 'left':
            return members[(current_member_index - 1) % len(members)]
        else:
            return members[(current_member_index + 1) % len(members)]
    else:
        return None

def start_leader_election(server_list, my_ip, my_uid):
    ring = form_ring(server_list)
    right_neighbour = get_neighbour(ring, my_ip, 'right')
    left_neighbour = get_neighbour(ring, my_ip, 'left')
    buffer_size = 1024

    ring_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ring_socket.bind((my_ip, 10001))
    print(f"Node is up and running at {my_ip}:10001")
    print('\nWaiting to receive election message...\n')

    election_message = {
        "mid": my_uid,
        "isLeader": False
    }
    
    participant = False
    leader_uid = None

    def send_message(message, neighbour):
        ring_socket.sendto(json.dumps(message).encode(), (neighbour, 10001))

    while True:
        data, address = ring_socket.recvfrom(buffer_size)
        received_message = json.loads(data.decode())

        if received_message['isLeader']:
            leader_uid = received_message['mid']
            participant = False
            send_message(received_message, left_neighbour)
        else:
            if received_message['mid'] < my_uid and not participant:
                new_election_message = {
                    "mid": my_uid,
                    "isLeader": False
                }
                participant = True
                send_message(new_election_message, left_neighbour)
            elif received_message['mid'] > my_uid:
                participant = True
                send_message(received_message, left_neighbour)
            elif received_message['mid'] == my_uid:
                leader_uid = my_uid
                new_leader_message = {
                    "mid": my_uid,
                    "isLeader": True
                }
                participant = False
                send_message(new_leader_message, left_neighbour)

# Beispielwerte für my_ip und my_uid
my_ip = '183.38.223.1'
my_uid = str(uuid.uuid4())
server_list = ['192.168.0.1', '183.38.223.1', '10.0.0.2']  # Beispielserverliste

start_leader_election(server_list, my_ip, my_uid)