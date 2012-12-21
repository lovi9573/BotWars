'''
Created on Dec 29, 2009

@author: 373jlovitt
'''

import socket
import thread
import time
import select
import BotWars
from threading import Lock,Event
from socket import error
import pickle
import random
from Queue import *


TERMINATOR = "\0\0\0\0"

#GameEngine Graphics Server used to send out updates and recieve requests
#:  Identify which socket requests come in on and dispatch to those sockets.
class TCPServer(object):
    

    def __init__(self,host):
        global TERMINATOR
        self.term = TERMINATOR
    
        self.host = host 
        self.port = 50000 
        self.backlog = 5 
        self.size = 1024 
        self.commands = []
        self.commandLock = Lock()
        self.sockets = {}   # id, socket
        self.socketsLock = Lock()
        self.indivRequests = []  # [id,request]
        self.indivRequestsLock = Lock()
        self.indivCommands = []
        self.indivCommandsLock = Lock()
        self.commandsEvent = Event()
        self.ismore = Event()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.s.bind((self.host,self.port)) 
        self.s.listen(self.backlog)   
        thread.start_new_thread(self.serverStart, ())
        self.isServiceThread =False
        
        #self.uiStart()
         
    
    def serviceClientsIn(self):
        data = ""
        while 1:
            ### check the readable status of each socket(has client sent anything)
            #print "server in sleep"
            #time.sleep(.1) #needed to avoid a hang btween server/client?
            
            while not self.sockets:
                pass
            #self.socketsLock.acquire()
            r,w,e = select.select(self.sockets.values(),[],[],.1)
            #self.socketsLock.release()
            #print "serviceClientsIn loop"
            if r:  #Data has been sent on the following sockets
                try:
                    self.socketsLock.acquire()
                    for socket in r:
                        data = socket.recv(self.size)
                        while data[-4:] != self.term:
                            if BotWars.VERBOSE:
                                print "server retrieving rest of unsent data"
                            data +=  socket.recv(self.size)
                        self.indivRequestsLock.acquire()
                        self.indivRequests.append((socket.fileno(),data[:-4]))
                        if BotWars.VERBOSE:
                            #print "Server Recieve: " +pickle.loads(data[:-1])[0]
                            pass
                        self.indivRequestsLock.release()
                        self.ismore.set()
                    self.socketsLock.release()
                except error, ae:
                    self.handleError(socket)
                    
    def serviceClientsOut(self):
        while 1:
            
            self.commandsEvent.wait()
            try:
                ###dispatch individual commands
                self.indivCommandsLock.acquire()
                while self.indivCommands:
                    self.socketsLock.acquire()
                    socket = self.sockets[self.indivCommands[0][0]]
                    socket.sendall(self.indivCommands[0][1]+self.term)
                    self.socketsLock.release()
                    self.indivCommands.pop(0)
                self.indivCommandsLock.release()           
                
                ### dispatch commands to each socket connected
                self.commandLock.acquire()
                while self.commands:
                    self.socketsLock.acquire()
                    for socket in self.sockets.values():
                        socket.sendall(self.commands[0]+self.term)
                    self.socketsLock.release()
                    if BotWars.DEBUG:
                        print "server send: "+self.commands[0]
                        pass
                    self.commands.pop(0)
                self.commandLock.release()
                self.commandsEvent.clear()
            ###capture disconnects and remove those sockets from the list
            ### release any locked locks
            ### kill service thread if no more sockets remain
            except error , se:
                self.handleError(socket)
                
    def handleError(self,socket):
        print "socket error from: ",socket
        if self.commandLock.locked():
            self.commandLock.release()
        self.socketsLock.acquire()
        delID = 0
        for id,sock in self.sockets.iteritems():
            if sock == socket:
                delID = id
        del self.sockets[delID]
        if len(self.sockets.values())==0:
            quit = True
        else:
            quit = False
        self.socketsLock.release()
        if quit:
            thread.exit()
            

    def serverStart(self):
        ###  Always accepts incoming connections ####
        while 1: 
            client, address = self.s.accept() 
            if client:
                ### put new socket in list of sockets and determine ob zu restart service thread
                self.socketsLock.acquire()
                self.sockets[client.fileno()]=client
                self.socketsLock.release()
                client = None
                ###  restart service thread if necessary
                if not self.isServiceThread:
                    thread.start_new_thread(self.serviceClientsIn,())
                    thread.start_new_thread(self.serviceClientsOut,())
                    self.isServiceThread = True


    def put(self,cmd):
        self.commandLock.acquire()
        self.commands.append(cmd)
        self.commandLock.release()
        self.commandsEvent.set()
        
    def putIndiv(self,num,cmd):
        self.indivCommandsLock.acquire()
        self.indivCommands.append([num,cmd])
        self.indivCommandsLock.release()
        self.commandsEvent.set()

    def get(self):
        x = ""
        self.indivRequestsLock.acquire()
        if len(self.indivRequests)>0:
            x = self.indivRequests.pop(0)
            if len(self.indivRequests)==0:
                self.ismore.clear()            
        elif len(self.indivRequests)==0:
            self.ismore.clear()
            self.indivRequestsLock.release()
            raise Empty
        self.indivRequestsLock.release()
        print "TCPServer.get is returning", x
        return x
    

##  GameFrame networking Client used to recive and request graphics updates from server.
class TCPClient(object):


    def __init__(self,server):
        global TERMINATOR
        self.term = TERMINATOR
        self.sendables = []
        self.sendablesLock = Lock()
        self.sendablesEvent = Event()
        self.commands = []
        self.commandLock = Lock()
        self.host = server  #localhost" #raw_input("Connect to ip: ")
        #self.parent = parent 
        self.ismore = Event()
        self.port = 50000 
        self.size = 1024 
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.s.connect((self.host,self.port))
        #self.monitor()
        thread.start_new_thread(self.monitorIncoming, ())
        thread.start_new_thread(self.monitorOutgoing, ())       

    def monitorIncoming(self):
        while 1:
            r,w,e = select.select([self.s], [], [])
            
            ### check if anything has been sent
            if r:
                for socket in r:
                    cmd = socket.recv(self.size)
                    while cmd[-4:] != self.term:
                        cmd += socket.recv(self.size)
                    self.commandLock.acquire()
                    self.queueCommand(cmd[:-4])
                    #print "Client.monitorIncoming command list:",self.commands
                    if BotWars.VERBOSE:
                        #print "client recieve: ", pickle.loads(cmd[:-1]),"\n"
                        pass
                    self.ismore.set()
                    self.commandLock.release()
    
    def monitorOutgoing(self):
        while 1:
            
            self.sendablesEvent.wait()
            
            ###Send out requests    
            self.sendablesLock.acquire()
            while self.sendables:
                if BotWars.VERBOSE:
                    x = self.sendables.pop(0)
                    #print "Client sent: " , pickle.loads(x), "\n"
                    self.s.sendall(x+self.term)
                else:
                    self.s.sendall(self.sendables.pop(0)+self.term)
            self.sendablesEvent.clear()    
            self.sendablesLock.release()     

    def put(self,input):
        #msg = self.name+"_"+input 
        self.sendablesLock.acquire()
        self.sendables.append(input) 
        self.sendablesEvent.set() 
        self.sendablesLock.release()
        
    def queueCommand(self,cmd):
        #self.commandLock.acquire()
        self.commands.append(cmd)
        #self.commandLock.release()
    
    def get(self,dummy = True):
        x = ""
        self.commandLock.acquire()
        if len(self.commands)>0:
            x = self.commands.pop(0)
            if len(self.commands)==0:
                self.ismore.clear() 
        elif len(self.commands)==0:
            self.ismore.clear()
            self.commandLock.release()
            raise Empty
        self.commandLock.release()
        return x
        
        
if __name__ == '__main__' :
    server = TCPServer("Localhost")
    thread.start_new_thread(server.serverStart, ())
    client = TCPClient("Localhost")
    data = ""
    datalog = []
    print "A"
    for x in range(0,20):
        for i in range(0,random.randint(1,10)):
            data += chr(random.randint(0,255))
        #print "data",x,":",data
        datalog.append(data)
        server.put(data)
        data = ""
    gets = 0
    print "B"

    while client.ismore.isSet():
        try:
            d = client.get()
            dd = datalog.pop(0)
            assert d == dd
            #print "got data #",gets
            gets +=1
        except AssertionError:
            print "AssertionError"
            print "get data is: ",d
            print "datalog data is: ",dd
    print "Done"
            
    