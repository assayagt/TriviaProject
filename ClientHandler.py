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
    
    def contGame(self):
        self.continueGame.set()

    def manageGame(self):
        while not self.server.getWinnerFound() and self.server.enoughConnected() and self.started:
            timeOfQuest = time.time() #just for statistics
            self.recvClientAnswer()
            timeOfAns = time.time() #just for statistics

            if self.answer is not None: #Can be removed when notify added
                # Check if the answer is correct
                if self.server.checkResponse(self.answer):
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