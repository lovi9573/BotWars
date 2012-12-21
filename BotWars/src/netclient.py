import socket 
import thread
import select
import threading 
import time
import pickle
import BotWars

class NetClient(object):
    
    def __init__(self,host = "",username = ""):
        if not host:
            host = raw_input("Connect to ip: ").strip("\r")
        if not username:
            self.userName = raw_input("Connect to bot: ").strip("\r") 
        else:
            self.userName = username
        port = 50001 
        self.size = 4096 
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.s.connect((host,port))
        self.nCommands = 2
        self.commandList = []
        
    def put(self,input):
        if input not in self.commandList and len(self.commandList)<self.nCommands:
            self.commandList.append(input)
        if input in self.commandList:
            msg = self.userName+"@"+input 
            self.s.send(msg) 
            data = self.s.recv(self.size) 
            return '--------------:', data," :--------------" 
        #s.close() 

    def setUserName(self,username = ""):
        self.userName = username


##  GameFrame networking Client used to recive and request graphics updates from server.
class TCPClient(object):


    def __init__(self,server):
        self.sendables = []
        self.sendablesLock = threading.Lock()
        self.sendablesEvent = threading.Event()
        self.commands = []
        self.commandLock = threading.Lock()
        self.host = server  #localhost" #raw_input("Connect to ip: ")
        #self.parent = parent 
        self.ismore = threading.Event()
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
                    while cmd[-1] != "\0":
                        cmd += socket.recv(self.size)
                    self.commandLock.acquire()
                    self.queueCommand(cmd[:-1])
                    if BotWars.VERBOSE:
                        print "client recieve: ", pickle.loads(cmd[:-1]),"\n"
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
                    print "Client sent: " , pickle.loads(x), "\n"
                    self.s.sendall(x+"\0")
                else:
                    self.s.sendall(self.sendables.pop(0)+"\0")
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
        self.commandLock.release()
        return x
        
        
        
if __name__ == "__main__":
    #netClient()
    pass