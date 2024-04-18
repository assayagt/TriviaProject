import random
import socket
import struct
import time
import threading
from newClientHandler import ClientHandler

# Constants
BUFFER_SIZE = 1024
WAITING_TIME = 10  # Time to wait in the waiting state (in seconds)
UDP_PORT = 13117
MAGIC_COOKIE = 0xabcddcba
MESSAGE_TYPE = 0x2
SERVER_PORT = 12345
SERVER_NAME = "TeamMysticServer".ljust(32, '\0')  # Make the server name 32 characters long
clientHandlers = []
POSSIBLE_TRUE = ['Y', 'T', '1']
POSSIBLE_FALSE = ['N', 'F', '0']
# Event to signal the end of waiting time
waiting_time_over = threading.Event()

serverPort = 12345
hostName = socket.gethostname()
IPAddress = socket.gethostbyname(hostName)

# List of trivia questions about Aston Villa FC
trivia_questions = [
    {"question": "Aston Villa FC was founded in 1874.", "is_true": True},
    {"question": "Aston Villa has won the FA Cup 8 times.", "is_true": True},
    {"question": "The club's home ground is Villa Park.", "is_true": True},
    {"question": "Aston Villa FC has never won the Premier League.", "is_true": False},
    {"question": "The club's nickname is 'The Lions'.", "is_true": True},
    {"question": "Aston Villa has won the UEFA Champions League.", "is_true": False},
    {"question": "Villa's record signing is Darren Bent.", "is_true": False},
    {"question": "Aston Villa holds the record for most consecutive top-flight league titles.", "is_true": True},
    {"question": "The club's mascot is a lion named Hercules.", "is_true": True},
    {"question": "Aston Villa was one of the founding members of the Football League in 1888.", "is_true": True},
    {"question": "The team's traditional kit colors are claret and blue.", "is_true": True},
    {"question": "Aston Villa FC has never won the League Cup.", "is_true": False},
    {"question": "The Holte End is the largest single stand at Villa Park.", "is_true": True},
    {"question": "The club's all-time leading goalscorer is Peter Withe.", "is_true": False},
    {"question": "Aston Villa's main rivalry is with Birmingham City.", "is_true": True},
    {"question": "The team's current captain is Jack Grealish.", "is_true": True},
    {"question": "Aston Villa has been relegated from the Premier League multiple times.", "is_true": True},
    {"question": "The club's highest finish in the Premier League era is 4th place.", "is_true": True},
    {"question": "Aston Villa has won the European Cup.", "is_true": True},
    {"question": "The club's first manager was George Ramsay.", "is_true": True}
]

def initUDP():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udpSocket.settimeout(0.2)
    udpSocket.bind(('localhost', UDP_PORT))
    return udpSocket

def createTCPsocket():
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server_socket.bind(('localhost', serverPort))
    tcp_server_socket.listen(5)
    return tcp_server_socket

def waitForClients(tcpSocekt, udpSocket):
    print("Server started listening on IP address " + IPAddress)
    timeOut = time.time() + 10  
    while True:
        if (time.time() > timeOut):
            tcpSocekt.close()
            break
        broadcastMessage(udpSocket)
        time.sleep(1)

def broadcastMessage(udpSocket):
    message = struct.pack("!Ic32sH", MAGIC_COOKIE, bytes([MESSAGE_TYPE]), SERVER_NAME.encode(), SERVER_PORT)
    udpSocket.sendto(message, ('<broadcast>', UDP_PORT))

def acceptClients(tcpSocket):
    while True:
        try:
            clientSocket, addr = tcpSocket.accept()
        except:
            # stop receiving clients
            return
        clientHandler = ClientHandler(clientSocket)
        clientThread = threading.Thread(target=clientHandler.Run)
        clientThread.start()
        clientHandlers.append(clientHandler)

def getRandomQuestion():
    # Choose one random trivia question
    random_question = random.choice(trivia_questions)
    random_question_to_send = random_question["question"]
    random_question_to_send = f"True or false: {random_question_to_send}"
    return random_question, random_question_to_send

def manageGame():
    if len(clientHandlers) < 1:
        print("No clients connected to this trivia...")
        return
    player_names = ["Player" + str(index + 1) + ": " + client.getPlayerName() + "\n" for index, client in enumerate(clientHandlers)]
    welcome_message = f"Welcome to the Mystic server, where we are answering trivia questions about Aston Villa FC.\n {' '.join(player_names)}"
    
    for client in clientHandlers:
        try:
            client.sendInfoToClient(welcome_message)
        except:
            break
    print(welcome_message)
    
    winner_found = False
    while not winner_found:
        random_question, random_question_to_print = getRandomQuestion()
        for client in clientHandlers:
            try:
                client.sendInfoToClient(random_question_to_print)
            except:
                break
            client.startGame()
        print(random_question_to_print)

        time.sleep(5)

        
        winner_name = ""

        sem = threading.Semaphore(0)
        sem.acquire()

        # Receive and check answers from clients
        response = clientHandlers[0].getAnswer()

        if response is not None: #Can be removed when notify added
            # Check if the answer is correct
            if response in POSSIBLE_TRUE and trivia_questions[trivia_questions.index(random_question)]['is_true']:
                winner_name = client.getPlayerName()
                print(f"\n{winner_name} is correct! {winner_name} wins!")
                winner_found = True
                # Broadcast message to all clients about the winner
                winner_message = f"\n{winner_name} is correct! {winner_name} wins!"
                for other_client in clientHandlers:
                    try:
                        other_client.endGame()
                        other_client.sendInfoToClient(winner_message)
                    except:
                        continue
            elif response in POSSIBLE_FALSE and not trivia_questions[trivia_questions.index(random_question)]['is_true']:
                winner_name = client.getPlayerName()
                print(f"\n{winner_name} is correct! {winner_name} wins!")
                winner_found = True
                # Broadcast message to all clients about the winner
                winner_message = f"\n{winner_name} is correct! {client.getPlayerName()} wins!"
                for other_client in clientHandlers:
                    try:
                        other_client.endGame()
                        other_client.sendInfoToClient(winner_message)
                    except:
                        continue
            else:
                print(f"Incorrect answer from {client.getPlayerName()}. They are disqualified.")
        


        # Need to fix that so there will be a new question
        if not winner_found:
            end_message = "\nNo correct answers were received, so there will be another question."
        else:
            end_message = f"Game over!\nCongratulations to the winner: {winner_name}"

        for client in clientHandlers:
            try:
                client.resetAnswer()
                client.sendInfoToClient(end_message)
            except:
                continue
        time.sleep(1)


def Main():
    udpSocekt = initUDP()
    while True:
        tcpSocket = createTCPsocket()
        acceptClientsThread = threading.Thread(target=acceptClients, args=(tcpSocket,))
        acceptClientsThread.start()
        waitForClients(tcpSocket, udpSocekt)
        manageGame()
        print("Game over, sending out offer requests...")


if __name__ == '__main__':
    Main()