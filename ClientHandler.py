import time
from socket import socket
import threading


class ClientHandler:
    playerName = ""
    bufferSize = 1024
    sem = threading.Semaphore(0)
    started = False
    def __init__(self, clientSocket1):
        self.clientSocket = clientSocket1
        

    def Run(self):

        self.recvPlayerName()
        self.waitForStart()

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

    def waitForStart(self):
        self.sem.acquire()

    def startGame(self):
        self.sem.release()
        self.started = True

    def closeSocket(self):
        return self.clientSocket.close()
    
    def setSocketTimeout(self, time):
        self.clientSocket.settimeout(time)
    
