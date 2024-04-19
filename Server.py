import random
import socket
import struct
import time
import threading
from ClientHandler import ClientHandler

class Server:
    # Constants
    BUFFER_SIZE = 1024
    WAITING_TIME = 10  # Time to wait in the waiting state (in seconds)
    UDP_PORT = 13117
    MAGIC_COOKIE = 0xabcddcba
    MESSAGE_TYPE = 0x2
    SERVER_PORT = 12345
    SERVER_NAME = "TeamMysticServer".ljust(32, '\0')  # Make the server name 32 characters long
    POSSIBLE_TRUE = ['Y', 'T', '1']
    POSSIBLE_FALSE = ['N', 'F', '0']

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

    def __init__(self):
        self.clientHandlers = []
        self.winner_found = False
        self.winner_name = None
        self.currentCorrectAnswer = None
        self.gameTime = threading.Event()
        self.countDisqs = 0
        self.timeOut = 0

    def initUDP(self):
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udpSocket.bind((socket.gethostbyname(socket.gethostname()), self.UDP_PORT))
        return udpSocket

    def createTCPsocket(self):
        tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_socket.bind(('', self.SERVER_PORT))
        tcp_server_socket.listen(5)
        return tcp_server_socket

    def waitForClients(self, tcpSocekt, udpSocket):
        print("Server started listening on IP address " + socket.gethostbyname(socket.gethostname()))
        self.resetTimer()
        while True:
            if (time.time() > self.timeOut):
                tcpSocekt.close()
                break
            self.broadcastMessage(udpSocket)
            time.sleep(1)
    
    def resetTimer(self):
        self.timeOut = time.time() + 10

    def broadcastMessage(self, udpSocket):
        message = struct.pack("!Ic32sH", self.MAGIC_COOKIE, bytes([self.MESSAGE_TYPE]), self.SERVER_NAME.encode(), self.SERVER_PORT)
        udpSocket.sendto(message, ('<broadcast>', self.UDP_PORT))

    def acceptClients(self, tcpSocket):
        while True:
            try:
                clientSocket, addr = tcpSocket.accept()
            except:
                # stop receiving clients
                return
            self.resetTimer()
            clientHandler = ClientHandler(clientSocket, self)
            clientThread = threading.Thread(target=clientHandler.Run)
            clientThread.start()
            self.clientHandlers.append(clientHandler)

    def getRandomQuestion(self):
        # Choose one random trivia question
        random_question = random.choice(self.trivia_questions)
        random_question_to_send = random_question["question"]
        random_question_to_send = f"\nTrue or false: {random_question_to_send}"
        self.setCorrectAnswer(random_question)
        return random_question_to_send
    
    def setCorrectAnswer(self, random_question):
        self.currentCorrectAnswer = self.trivia_questions[self.trivia_questions.index(random_question)]['is_true']
    
    def initializeGame(self):
        if len(self.clientHandlers) < 1:
            print("No clients connected to this trivia...")
            return
        player_names = ["Player" + str(index + 1) + ": " + client.getPlayerName() + "\n" for index, client in enumerate(self.clientHandlers)]
        welcome_message = f"Welcome to the Mystic server, where we are answering trivia questions about Aston Villa FC.\n {' '.join(player_names)}"
        
        for client in self.clientHandlers:
            try:
                client.sendInfoToClient(welcome_message)
            except:
                break
        print(welcome_message)

    def handleGameMode(self):
        random_question_to_print = self.getRandomQuestion()
        for client in self.clientHandlers:
            try:
                client.sendInfoToClient(random_question_to_print)
            except:
                break
            if not client.getIfStarted():
                client.startGame()
        print(random_question_to_print)

        self.gameTime.wait(self.WAITING_TIME)
        if not self.winner_found and not self.countDisqs == len(self.clientHandlers):
            self.sendTimeoutMsg()
    
    def sendTimeoutMsg(self):
        msg = "\nTime is up. You'll get a new question."
        for client in self.clientHandlers:
            client.sendInfoToClient(msg)
        print(msg)


    def checkResponse(self, response):
        return response in self.POSSIBLE_TRUE and self.currentCorrectAnswer or response in self.POSSIBLE_FALSE and not self.currentCorrectAnswer

    def announceWinner(self, winner_name):
        self.winner_found = True
        self.winner_name = winner_name
        print(f"\n{winner_name} is correct! {winner_name} wins!")
        # Broadcast message to all clients about the winner
        winner_message = f"\n{winner_name} is correct! {winner_name} wins!"
        for other_client in self.clientHandlers:
            try:
                other_client.endGame()
                other_client.sendInfoToClient(winner_message)
            except:
                continue
        self.gameTime.set()

    def announceDisqualify(self):
        self.countDisqs += 1
        return self.countDisqs == len(self.clientHandlers)
    
    def releaseDisqs(self):
        disqMsg = "\nYou are all wrong and disqualified, but I'll give you another chance :)\n"
        print(disqMsg)
        for client in self.clientHandlers:
            client.contGame()
            client.sendInfoToClient(disqMsg)
        self.gameTime.set()
        

    def clearHandlers(self):
        # Close all client sockets
        end_message = f"Game over!\nCongratulations to the winner: {self.winner_name}"
        for client in self.clientHandlers:
            try:
                client.resetAnswer()
                client.sendInfoToClient(end_message)
                client.shutDownSocket()
                client.closeSocket()
            except Exception as e:
                print(f"Error closing client socket: {e}")
                continue
        self.clientHandlers = []

    def getWinnerFound(self):
        return self.winner_found
    
    def resetGame(self):
        self.currentCorrectAnswer = None
        self.gameTime.clear()
        self.countDisqs = 0
    
    def resetWinner(self):
        self.winner_found = False
        self.winner_name = None


def Main():
    server = Server()
    udpSocekt = server.initUDP()
    while True:
        tcpSocket = server.createTCPsocket()
        acceptClientsThread = threading.Thread(target=server.acceptClients, args=(tcpSocket,))
        acceptClientsThread.start()
        server.waitForClients(tcpSocket, udpSocekt)
        server.initializeGame()
        while not server.getWinnerFound():
            server.handleGameMode()
            server.resetGame()
        server.clearHandlers()
        server.resetWinner()
        print("Game over, sending out offer requests...")


if __name__ == '__main__':
    Main()