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
        self.exit = False
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
        while not self.exit:
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
                        data = socket.recv(9)
                        size = int(data[:9])
                        data = data[9:]
                        bytesrecvd = len(data)
                        while bytesrecvd < size:
                            buffsize = self.size
                            if ((size-bytesrecvd) < self.size):
                                buffsize = size-bytesrecvd
                                d = socket.recv(buffsize)
                                #print "data:",d,"buffsize:",buffsize
                                data += d    
                            else:
                                data +=  socket.recv(buffsize)
                            bytesrecvd = len(data)    
                        self.indivRequestsLock.acquire()
                        self.indivRequests.append((socket.fileno(),data))
                        if BotWars.VERBOSE:
                            #print "Server Recieve: " +pickle.loads(data[:-1])[0]
                            pass
                        self.indivRequestsLock.release()
                        self.ismore.set()
                    self.socketsLock.release()
                except error, ae:
                    self.handleError(socket)
                    
    def serviceClientsOut(self):
        while not self.exit:
            
            self.commandsEvent.wait()
            try:
                r,w,e = select.select([],self.sockets.values(),[],0)
                #TODO: check the writable sockets against self.sockets and remove any nonwritable from self.sockets
                self.socketsLock.acquire()
                for id,sock in self.sockets.iteritems():
                    if sock not in w:
                        del self.sockets[id]       
                self.socketsLock.release()
                print "writable sockets:",w
                ###dispatch individual commands
                self.indivCommandsLock.acquire()
                while self.indivCommands:
                    id, data = self.indivCommands.pop(0)
                    size = self.prefixData(data)
                    self.socketsLock.acquire()
                    socket = self.sockets[id]
                    socket.sendall(size + data)
                    self.socketsLock.release()
                self.indivCommandsLock.release()           
                
                ### dispatch commands to each socket connected
                self.commandLock.acquire()
                while self.commands:
                    self.socketsLock.acquire()
                    data = self.commands.pop(0)
                    size = self.prefixData(data)
                    for socket in self.sockets.values():
                        socket.sendall(size + data)
                    self.socketsLock.release()
                    if 1:
                        #print "server send: "+size + data
                        pass
                self.commandLock.release()
                self.commandsEvent.clear()
            ###capture disconnects and remove those sockets from the list
            ### release any locked locks
            ### kill service thread if no more sockets remain
            #TODO: Fix me
            except None: #error , se:
                self.handleError(socket)
    
    def prefixData(self,data):
        size = str(len(data))
        ndigits = len(size)
        filler = ""
        for i in range (0,9-ndigits):
            filler +="0"
        return filler+size        
                
    def handleError(self,socket):
        print "socket error from: ",socket.getpeername()
        if self.commandLock.locked():
            self.commandLock.release()
        if self.socketsLock.locked():
            self.socketsLock.release()
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
        print "bad socket cleaned up.  Service threads exiting: ",quit
        if quit:
            thread.exit()
            

    def serverStart(self):
        ###  Always accepts incoming connections ####
        while not self.exit: 
            client, address = self.s.accept() 
            print "Accepting connection from ",address
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

    def killServer(self):
        self.exit = True

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
                    data = socket.recv(9)
                    size = int(data[:9])
                    data = data[9:]
                    bytesrecvd = len(data)
                    
                    while bytesrecvd < size:
                        #print "hello"
                        #print "size:",size,"bytesrecvd:",bytesrecvd
                        buffsize = self.size
                        if ((size-bytesrecvd) < self.size):
                            buffsize = size-bytesrecvd
                            d = socket.recv(buffsize)
                            #print "data:",d,"buffsize:",buffsize
                            data += d
                        else:
                            data += socket.recv(buffsize)
                        bytesrecvd = len(data)
                    self.commandLock.acquire()
                    self.queueCommand(data)
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
                data = self.sendables.pop(0)
                size = self.prefixData(data)
                #print "Client sent: " , size+data
                self.s.sendall(size + data)
            self.sendablesEvent.clear()    
            self.sendablesLock.release()   
            
    def prefixData(self,data):
        size = str(len(data))
        ndigits = len(size)
        filler = ""
        for i in range (0,9-ndigits):
            filler +="0"
        return filler+size   

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
    for x in range(0,200):
        for i in range(0,random.randint(1,random.randint(1,2000))):
            data += chr(random.randint(0,255))
        #print "data",x,":",data
        print x
        datalog.append(data)
        server.put(data)
        data = ""
        while client.ismore.isSet():
            try:
                d = client.get()
                assert d in datalog
                datalog.remove(d)
            except AssertionError:
                print "AssertionError"
                print "get data is: ",d
    print "Server to Client Done"
    
    data = ""
    datalog = []
    print "B"
    for x in range(0,200):
        for i in range(0,random.randint(1,random.randint(1,2000))):
            data += chr(random.randint(0,255))
        #print "data",x,":",data
        print x
        datalog.append(data)
        client.put(data)
        data = ""
        while server.ismore.isSet():
            try:
                id,d = server.get()
                assert d in datalog
                datalog.remove(d)
            except AssertionError:
                print "AssertionError"
                print "get data is: ",d
            except Empty:
                pass
    print "Client to Server Done"
    server.killServer()       
    