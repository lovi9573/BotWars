#A simple dialog box that displays player statistics


from Tkinter import *
import tkFont
import os
from socket import *
import BotWars

class InitDialog(Toplevel):
    
    def __init__(self,master,callback):
        self.callback = callback
        Toplevel.__init__(self)        
        self.wheight = 600
        self.wwidth = 800
        self.isserver = IntVar()
        Radiobutton(self,text = "Server",variable = self.isserver, value = 1).grid()
        Radiobutton(self,text = "Client", variable = self.isserver, value = 0).grid()
        Label(self, text = "Server IP:").grid()
        self.host = StringVar()
        if(os.name == 'nt'):
            hostname, aliaslist, ipaddrlist = gethostbyaddr(gethostname())
        elif(os.name == 'posix'):
            hostname, aliaslist, ipaddrlist = gethostbyname_ex('localhost')
        if BotWars.DEBUG:
            print "IPs on this machine: " ,ipaddrlist
        self.host.set(ipaddrlist[-1])
        self.hostentry = Entry(self, textvariable = self.host)
        self.hostentry.grid()
        self.submit = Button(self,command = self.sendData, text = "Submit")
        self.submit.grid()
        
    
    def sendData(self):
        self.callback(bool(self.isserver.get()), self.hostentry.get())
        self.destroy()
        

class ServerDialog(Toplevel):
    
    def __init__(self,master, callback):
        self.callback = callback 
        self.botlist = []
        Toplevel.__init__(self)
        self.wheight = 600
        self.wwidth = 800  
        #Graphical server or not
        self.isServer = IntVar()
        Checkbutton(self,text = "Graphical Server", variable = self.isServer).grid()      
        #Number of bots per player to enter
        Label(self, text = "number of bots per player:").grid()
        self.nBots = IntVar()
        Scale(self, orient = HORIZONTAL, to = 10 , variable = self.nBots).grid()        
        #get list of filenames matching pattern <name>_bot.py
        filelist = os.listdir(os.getcwd())
        for file in filelist:
            if (file.find("_bot.py") != -1 and file.find("_bot.pyc") == -1):
                self.botlist.append(filelist.pop(filelist.index(file)).rstrip(".py"))
        
        Label(self, text = "select bots to enter into the game:").grid()
        self.botsdict = {}
        for bot in self.botlist:
            self.botsdict[bot] = IntVar()
            Checkbutton(self, text = bot, variable = self.botsdict[bot] ).grid()
        
        self.submit = Button(self,command = self.sendData, text = "Submit")
        self.submit.grid()
    
    def sendData(self):
        self.botentrylist = []
        for name in self.botsdict.keys():
            if bool(self.botsdict[name].get()):
                for i in range(0,self.nBots.get()):
                    self.botentrylist.append(name)    
        self.callback(self.botentrylist,bool(self.isServer.get()))
        self.destroy()

class ClientDialog(Toplevel):
    
    def __init__(self,master,list,callback):
        self.callback = callback
        Toplevel.__init__(self)
        self.l = Listbox(self,height = 20 )
        for name in list:
            self.l.insert(END,name)
        self.l.grid()
        
        self.submit = Button(self,command = self.sendData, text = "Submit")
        self.submit.grid()
        
    def sendData(self):
        self.callback(self.l.get(ACTIVE))
        self.destroy()

class StatsDialog(Toplevel):
    
    def __init__(self,master,sorttype, *statsList):
        global DEBUG
        if DEBUG:
            print "preinit"
        Toplevel.__init__(self)
        if DEBUG:
            print "post-toplevel.init"
        self.statsList = statsList
        
        self.sortType = sorttype
        if self.sortType == "Points":
            self.getType = "Tournament"
        else:
            self.getType = "Round"
        
        self.wheight = 20* (len(statsList)+1)+13
        self.wwidth = 1200
        self.canvas = Canvas(self,bd = 2,relief = "ridge",height = self.wheight,width=2400)
        self.canvas.grid()
        self.showStats()
        
    def showStats(self):
        y = 20
        x = 10
        statsFont = tkFont.Font(size = y-2)
        header = " * "+ "Player" + "\t\t" + "Dmg" + "\t" + "Kills" + "\t" + \
            "Rounds" + "\t" + "Fired" + "\t" + "Guarded" + "\t" + "% firing"+"\t"+"Pts"+"\t"+"Merits"
        self.canvas.create_text(x,y,anchor=W,font=statsFont,fill = "#CA0", text = header)
        self.playersDict = {}
        players = []
        for obj in self.statsList:
            players.append(obj.name)
            self.playersDict[obj.name]=obj
        players.sort(self.comparePlayers)
        
        for plyr in players:
            plyrobj = self.playersDict[plyr]
            y += 20
            name = plyr
            if len(plyr)>12:
                name = plyr[:9]+"..."
            name += " "*(12-len(name))
            
            report = " * "+ name + "\t" + plyrobj.getstat("All",self.getType)
            self.canvas.create_text(x,y,anchor=W,font = statsFont,text = report)
           
    def comparePlayers(self,x,y):
        if self.sortType == "Rounds":
            xSurvive = self.playersDict[x].getstat("roundsSurvived",self.getType)
            ySurvive = self.playersDict[y].getstat("roundsSurvived",self.getType)
            return ySurvive - xSurvive
        
        if self.sortType == "Points":
            xPts = self.playersDict[x].getstat("points",self.getType)
            yPts = self.playersDict[y].getstat("points",self.getType)
            return yPts - xPts
        
class SettingsDialog(Toplevel):
    
    def __init__(self,master,Dict):
        Toplevel.__init__(self,master)
        
        self.meritsDict = Dict
        self.values = {}
        self.wheight = 20* (len(Dict.keys())+1)+13
        self.wwidth = 1200
        #self.canvas = Canvas(self,bd = 2,relief = "ridge",height = self.wheight,width=self.wwidth)
        #self.canvas.grid()
        self.createEntries()


    def createEntries(self):
        y=0
        Label(self,text = "Variable").grid(row=0,column=0)
        Label(self,text = "Performance").grid(row=0,column=1)
        Label(self,text = "Result").grid(row=0,column=2)
        for key in self.meritsDict.keys():
            y+=1
            self.values[key]=[]
            x=0
            Label(self,text=key).grid(column=x,row=y)            
            for value in self.meritsDict[key]:
                x+=1
                a=self.values[key]
                a.append(StringVar())
                a[x-1].set(value)
                Entry(self,textvariable=a[x-1]).grid(column=x,row=y)
        Button(self,text="Accept",command=self.accept).grid(column=x+1,row=y+1)
            
    def accept(self):
        for key in self.values.keys():
            for value in self.values[key]:
                try:
                    a = float(value)
                except ValueError, ve:
                    value = None    