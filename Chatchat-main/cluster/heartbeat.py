import socket
import sys
from time import sleep
from cluster import hosts, ports, leader_election

# Sending heartbeat
def send_heartbeat():
    while True:
        # create Socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.5)

        # Leader Election algorithm
        hosts.current_neighbour = leader_election.start_leader_election(hosts.server_list, hosts.myIP)
        host_address = (hosts.current_neighbour, ports.server_port)

        # Überprüfung, ob ein benachbarter Server vorhanden ist
        if hosts.current_neighbour:
            # Warte 5 Sekunden vor dem Senden des Heartbeat-Signals
            sleep(5)

            # Versuch, eine Verbindung zum benachbarten Server herzustellen, um das Heartbeat-Signal zu senden
            try:
                sock.connect(host_address)
                print(f'[HEARTBEAT] Reply from Neighbours {hosts.current_neighbour}', file=sys.stderr)

            except Exception as e:
                print(f'[HEARTBEAT] Error: {e}', file=sys.stderr)
                hosts.server_list.remove(hosts.current_neighbour)

                # Check the crashed Server
                if hosts.current_leader == hosts.current_neighbour:
                    print(f'[HEARTBEAT] Server Leader {hosts.current_neighbour} failed', file=sys.stderr)
                    hosts.is_leader_crashed = True
                    # New Server Leader Election
                    hosts.current_leader = leader_election.start_leader_election(hosts.server_list, hosts.myIP)
                    hosts.has_network_changed = True

                else:
                    print(f'[HEARTBEAT] Server Replica {hosts.current_neighbour} failed', file=sys.stderr)
                    hosts.is_replica_crashed = True

            finally:
                sock.close()

# Beispiel verwenden
if __name__ == "__main__":
    send_heartbeat()
