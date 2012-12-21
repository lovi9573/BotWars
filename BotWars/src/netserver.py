import socket
import thread
import time
import select
import BotWars
from threading import Lock,Event
from socket import error
import pickle

class UserCommandServer(object):
    
    

    def __init__(self,host=''):
    
        self.host = host 
        self.port = 50001 
        self.backlog = 5 
        self.size = 4096 
        self.commands = []
        self.commandLock = Lock()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.s.bind((self.host,self.port)) 
        self.s.listen(self.backlog)   
        thread.start_new_thread(self.serverStart, ())
        
         
    
    def serviceClient(self,client,port):
        #standalone thread per client to service commands of form botname_command
        data = ""
        address = 'localhost'
        #client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        #client.connect((address,port))
        while data != "quit" and data != "quit all":
            data = client.recv(self.size) 
            if data and data != "quit":
                who,cmd = data.split("@") 
                if(BotWars.VERBOSE):
                    print "Command: ",cmd,", recieved for ",who
                self.commandLock.acquire()
                self.commands.append(data)
                self.commandLock.release()
                client.send("Command: "+cmd+", recieved for "+who) 
        client.close() 



    def serverStart(self):
        #Standalone Thread to listen for incoming connections
        while 1: 
            client, address = self.s.accept() 
            if client:
                returnVal = thread.start_new_thread(self.serviceClient, (client,self.port))
                client = None


    def uiStart(self):
        input = ""
        while input != "quit":
            input = raw_input("press any key to flush the queue.  type \"quit\" to quit")
            self.commandLock.acquire()
            for x in self.commands:
                print x,"\n"
            self.commands=[]
            self.commandLock.release()
        
    #Returns the next user command in the queue. Returns True as well if more commands are present.
    def get(self):
        x = ""
        isMore = False
        if len(self.commands)>0:
            self.commandLock.acquire()
            x = self.commands.pop(0)
            self.commandLock.release()
        if len(self.commands)>0:
            isMore = True
        return x,isMore
            
        
        
        
#GameEngine Graphics Server used to send out updates and recieve requests
#:  Identify which socket requests come in on and dispatch to those sockets.
class TCPServer(object):
    

    def __init__(self,host):
    
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
                        while data[-1] != "\0":
                            if BotWars.VERBOSE:
                                print "server retrieving rest of unsent data"
                            data +=  socket.recv(self.size)
                        self.indivRequestsLock.acquire()
                        self.indivRequests.append((socket.fileno(),data[:-1]))
                        if BotWars.VERBOSE:
                            print "Server Recieve: " +pickle.loads(data[:-1])[0]
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
                    socket.sendall(self.indivCommands[0][1]+"\0")
                    self.socketsLock.release()
                    self.indivCommands.pop(0)
                self.indivCommandsLock.release()           
                
                ### dispatch commands to each socket connected
                self.commandLock.acquire()
                while self.commands:
                    self.socketsLock.acquire()
                    for socket in self.sockets.values():
                        socket.sendall(self.commands[0]+"\0")
                    self.socketsLock.release()
                    if BotWars.DEBUG:
                        print "server send: "+pickle.loads(self.commands[0])[0]
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
        self.indivRequestsLock.acquire()
        self.indivRequests.append([num,cmd])
        self.indivRequestsLock.release()
        self.commandsEvent.set()

    def get(self):
        x = ""
        self.indivRequestsLock.acquire()
        if len(self.indivRequests)>0:
            x = self.indivRequests.pop(0)
        if len(self.indivRequests)==0:
            self.ismore.clear()
        self.indivRequestsLock.release()
        print "TCPServer.get is returning", x
        return x
    