from collections import deque
import json
from socket import AF_INET, SOCK_STREAM, socket
import sys
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client_dict = {}  # Dictionary of connected clients
lock = threading.Lock()  # Lock for thread-safe access to client_dict

def broadcast_message(sender, message):
    """
    Broadcasts a message to all connected clients except the sender.
    """
    with lock:
        for client, conn_socket in client_dict.items():
            if client != sender:
                try:
                    conn_socket.send(message.encode())
                except Exception as e:
                    logging.error(f'Failed to send message to client {client}: {str(e)}')
                    rm_client(client)  # Remove the client if an error occurs

def add_client(client, socket):
    """
    Adds a new client to the client dictionary.
    """
    with lock:
        client_dict[client] = socket
        logging.info(f'Client {client} connected successfully.')

def rm_client(client):
    """
    Removes a client from the client dictionary and closes their socket.
    """
    with lock:
        if client in client_dict:
            client_dict[client].close()
            del client_dict[client]
            logging.info(f'Client {client} disconnected successfully.')

def client_handler(connectionSocket, addr):
    """
    Handles a single client connection.
    """
    try:
        add_client(addr, connectionSocket)  # Add client on successful connection
        while True:
            clientEncoded = connectionSocket.recv(1024)
            if not clientEncoded:
                break
            clientData = json.loads(clientEncoded.decode())
            logging.info(f'Client {addr} sent message: {clientData}')
            if clientData['type'] == 'disconnect':
                break
            broadcast_message(addr, json.dumps(clientData))
    except Exception as e:
        logging.error(f'An error occurred with client {addr}: {str(e)}')
    finally:
        rm_client(addr)  # Ensure client is removed when done
        connectionSocket.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Usage: python ChatServer.py <port> <server_ip>")
        sys.exit()

    port = int(sys.argv[1])
    server_ip = sys.argv[2]
    hostSocket = socket(AF_INET, SOCK_STREAM)
    hostSocket.bind((server_ip, port))
    hostSocket.listen(10)  # Listen for more than 1 client
    logging.info(f'ChatServer started with server IP: {server_ip}, port: {port}')

    try:
        while True:
            connectionSocket, addr = hostSocket.accept()
            threading.Thread(target=client_handler, args=(connectionSocket, addr)).start()
    finally:
        hostSocket.close()  # Ensure the server socket is closed on exit
