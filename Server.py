import random
import socket
import struct
import time
import threading
from ClientHandler import ClientHandler
from bcolors import bcolors
from Questions import trivia_questions

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

    def __init__(self):
        self.clientHandlers = []
        self.winner_found = False
        self.winner_name = None
        self.currentCorrectAnswer = None
        self.gameTime = threading.Event()
        self.countDisqs = 0
        self.timeOut = 0

        # init list of trivia questions about Israel:
        self.trivia_questions = trivia_questions

        # init variables for statistics:
        self.currentQuestIndex = -1
        self.fastestPlayerMsg = None
    
   
    def initUDP(self):
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udpSocket.bind((socket.gethostbyname(socket.gethostname()), self.UDP_PORT))
        return udpSocket

    def initTCPsocket(self):
        tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_socket.bind(('', self.SERVER_PORT))
        tcp_server_socket.listen(5)
        return tcp_server_socket

    def waitForConnections(self, tcpSocekt, udpSocket):
        print("Server started listening on IP address " + socket.gethostbyname(socket.gethostname()))
        self.resetTimer()
        while True:
            if (time.time() > self.timeOut):
                #close the socket which accepts new clients
                tcpSocekt.close()
                break
            self.broadcastMessage(udpSocket)
            time.sleep(1)
    
    def resetTimer(self):
        self.timeOut = time.time() + self.WAITING_TIME

    def broadcastMessage(self, udpSocket):
        message = struct.pack("!Ic32sH", self.MAGIC_COOKIE, bytes([self.MESSAGE_TYPE]), self.SERVER_NAME.encode(), self.SERVER_PORT)
        udpSocket.sendto(message, ('<broadcast>', self.UDP_PORT))

    def acceptConnections(self, tcpSocket):
        while True:
            try:
                clientSocket, addr = tcpSocket.accept()
            except:
                # stop receiving clients
                return
            if clientSocket:
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
        self.setQuestionIndex(random_question)
        return random_question_to_send
    
    def setCorrectAnswer(self, random_question):
        self.currentCorrectAnswer = self.trivia_questions[self.trivia_questions.index(random_question)]['is_true']
    
    def setQuestionIndex(self, random_question):
        self.currentQuestIndex = self.trivia_questions.index(random_question)

    def enoughConnected(self):
        return len(self.clientHandlers) >= 1

    
    def initializeGame(self):
        welcome_message = f"Welcome to the Mystic server, where we are answering trivia questions about Israel.\n"
        clientsToRemove = []
        for client in self.clientHandlers:
            try:
                client.sendInfoToClient(welcome_message)
            except ConnectionResetError:
                clientsToRemove.append(client)
        
        for other_client in clientsToRemove:
            if other_client in self.clientHandlers:
                self.clientHandlers.remove(other_client)
                del other_client
        
        player_names = ["Player" + str(index + 1) + ": " + client.getPlayerName() + "\n" for index, client in enumerate(self.clientHandlers)]
        fullMsg = welcome_message + " ".join(player_names)
        for client in self.clientHandlers:
            try:
                client.sendInfoToClient(''.join(player_names))
            except:
                continue
        print(fullMsg)

    def handleGameMode(self):
        random_question_to_print = self.getRandomQuestion()
        clientsToRemove = []
        for client in self.clientHandlers:
            try:
                client.sendInfoToClient(random_question_to_print)
            except ConnectionResetError:
                clientsToRemove.append(client)
                continue
            if not client.getIfStarted():
                client.startGame()

        time.sleep(0.1)
        for other_client in clientsToRemove:
            if other_client in self.clientHandlers:
                self.clientHandlers.remove(other_client)
                del other_client
        print(random_question_to_print)

        self.gameTime.wait(self.WAITING_TIME)
        if not self.winner_found and not self.countDisqs == len(self.clientHandlers):
            self.sendTimeoutMsg()
    
    def sendTimeoutMsg(self):
        msg = "\nTime is up. You'll get a new question."
        clientsToRemove = []
        for client in self.clientHandlers:
            try:
                client.sendInfoToClient(msg)
            except ConnectionResetError:
                clientsToRemove.append(client)
        
        time.sleep(0.1)
        for other_client in clientsToRemove:
            if other_client in self.clientHandlers:
                self.clientHandlers.remove(other_client)
                del other_client
        print(msg)

    def checkResponse(self, response):
        return response in self.POSSIBLE_TRUE and self.currentCorrectAnswer or response in self.POSSIBLE_FALSE and not self.currentCorrectAnswer

    def announceWinner(self, winner_name):
        clientsToRemove = []
        self.winner_found = True
        self.winner_name = winner_name
        print(f"\n{bcolors.OKGREEN}{winner_name} is correct! {winner_name} wins!{bcolors.ENDC}")
        # Broadcast message to all clients about the winner
        winner_message = f"\n{bcolors.OKGREEN}{winner_name} is correct! {winner_name} wins!{bcolors.ENDC}"
        for other_client in self.clientHandlers:
            try:
                other_client.endGame()
                other_client.sendInfoToClient(winner_message)
            except ConnectionResetError:
                clientsToRemove.append(other_client)
                continue
        
        time.sleep(0.1)

        for other_client in clientsToRemove:
            if other_client in self.clientHandlers:
                self.clientHandlers.remove(other_client)
                del other_client
        time.sleep(0.1)
        self.gameTime.set()
        

    def announceDisqualify(self):
        self.countDisqs += 1
        return self.countDisqs == len(self.clientHandlers)
    
    def releaseDisqs(self):
        disqMsg = f"\n{bcolors.WARNING}You are all wrong and disqualified, but I'll give you another chance :){bcolors.ENDC}\n"
        print(disqMsg)
        clientsToRemove = []
        for client in self.clientHandlers:
            client.contGame()
            try:
                client.sendInfoToClient(disqMsg)
            except ConnectionResetError:
                clientsToRemove.append(client)
        
        time.sleep(0.1)
        for other_client in clientsToRemove:
            if other_client in self.clientHandlers:
                self.clientHandlers.remove(other_client)
                del other_client

        self.gameTime.set()
        

    def clearHandlers(self, end_message):
        # Close all client sockets
        for client in self.clientHandlers:
            try:
                client.resetAnswer()
                client.sendInfoToClient(end_message)
                client.shutDownSocket()
                client.closeSocket()
                del client
            except Exception as e:
                print(f"Error closing client socket: {e}")
                continue
        self.clientHandlers = []

    def getWinnerFound(self):
        return self.winner_found
    
    def getWinnerName(self):
        return self.winner_name
    
    def resetGame(self):
        self.currentCorrectAnswer = None
        self.gameTime.clear()
        self.countDisqs = 0
    
    def resetWinner(self):
        self.winner_found = False
        self.winner_name = None

    def sendFunStatistics(self):
        mostWrongQuest = self.printMostWrongQuest()
        statsMsg = f"\n{bcolors.OKCYAN}{bcolors.UNDERLINE}Some fun Statistics:{bcolors.ENDC}"
        if self.fastestPlayerMsg != None or mostWrongQuest != None:
            print(statsMsg)
        
            if self.fastestPlayerMsg !=None:
                print(self.fastestPlayerMsg)
            if mostWrongQuest != None:
                print(mostWrongQuest)
            for client in self.clientHandlers:
                try:
                    client.sendInfoToClient(statsMsg)
                    if self.fastestPlayerMsg:
                        client.sendInfoToClient(self.fastestPlayerMsg)
                    
                    if mostWrongQuest != None:
                        client.sendInfoToClient(mostWrongQuest)
                    else: 
                        client.sendInfoToClient("\n")
                except:
                    break

    def updateWrongQuestion(self):
        self.trivia_questions[self.currentQuestIndex]['wrongCounter'] +=1

    def updateFastestTimeQuestion(self, totalTime, fastestClientName):
        self.fastestPlayerMsg = None
        if self.trivia_questions[self.currentQuestIndex]['fastestTime'] > totalTime:
            self.trivia_questions[self.currentQuestIndex]['fastestTime'] = totalTime
            self.fastestPlayerMsg = f"\n- {bcolors.OKCYAN} {fastestClientName} is the fastest Chief of Staff of all times to answer correctly on this question!{bcolors.ENDC}\n"

    def printMostWrongQuest(self):
        questStatsMsg = None
        max_wrong_question = max(self.trivia_questions, key=lambda x: x['wrongCounter'])
        numberOfMistakes = self.trivia_questions[self.trivia_questions.index(max_wrong_question)]['wrongCounter']
        if numberOfMistakes != 0:
            hardestQuest = max_wrong_question['question']
            questStatsMsg = f"\n- {bcolors.OKCYAN}The hardest question with most mistakes is: {hardestQuest}\n total mistakes: {numberOfMistakes}{bcolors.ENDC}\n\n"
        return questStatsMsg
        

def Main():
    server = Server()
    udpSocekt = server.initUDP()
    while True:
        tcpSocket = server.initTCPsocket()
        acceptConnectionsThread = threading.Thread(target=server.acceptConnections, args=(tcpSocket,))
        acceptConnectionsThread.start()
        server.waitForConnections(tcpSocket, udpSocekt)
        server.initializeGame()
        while not server.getWinnerFound() and server.enoughConnected():
            server.handleGameMode()
            server.resetGame()
        if server.enoughConnected():
            end_msg = f"{bcolors.OKBLUE}Game over!\nCongratulations to the winner: {server.getWinnerName()}{bcolors.ENDC}"
            server.sendFunStatistics()
            server.clearHandlers(end_msg)
            server.resetWinner()
        else:
            end_msg = f"{bcolors.WARNING}Unfortunately, there are not enough players to play the game.{bcolors.ENDC}"
            server.clearHandlers(end_msg)
            print(end_msg)
        print(f"{bcolors.OKBLUE}Game over, sending out offer requests...{bcolors.ENDC}")

if __name__ == '__main__':
    Main()


