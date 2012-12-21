
import thread
from Queue import Queue,Empty
from tcp2 import TCPServer


class TwoWayQueueSocket():
    """ A two way Queue interface for the GameEngine end of the twowayqueue """
    def __init__(self,incoming, outgoing):
        self.incoming = incoming
        self.outgoing = outgoing
        
    def put(self,data):
        self.outgoing.put(data)
    
    def get(self, block = True):
        return self.incoming.get(block)

class TwoWayQueue:
    """ A two way queue to connnect a gui on the local machine """
    
    def __init__(self):
        self.outgoing = Queue()
        self.incoming = Queue()
        self.serverSocket = TwoWayQueueSocket(self.incoming, self.outgoing)
        self.clientSocket = TwoWayQueueSocket(self.outgoing, self.incoming)
        self.serverConnected = False
        self.clientConnected = False
        
    def serverConnect(self):
        self.serverConnected = True
        return self.serverSocket
    
    def clientConnect(self):
        self.clientConnected = True
        return self.clientSocket
    
class GameQueue(Queue):
    """ a command queue including a twowayqueue for local gui and a TCPqueue for remote clients """
    
    def __init__(self,host="Localhost"):
        Queue.__init__(self)
        self.tcp = TCPServer(host)
        self.local = TwoWayQueue()
        
    def monitorIncoming(self):
        thread.start_new_thread(self.monitorTCP,())
        thread.start_new_thread(self.monitorLocal,())
        
    def monitorTCP(self):
        while 1:
            self.tcp.ismore.wait()
            try:
                #socketID, data = self.tcp.get()
                self.put(self.tcp.get())
            except Empty:
                pass
            
        
    def monitorLocal(self):
        while 1:
            self.put((0,self.local.incoming.get()))
            
    def clientConnect(self):
        return self.local.clientConnect()
    
    def isConnected(self):
        return self.local.clientConnected
    
    def broadcast(self,data):
        self.tcp.put(data)
        self.local.serverSocket.put(data)
        
    def putLocal(self,data):
        self.local.serverSocket.put(data)
        
    def putTCP(self,id,data):
        self.tcp.putIndiv(id, data)
    