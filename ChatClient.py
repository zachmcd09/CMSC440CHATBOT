# ChatClient.py
import argparse
import io
import json
import socket   # Import socket module
import sys   # Import system module
from datetime import datetime
import threading  # Import datetime module for timestamping
from collections import Counter, defaultdict

# Initialize global variables for statistics tracking
class ChatClient:
    def __init__(self, ip, port, nickname, client_id):
        self.ip = ip
        self.port = port
        self.nickname = nickname
        self.client_id = client_id
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.start_time = datetime.now()
        self.stats = defaultdict(int)

    def _generate_json_message(self, msg_type, **kwargs):
        payload = {"timestamp": datetime.now().isoformat()}
        payload.update(**kwargs)  # Add additional key-value pairs to the payload
        return json.dumps({"type": msg_type, **payload})

    def get_hello_string(self):
        """Generates a JSON 'hello' message for initiating a chat session."""
        return self._generate_json_message("ChatClient started with server IP:", **{
            'ip': self.ip,
            ', port': self.port,
            ', nickname': self.nickname,
            ', client ID:': self.client_id
        })

    def get_nickname_string(self):
        """
        Constructs a JSON string representing the user's nickname and client ID.
        
        Args:
            nickname (str): The user's chosen nickname for the chat application.
            client_id (int): A unique identifier for the client instance.
        
        Returns:
            str: A JSON string with the user's nickname, client ID, and timestamp.
        """
        return self._generate_json_message("nickname", nickname=self.nickname, clientID=self.client_id)

    def get_message_string(self, message):
        """
        Returns a JSON-formatted string representing the user's sent message.

        Parameters:
            nickname (str): The user's chosen nickname.
            message (str): The content of the user's sent message.

        Returns:
            str: A JSON-formatted string representing the user's sent message.
        """
        return self._generate_json_message("message", nickname=self.nickname, message=message)

    def get_disconnect_string(self):
        """
        Returns a JSON-formatted string representing the user's disconnection request.

        Parameters:
            nickname (str): The user's chosen nickname.
            client_id (str): A unique identifier for the client.

        Returns:
            str: A JSON-formatted string representing the user's disconnection request.
        """
        return self._generate_json_message("disconnect", nickname=self.nickname, clientID=self.client_id)

    def print_summary(self):
        """
        Prints a summary of the chat session statistics.
        """
        end_time = datetime.now()
        print(f'Summary: start: {self.start_time}, end:{end_time}, msg sent:{self.stats["messages_sent"]},msg rcv:{self.stats["messages_received"]}, char sent: {self.stats["characters_sent"]}, char rcv: {self.stats["characters_received"]}')

    def send_message(self, message):
        """
        Sends a message to the server and updates statistics.
        """
        self.stats["messages_sent"] += 1  # Increment count of sent messages
        self.stats["characters_sent"] += len(message)  # Update total character count for all sent messages
        message_string = self.get_message_string(self.nickname, message).encode()  # Encode the JSON-formatted string to bytes before sending
        self.client_socket.send(message_string)


    def read_from_server(self, clientSocket):
        """
        Reads incoming message from the server and updates statistics.
        """
        while True:
            data = clientSocket.recv(1024)
            if not data:
                break
            self.stats["messages_received"] += 1  # Increment message count
            self.stats["characters_received"] += len(data)  # Update character count
            print('FROM SERVER:', json.loads(data)["timestamp"])  # Correctly parse the JSON data


def main():
    """
    Main function that handles command-line arguments and sets up the chat session.
    """
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('hostname', type=str, help='The server hostname')
    parser.add_argument('port', type=int, help='The server port number')
    parser.add_argument('nickname', type=str, help='Your chat nickname')
    args = parser.parse_args()

    try:
        ip = socket.gethostbyname(args.hostname)
    except socket.gaierror as e:
        print(f"Error resolving hostname: {e}")
        sys.exit(1)
    if len(sys.argv) != 4:
        print("ERR - Usage: python ChatClient.py <hostname> <port> <nickname>")
        sys.exit()

    ip = socket.gethostbyname(args.hostname)  # Get IP address from hostname provided as command-line argument
    port = int(args.port)  # Convert port number to integer type
    nickname = str(args.nickname)   # Set user's chosen nickname from command-line argument

    clientSession = ChatClient(ip, port, nickname, str(f"{ip}:{port}"))

    # Create a TCP/IP socket object
    clientSession.client_socket.connect((ip, port))  # Establish connection with the server using provided IP address and port number

    print(f"ChatClient started with IP: {clientSession.ip},port: {clientSession.port}, nickname: {clientSession.nickname}, client ID: {clientSession.client_id}")  # Inform the user of their unique identifier
    
    # Send the nickname and client ID to the server using the get_nickname_string function
    nickname_string = clientSession.get_nickname_string()
    clientSession.client_socket.send(nickname_string.encode())
    print(nickname_string)  # Optionally print the sent JSON-formatted string to the console

    server = threading.Thread(target=clientSession.read_from_server, args=[clientSession.client_socket])  # Create a separate thread for reading from server
    server.start()  # Start the thread

    while True:
        clientSentence = input('Enter message:\n') # Prompt user for their sent message and assign it to variable 'clientSentence'
        if clientSentence.upper().strip() == "DISCONNECT": # Check if user entered command to disconnect from chat session
            clientSession.get_disconnect_string()  # Exit loop and proceed with further steps in program execution flow
            break
        if clientSentence != "":  # Check if user entered any message
            clientSession.stats.update({clientSentence: clientSession.stats[clientSentence] + 1})  # Increment the count for the message in the stats dictionary
        
            message_string = clientSession.get_message_string(clientSentence)   # Generate JSON-formatted string representing user's sent message using helper function 'get_message_string()'

            clientSession.client_socket.send(message_string.encode())  # Send generated JSON-formatted string to server over established TCP/IP connection

    server.join()  # Wait for the thread to finish

    clientSession.print_summary()  # Print chat session summary to console
    clientSession.client_socket.close()  # Close the socket

if __name__ == "__main__":
    main()
