# leader_election.py
import socket
import threading
import time

class LeaderElection:
    def __init__(self, id, left_host, left_port, right_host, right_port):
        self.id = id
        self.left_host = left_host
        self.left_port = left_port
        self.right_host = right_host
        self.right_port = right_port
        self.leader = None
        self.phase = 0
        self.active = True

    def start_election(self):
        threading.Thread(target=self.election).start()

    def election(self):
        while self.active:
            self.phase += 1
            print(f"Node {self.id} starts phase {self.phase}")
            self.send_message(self.id, self.phase, self.right_host, self.right_port)
            self.send_message(self.id, self.phase, self.left_host, self.left_port)
            time.sleep(5)

    def send_message(self, sender_id, phase, host, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(f"{sender_id} {phase}".encode('utf-8'))
        except ConnectionRefusedError:
            print(f"Connection to {host}:{port} refused")

    def receive_message(self, sender_id, phase):
        if phase < self.phase:
            return
        if phase == self.phase and sender_id < self.id:
            return

        if sender_id == self.id:
            self.active = False
            self.leader = self.id
            print(f"Node {self.id} elected as leader in phase {self.phase}")
            self.announce_leader()
        else:
            self.send_message(sender_id, phase, self.right_host, self.right_port)
            self.send_message(sender_id, phase, self.left_host, self.left_port)

    def announce_leader(self):
        self.send_leader_announcement(self.id, self.right_host, self.right_port)
        self.send_leader_announcement(self.id, self.left_host, self.left_port)

    def send_leader_announcement(self, leader_id, host, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(f"leader {leader_id}".encode('utf-8'))
        except ConnectionRefusedError:
            print(f"Connection to {host}:{port} refused")

    def receive_leader_announcement(self, leader_id):
        self.leader = leader_id
        print(f"Node {self.id} recognizes Node {leader_id} as leader")
        if self.leader != self.id:
            self.send_leader_announcement(leader_id, self.right_host, self.right_port)
            self.send_leader_announcement(leader_id, self.left_host, self.left_port)
