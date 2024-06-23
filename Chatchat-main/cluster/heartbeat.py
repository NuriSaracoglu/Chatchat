import socket
import sys
from time import sleep
import json
from cluster import hosts, ports, leader_election

# Sending heartbeat
def send_heartbeat():
    while True:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Perform leader election to determine current neighbour
        hosts.current_neighbour = leader_election.start_leader_election(hosts.server_list, hosts.myIP)
        ring_address = (hosts.current_neighbour, ports.multicast_port)

        # Wait for 5 seconds before sending the heartbeat signal
        sleep(5)

        # Prepare heartbeat message
        heartbeat_message = {
            "source": hosts.myIP,
            "message": "heartbeat"
        }

        # Send heartbeat message to current neighbour
        try:
            sock.sendto(json.dumps(heartbeat_message).encode(), ring_address)
            print(f'[HEARTBEAT] Heartbeat sent to neighbour {hosts.current_neighbour}', file=sys.stderr)

        except Exception as e:
            print(f'[HEARTBEAT] Failed to send heartbeat to neighbour {hosts.current_neighbour}: {e}', file=sys.stderr)

        finally:
            sock.close()

if __name__ == '__main__':
    send_heartbeat()
