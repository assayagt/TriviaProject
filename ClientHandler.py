import socket
import threading
from bcolors import bcolors
import time

class ClientHandler:
    
    def __init__(self, clientSocket, server):
        self.clientSocket = clientSocket
        self.server = server
        self.continueGame = threading.Event()
        self.playerName = ""
        self.bufferSize = 1024
        self.semaphore = threading.Semaphore(0)
        self.answer = None
        self.started = False
        

    def Run(self):
        '''
        thread function for running each player. waiting until game is started
        '''
        self.recvPlayerName()
        self.waitGameStart()
        self.manageGame()

    def recvPlayerName(self):
        try:
            data = self.clientSocket.recv(self.bufferSize)
        except:
            return

        self.playerName = data.decode()

    def getPlayerName(self):
        return self.playerName

    def getIfStarted(self):
        return self.started

    def sendInfoToClient(self, msgInfo):
        self.clientSocket.sendall(msgInfo.encode())

    def waitGameStart(self):
        self.semaphore.acquire()

    def startGame(self):
        self.semaphore.release()
        self.started = True
    
    def endGame(self):
        self.started = False

    def closeSocket(self):
        return self.clientSocket.close()
    
    def shutDownSocket(self):
        self.clientSocket.shutdown(socket.SHUT_RDWR)

    def recvClientAnswer(self):
        try:
            self.answer = self.clientSocket.recv(self.bufferSize).decode()
        except:
            return

    def getAnswer(self):
        return self.answer
    
    def resetAnswer(self):
        self.answer = None

    def getContGame(self):
        return self.continueGame
    
    def contGame(self):
        self.continueGame.set()
    
    def resetContGame(self):
        self.continueGame.clear()

    def manageGame(self):
        '''
        manage game for each client and handle the connection with the client
        '''
        while not self.server.getWinnerFound() and self.server.enoughConnected() and self.started:
            timeOfQuest = time.time() #just for statistics
            self.recvClientAnswer()
            timeOfAns = time.time() #just for statistics

            if self.answer is not None: #Can be removed when notify added
                # Check if the answer is correct
                response = self.server.checkResponse(self.answer)
                print(response)
                if response is None:
                    try:
                        self.sendInfoToClient(f"\n{bcolors.WARNING}Your input is invalid. Please eneter T,Y,1 for true and F,N,0 for false.{bcolors.ENDC}\n")
                    except:
                        continue
                elif response:
                    self.server.announceWinner(self.getPlayerName())
                    totalTime = timeOfAns - timeOfQuest
                    self.server.updateFastestTimeQuestion(totalTime, self.getPlayerName()) #statistics
                else:
                    wrongMsg = f"\n{bcolors.FAIL}You are wrong. try next time.{bcolors.ENDC}"
                    self.server.updateWrongQuestion() #statistics
                    try:
                        self.sendInfoToClient(wrongMsg)
                    except:
                        break
                    lastDisq = self.server.announceDisqualify()
                    if lastDisq:
                        self.server.releaseDisqs()
                    else:
                        self.continueGame.wait()