import socket
import threading

from HostAndPorts import ports
from leader_election import LeaderElection

HOST = '127.0.0.1'
LISTENER_LIMIT = 5
active_clients = [] #List of all currently connected users

# Function to listen for upcoming messages from a client
def listen_for_messages(client, username):

    while 1:
        #response is the message
        message = client.recv(2048).decode('utf-8')
        if message != '':
            final_msg = username + '~' + message
            send_messages_to_all(final_msg)
        else:
            print("The message send from client {username} is empty")


#how to send message
#when send message we have to encode it and recv we have to decode
def send_message_to_client(client, message):
    
    client.sendall(message.encode())

# Function to send any new message to all the client that
#are currently connectet to this server
def send_messages_to_all(message):
    
    for user in active_clients:

        send_message_to_client(user[1], message)


#Function to handle client
def client_handler(client):
    
    #Server will listen for client message that will
    #contain the username
    while 1:

        username = client.recv(2048).decode('utf-8')
        if username !='':
            active_clients.append((username,client))
            prompt_message = "SERVER~" + f"{username} added to the chat"
            send_messages_to_all(prompt_message)
            break
        else:
            print("Client username is empty")
            
    threading.Thread(target=listen_for_messages,args=(client,username, )).start()    

#main function
def main():
    server_id = 1  # Unique ID for this server
    left_host = '127.0.0.1'
    left_port = 5001  # Port of the left neighbor
    right_host = '127.0.0.1'
    right_port = 5003  # Port of the right neighbor

    # Initialize the leader election
    leader_election =LeaderElection(server_id, left_host, left_port, right_host, right_port)
    leader_election.start_election()
    #Creating the socket class object 
    #Af_inet: we are goint to use ipv4 adresses
    #Socket stream is tcp for onecast
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #creating a try catch block
    try:
        # if client will connect to the server they have connect to the host and then to the port
        server.bind((HOST,ports.server_port))
        print(f"Running the server on {HOST} {ports.server_port}")
    except:
        print(f"Unable to bind to host {HOST} and port {ports.server_port}")

    #Set serv limit
    server.listen(LISTENER_LIMIT)

    #This while loop will keep listening to client connections
    while 1:
        client, address = server.accept()
        #address 0 will print the host and 1 the port of the client
        print(f"Successfully connected to client {address[0]} {address[1]}")

        threading.Thread(target=client_handler, args =(client, )).start()


if __name__ == "__main__":
    main()

