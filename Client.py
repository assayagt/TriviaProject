import socket
import struct
import threading
import msvcrt

# Constants
SERVER_PORT = 12345
BUFFER_SIZE = 1024
SERVER_NAME = "Mystic"  # Assuming the server name extracted from the offer announcement

# Create an event object
terminate_event = threading.Event()

def createUDPSocket():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', 13117))
    return udp_socket

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
        
if __name__ == "__main__":
    print("Client started, listening for offer requests...")
    # Start a thread to listen for offer announcements
    udpSocket = createUDPSocket()
    while True:

        terminate_event.clear()

        try:
            server_ip, server_port = listen_for_offers(udpSocket)
        except:
            print("Cant find any proper offers, trying again.")
            continue

        
