import select
import time
import socket
import threading


class ClientHandler:
    playerName = ""
    bufferSize = 1024
    sem = threading.Semaphore(0)
    answer = None
    started = False
    def __init__(self, clientSocket, server):
        self.clientSocket = clientSocket
        self.server = server
        self.continueGame = threading.Event()
        

    def Run(self):

        self.recvPlayerName()
        self.waitForStart()
        #self.recvClientAnswer()
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

    def waitForStart(self):
        self.sem.acquire()

    def startGame(self):
        self.sem.release()
        self.started = True
    
    def endGame(self):
        self.started = False

    def closeSocket(self):
        return self.clientSocket.close()
    
    def shutDownSocket(self):
        self.clientSocket.shutdown(socket.SHUT_RDWR)

    def recvClientAnswer(self):
        while self.started:
            try:
                self.answer = self.clientSocket.recv(self.bufferSize).decode()
                break
            except:
                break

    def getAnswer(self):
        return self.answer
    
    def resetAnswer(self):
        self.answer = None
    
    def contGame(self):
        self.continueGame.set()

    def manageGame(self):
        while not self.server.getWinnerFound():

            self.recvClientAnswer()

            if self.answer is not None: #Can be removed when notify added
                # Check if the answer is correct
                if self.server.checkResponse(self.answer):
                    self.server.announceWinner(self.getPlayerName())
                else:
                    wrongMsg = "You are wrong. try next time."
                    self.sendInfoToClient(wrongMsg)
                    lastDisq = self.server.announceDisqualify()
                    if lastDisq:
                        self.server.releaseDisqs()
                    else:
                        self.continueGame.wait()




                    

            
