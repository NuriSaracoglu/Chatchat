import socket
import struct
import pickle
import sys
from time import sleep
from cluster import hosts, ports

#multicast IP & UDP Socket
multicast_address = (hosts.multicast, ports.multicast_port)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)


def send_update_to_multicast_group():
    sleep(1)

    complete_message = pickle.dumps([hosts.server_list, hosts.current_leader, hosts.is_leader_crashed, hosts.is_replica_crashed,
                            str(hosts.client_list)])
    sock.sendto(complete_message, multicast_address)
    print(f'\n[MULTICAST SENDER {hosts.myIP}] Sending data to Multicast Receivers {multicast_address}',
          file=sys.stderr)

    # if Multicast Receiver exists then return True otherwise return False
    try:
        sock.recvfrom(hosts.buffer_size)

        if hosts.current_leader == hosts.myIP:
            print(f'[MULTICAST SENDER {hosts.myIP}] All Servers have been updated\n',
                  file=sys.stderr)
        return True

    except socket.timeout:
        print(f'[MULTICAST SENDER {hosts.myIP}] Multicast Receiver not detected',
              file=sys.stderr)
        return False


def send_join_request_to_chat_server():
    
    print(f'\n[MULTICAST SENDER {hosts.myIP}] Chat join request to multicast address {multicast_address} sent',
          file=sys.stderr)
    complete_message = pickle.dumps(['JOIN', '', '', '']) 
    sock.sendto(complete_message, multicast_address)

    try:
        received_data, address = sock.recvfrom(hosts.buffer_size)
        hosts.current_leader = pickle.loads(received_data)[0]
        return True
    
    except socket.timeout:
        print(f'[MULTICAST SENDER {hosts.myIP}] No multicast receiver detected -> Chat Server is currently offline.',
              file=sys.stderr)
        return False

   
 

