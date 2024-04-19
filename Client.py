import socket
import struct
import threading
import msvcrt
import random

# Constants
BUFFER_SIZE = 1024
SERVER_NAME = "Mystic"  # Assuming the server name extracted from the offer announcement

chief_of_staff_names = [
    "Yaakov Dori",
    "Yigael Yadin",
    "Mordechai Maklef",
    "Moshe Dayan",
    "Haim Laskov",
    "Tzvi Tzur",
    "Yitzhak Rabin",
    "David Elazar",
    "Mordechai Gur",
    "Rafael Eitan",
    "Dan Shomron",
    "Ehud Barak",
    "Amnon Lipkin-Shahak",
    "Shaul Mofaz",
    "Moshe Ya'alon",
    "Dan Halutz",
    "Gabi Ashkenazi",
    "Benny Gantz",
    "Gadi Eizenkot",
    "Aviv Kochavi"
]

# Create an event object
terminate_event = threading.Event()

def createUDPSocket():
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', 13117))
        return udp_socket
    except OSError as e:
        print("\nError creating UDP socket")
        return None

# Function to listen for offer announcements
def listen_for_offers(udp_socket):
    # Receive offer message
    data, addr = udp_socket.recvfrom(BUFFER_SIZE)
    magic_cookie, message_type, server_name, server_port = struct.unpack("!Ic32sH", data)
    server_name = server_name.decode().strip('\x00')  # Remove null characters from the end
    if magic_cookie == 0xabcddcba and message_type == b'\x02':
        print(f"Received offer from server \"{server_name}\" at address {addr[0]}, attempting to connect...")
        # Start TCP connection
        return addr[0], server_port
        
# Function to establish TCP connection with the server
def connect_to_server(server_ip, server_port):
    try:
        # Create a TCP socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server
        tcp_socket.connect((server_ip, server_port))
        print("Connected!")

        # Send player name
        player_name = random.choice(chief_of_staff_names)  # Change this to the player's name
        tcp_socket.sendall(player_name.encode())
        
        return tcp_socket
    
    except Exception as e:
        print("\nFailed to connect to the server")
        return None

# Function to handle user input

def get_user_input(tcp_socket):
    while not terminate_event.is_set():
        if msvcrt.kbhit():
            try:
                tcp_socket.send(msvcrt.getche())
            except Exception as e:
                print(f"\nError sending data to server")
                break

# Function to handle receiving data from the server
def receive_data(tcp_socket):
    while not terminate_event.is_set():
        try:
            data = tcp_socket.recv(BUFFER_SIZE)
            if not data:
                print(data.decode())
                terminate_event.set()  # Signal termination
                tcp_socket.close()
                break
            print(data.decode())
        except Exception as e:
            break

# Function to handle game mode state
def game_mode(tcp_socket):
    # Receive welcome message from the server
    welcome_message = tcp_socket.recv(BUFFER_SIZE).decode()
    print(welcome_message)

    # Create threads for user input and receiving data from the server
    input_thread = threading.Thread(target=get_user_input, args=(tcp_socket,))
    receive_thread = threading.Thread(target=receive_data, args=(tcp_socket,))

    # Start the threads
    input_thread.start()
    receive_thread.start()

    # Wait for threads to complete
    input_thread.join()
    receive_thread.join()

if __name__ == "__main__":
    print("Client started, listening for offer requests...")
    
    while True:
        # Start a thread to listen for offer announcements
        udpSocket = createUDPSocket()

        if udpSocket is not None:
            terminate_event.clear()

            try:
                server_ip, server_port = listen_for_offers(udpSocket)
            except:
                print("Cant find any proper offers, trying again.")
                continue

            try:
                tcp_socket = connect_to_server(server_ip, server_port)
            except:
                print("Cant connect to server. looking for a new one")
                tcp_socket.close()
                continue

            try:
                if tcp_socket is not None:
                    udpSocket.close()
                game_mode(tcp_socket)
            except:
                print("Problem occurred in game, looking for new server")
                    
            print("Server disconnected, listening for offer requests...")
