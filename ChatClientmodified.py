#OPTCC.PY

import socket   # Import socket module
import sys   # Import system module
from datetime import datetime
import threading  # Import datetime module for timestamping

# Initialize global variables for statistics tracking
start_time = None
number_of_messages_sent = 0
number_of_messages_received = 0
number_of_characters_sent = 0
number_of_characters_received = 0

def get_hello_string(ip, port, nickname, client_id):
    """
    Returns a JSON-formatted string representing the start of chat session.

    Parameters:
        ip (str): The IP address used to establish connection with server.
        port (int): The port number used to establish connection with server.
        nickname (str): The user's chosen nickname.
        client_id (str): A unique identifier for the client.

    Returns:
        str: A JSON-formatted string representing the start of chat session.
     """
    timestamp = datetime.now()  # Get current timestamp
    return f"""{{ChatClient started with server IP: {ip}, port: {port}, nickname: {nickname}, client ID: {client_id}, Date/Time: {timestamp}}}"""
def get_nickname_string(nickname, client_id):
    """
    Constructs a JSON string representing the user's nickname and client ID.
    
    Args:
        nickname (str): The user's chosen nickname for the chat application.
        client_id (int): A unique identifier for the client instance.
    
    Returns:
        str: A JSON string with the user's nickname, client ID, and timestamp.
    """
    timestamp = datetime.now()  # Get current UTC timestamp
    return f"""{{"type": "nickname", "nickname": {nickname}, "clientID": {client_id}, "timestamp": "{timestamp}"}}"""

def get_message_string(nickname, message):
    """
    Returns a JSON-formatted string representing the user's sent message.

    Parameters:
        nickname (str): The user's chosen nickname.
        message (str): The content of the user's sent message.

    Returns:
        str: A JSON-formatted string representing the user's sent message.
     """
    timestamp = datetime.now()  # Get current timestamp
    return f"""{{"type": "message", "nickname": "{nickname}", "message": "{message}", "timestamp": "{timestamp}"}}"""

def get_broadcast_string(nickname, message):
    """
    Returns a JSON-formatted string representing the received broadcasted message.

    Parameters:
        nickname (str): The sender's chosen nickname.
        message (str): The content of the sent message.

    Returns:
        str: A JSON-formatted string representing the received broadcasted message.
     """
    timestamp = datetime.now()  # Get current timestamp
    return f"""{{"type": "broadcast", "nickname": "{nickname}", "message": "{message}", "timestamp": "{timestamp}"}}"""

def get_disconnect_string(nickname, client_id):
    """
    Returns a JSON-formatted string representing the user's disconnection request.

    Parameters:
        nickname (str): The user's chosen nickname.
        client_id (str): A unique identifier for the client.

    Returns:
        str: A JSON-formatted string representing the user's disconnection request.
     """
    timestamp = datetime.now()  # Get current timestamp
    return f"""{{"type": "disconnect", "nickname": "{nickname}", "clientID": "{client_id}", "timestamp": "{timestamp}"}}"""

def print_summary():
    """
    Prints a summary of the chat session statistics.
     """
    end_time = datetime.now()  # Get current timestamp for end time
    print(f'Summary: start: {start_time}, end:{end_time}, msg sent:{number_of_messages_sent},msg rcv:{number_of_messages_received}, char sent: {number_of_characters_sent}, char rcv: {number_of_characters_received}')

def read_from_server(clientSocket):
    """
    Reads incoming message from the server and updates statistics.
     """
    global number_of_messages_received, number_of_characters_received  # Access global variables for update
    while True:
        serverSentence = clientSocket.recv(1024)   # Receive data from the server
        if not serverSentence:
            break
        serverSentence = serverSentence.decode()  # Decode received bytes to string

        number_of_messages_received += 1  # Increment message count
        number_of_characters_received += len(serverSentence)   # Update character count

        print('FROM SERVER:', serverSentence)   # Print received message to console

def main():
    """
    Main function that handles command-line arguments and sets up the chat session.
     """
    global start_time, number_of_messages_sent, number_of_messages_received, number_of_characters_sent, number_of_characters_received  # Access global variables for update

    if len(sys.argv) != 4:
        print("ERR - arg {x}")
        exit()

    ip = socket.gethostbyname(sys.argv[1])  # Get IP address from hostname provided as command-line argument
    port = int(sys.argv[2])  # Convert port number to integer type
    nickname = sys.argv[3]   # Set user's chosen nickname from command-line argument

    client_id = input("Enter your unique identifier: ")  # Prompt user for their unique identifier and assign it to variable 'client_id'

    # Create socket and connect to server
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create a TCP/IP socket object
    clientSocket.connect((ip, port))  # Establish connection with the server using provided IP address and port number

    start_time = datetime.now()  # Get current timestamp for start time
    
    # Send the nickname and client ID to the server using the get_nickname_string function
    nickname_string = get_nickname_string(nickname, client_id)
    clientSocket.send(nickname_string.encode())
    print(nickname_string)  # Optionally print the sent JSON-formatted string to the console

    t1 = threading.Thread(target=read_from_server, args=[clientSocket])  # Create a separate thread for reading from server
    t1.start()  # Start the thread

    while True:
        clientSentence = input('Enter message:\n')  # Prompt user for their sent message and assign it to variable 'clientSentence'

        if clientSentence.lower() == "disconnect":  # Check if user entered command to disconnect from chat session
            break  # Exit loop and proceed with further steps in program execution flow

        message_string = get_message_string(nickname, clientSentence)   # Generate JSON-formatted string representing user's sent message using helper function 'get_message_string()'

        clientSocket.send(message_string.encode())  # Send generated JSON-formatted string to server over established TCP/IP connection

        number_of_messages_sent += len(clientSentence)  # Increment count of sent messages by user in current chat session
        number_of_characters_sent += len(message_string)   # Update total character count for all sent messages by user in current chat session

    clientSocket.send(get_disconnect_string(nickname, client_id).encode())  # Send JSON-formatted string representing user's disconnection request to server over established TCP/IP connection using helper function 'get_disconnect_string()'

    t1.join()  # Wait for the thread to finish

    print_summary()  # Print chat session summary to console
    clientSocket.close()  # Close the socket

if __name__ == "__main__":
    main()
