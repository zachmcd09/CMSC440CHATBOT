# ChatServer.py

from collections import deque
import socket
from socket import AF_INET, SOCK_STREAM
import sys
import logging
import threading
import argparse
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatServer:
    def __init__(self, ip, port):
        self.logger = logging.getLogger(__name__)
        self.port = port
        self.ip = ip
        self.server_socket = socket.socket(AF_INET, SOCK_STREAM)
        self.client_dict = dict()  # dictionary of connected clients
        self.active_clients = deque()  # Use deque to efficiently add/remove clients
        self.lock = threading.Lock()   # lock for thread-safe access to client_dict

    def broadcast_message(self, sender, message):
        """
        Broadcasts a message to all connected clients except the sender.

        Args:
            sender: The client sending the message.
            message: The message to broadcast.
        """
        try:
            with self.lock:
                # Filter out the sender before iterating over active clients
                for socket in [client for client in self.active_clients if client != sender]:
                    try:
                        socket.send(message.encode())
                    except Exception as e:
                        logging.error(f'Failed to send message to client {socket}: {str(e)}')
                        # Remove the client if an error occurs during sending
                        self.rm_client(socket)
        except Exception as e:
            self.logger.error(f'Error occurred while broadcasting message: {str(e)}')

    def add_client(self, client, socket):
        """
        Adds a new client to the client dictionary.

        Args:
            client: The client's address.
            socket: The client's socket.
        """
        try:
            with self.lock:
                if client not in self.client_dict:  # Check if the client is already connected
                    self.client_dict[client] = socket
                    self.active_clients.append(socket)  # Add to both dict and set for broadcasting
                    client_id = self.get_next_client_id()
                    self.client_dict[client_id] = {'socket': socket, 'addr': addr}

                    logging.info(f'Client {client} connected successfully.')
        except KeyError as e:
            logging.error(f'Error occurred while adding client {client}: {str(e)}')

    def get_next_client_id(self):
        """Get a unique identifier for a new client."""
        self.client_id += 1
        return self.client_id

    
    def rm_client(self, addr):
        """
        Removes a client from the client dictionary and closes their socket.
        Args:
            addr: The client's address.
        """
        with self.lock:
            try:
                connectionSocket = self.client_dict[addr]
                connectionSocket.close()
                self.active_clients.remove(connectionSocket)
                del self.client_dict[addr]  # Ensure the client is removed from the dictionary
                logging.info(f'Client {addr} disconnected successfully.')
            except KeyError as e:
                logging.error(f'Error occurred while removing client {addr}: {str(e)}')
            except ValueError:
                logging.error(f'Socket for client {addr} not found in active clients list.')
            except Exception as e:
                logging.error(f'Unexpected error occurred while disconnecting client {addr}: {str(e)}')



    def client_handler(self, connectionSocket, addr):
        """
        Handles a multiple client connections, processes multiple incoming messages in FIFO order,
        broadcasts messages, and manages client disconnections upon request.

        Args:
            connectionSocket: The client's socket.
            addr: The client's address.
        """
        try:
            self.add_client(addr, connectionSocket)
            self.logger.info('Client %s made connection', addr)
            
            while True:
                clientEncoded = connectionSocket.recv(1024)
                if not clientEncoded:
                    break  # Client disconnected
                
                clientMessage = clientEncoded.decode()
                self.logger.info('FROM CLIENT %s: %s', addr, clientMessage)
                serverSentence = "DISCONNECT" if clientMessage.strip().upper() == "DISCONNECT" else clientMessage
                self.broadcast_message(connectionSocket, serverSentence)
                connectionSocket.send(serverSentence.encode())
                self.logger.info('TO CLIENT %s: %s', addr, serverSentence)
                if clientMessage.strip().upper() == "DISCONNECT":
                    break  # Client
        except Exception as e:
            logging.error("Failed to handle client %s: %s", addr, str(e))
        finally:
            self.rm_client(addr)  # Ensure the client is removed and the socket is closed



    def start(self):
        """Start the chat server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))  # Correctly use self.port here
        self.server_socket.listen()
        
        print("Chat server is running...")
        
        while True:
            connectionSocket, addr = self.server_socket.accept()
            client_thread = threading.Thread(target=self.client_handler, args=(connectionSocket, addr))
            client_thread.start()


def main():
    parser = argparse.ArgumentParser(description="Start a chat server.")
    parser.add_argument("port", type=int, help="Port number must be between 1 and 65536.")
    parser.add_argument("server_ip", help="Server IP address.")
    args = parser.parse_args()
    server_ip = args.server_ip
    port = args.port
    try:
        if not 1 <= port <= 65536:
            raise ValueError("Port number must be between 1 and 65536.")
    except ValueError as e:
        logging.error(str(e))
        sys.exit(1)  # Exit with an error code
    ActiveServer = ChatServer(server_ip, port)
    ActiveServer.start()  # Start the server with proper backlog and thread



if __name__ == "__main__":
    main()
