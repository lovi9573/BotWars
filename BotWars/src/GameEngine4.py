#TODO: change parentFrame to a FiFo queue in Servergui

import random
import pickle
import time
import copy
import math
import thread
from GameQueue import GameQueue
import BotWars  
from Queue import Queue,Empty

from Wrappers import *
from Wrappers import BotWrapper



class GameEngine(object):
    playersDict = {}
    STARTHEALTH = 100
    MAXDAMAGE = 20
    VERSION = 4
    
#@TODO: Change parentFrame to a two way queue that has a flag for gui connected.
    def __init__(self,parentFrame=None,playArea=[1000,650],host="localhost",verbose=True):
        self.VERBOSE=BotWars.VERBOSE
        self.activePlayers = []
        self.playersDict = {}
        #self.parentFrame = parentFrame
        #self.userCommandServer = UserCommandServer(host)
        self.botCommands = Queue()
        self.isRunning = False
        self.queue = GameQueue(host)
        self.playArea = playArea
        self.SLEEPTIME = 0.5
        self.WOF = 10
        self.round = 1
        self.game = 0
        self.currentPoints = 0
        #A dictionary of understood commands in the format
        # Incoming command , (response command, data collector or function)
        self.commandDict = {"run":("",self.run),
                            "setSleepTime":("",self.setSleepTime),
                            "setWoF":("",self.setWoF),
                            "reset":("",self.reset),
                            "sendStats":("",self.sendStats),
                            "getAvailableBots":("setAvailableBots",self.getAvailableBots),
                            "botCommand" : ("",self.botCommand),
                            "getInit":("init",self.packageAvatars)}
 
    def connectGui(self):
        """Connect a gui to this GameEngine's command queue"""
        return self.queue.clientConnect()

 
    def loadBots(self,botlist):
        """import the bot class from the given module list(filenames)""" 
        self.players = botlist
        #Create Bots into a temporary array
        bot_Basket =[]
        for player in self.players:
            bot_Basket.append(BotWrapper(player,self))
        
        # Test and Create dictionary of screen name-->BotWrapper
        for botwrapper in bot_Basket:
            if botwrapper.test():
                self.playersDict[botwrapper.getName()] = botwrapper
                botwrapper.setWoF(self.WOF)
                
        # Create a list of active players     
        self.activePlayers = copy.copy(self.playersDict.keys())
        self.setPlayerPositions(self.playArea,70)
        thread.start_new_thread(self.processCommands, ())
        print "--------------Bots Loaded -----------------"
        
    def getPlayersDict(self):
        return copy.copy(self.playersDict)
    
    
#==========================================================================================
#======================================GAME METHODS =======================================
#==========================================================================================
        
    def doLookRound(self,plyr):
        """ Allow the given bot to look in one direction to find enemies """
        plyrobj = self.playersDict[plyr]
        view = View(plyrobj.getPosition(),plyrobj.getLookDirection(),self.WOF,plyrobj.getName())
        foundObjs = self.findObjects(view)
        for o in foundObjs:
            plyrobj.setLookResults(o)
        return view
            
    def doCommandStage(self):
        """Get Commands from TCP/IP Server and distribute to recipient bot"""
        #@todo: This needs a rewrite to use the GameQueue structure instead of the user command server.
        ismore = True
        while ismore:
            try:
                name,cmd = self.botCommands.get(False)
            except Empty:
                ismore = False
            if ismore and name in self.playersDict.keys():
                self.playersDict[name].command(cmd)
    
    
    
    def doPrepareRound(self,plyr):
        """Call for plyr to prepare and return their stance""" 
        plyrobj = self.playersDict[plyr]
        stance = plyrobj.prepare(self.round)
        return stance
    
    def doMoveRound(self,plyr):
        """Allow the given player to move on the field  """
        #TODO: optimize
        plyrobj = self.playersDict[plyr]
        movedir = plyrobj.getMoveDirection()
        #translationDict = {"N":(0,35),"W":(-35,0),"S":(0,-35),"E":(35,0)}
        if (movedir !=0): #plyrstance.isA("Move"): All bots can move every round
            dx =dy = 0
            xp,yp = plyrobj.getPosition()
            #check for collisions
            collision = False
            plyrpos = GameObject(position = [xp,yp])
            plyrpos.translate(GameObject(movedir,35).calcCoordinates())
            for otherplyrobj in self.playersDict.values():
                xo,yo = otherplyrobj.getPosition()
                dist = plyrpos.getDistance([xo,yo])
                #TODO:  distance calculations are off....float accuraccy
                if dist<140 and plyrobj.getName() != otherplyrobj.getName():
                    collision = True
            if plyrpos.position[0]<70 or plyrpos.position[0]>930 or plyrpos.position[1]<70 or plyrpos.position[1]>580:
                collision = True
            if not collision:
                #dx,dy = translationDict[plyrstance.type]
                plyrobj.setPosition(plyrpos.getCoordinates())
                if (self.VERBOSE == True):
                    #print plyr, [xp,yp],plyrpos.position," --->", otherplyrobj.getName(), [xo,yo], "=", dist  
                    print plyr ,"moves from",[xp,yp],"to",plyrobj.getPosition()
                return plyrobj.getAvatar()
        return None
                
    def doFireRound(self,plyr):
        """Allow the given player to fire """
        plyrobj = self.playersDict[plyr]
        plyrstance = plyrobj.getStance()
        #   FIRING   #
        if plyrstance.isA("Fire"):
            plyrobj.botstats.add("numFires",1)
            target = plyrobj.getTarget()
            hitobj = None
            dmg = 0
            if (self.VERBOSE == True):
                print plyr ," shoots ", target.distance,"units in the direction",target.direction," and hits position",target.position
            #   CHECK FOR ANYONE IN VICINITY   #
            for enemy in self.activePlayers:
                enemyobj = self.playersDict[enemy]
                if target.getDistance(enemyobj.position)<71:
                    dmg = 0-random.randint(0,plyrobj.getModifier("maxDamage"))
                    eStance = enemyobj.getStance()
                    #   HIT TARGET IS GUARDING   #
                    if eStance.isA("Guard"):
                        enemyobj.botstats.add("numGuardsOnFire" ,1)
                        if eStance.isA(plyrstance.type):
                            enemyobj.botstats.add("numGuardsCorrect",1)
                            dmg = dmg*enemyobj.getModifier("guardPercentageOn")
                        else:
                            dmg = float(dmg)*enemyobj.getModifier("guardPercentageOff")
                        dmg = int(dmg)
                    #   HIT TARGET IS FIRING   #
                    else:
                        if dmg == -20:
                            dmg *=2
                    #  checking for minimum damage  #
                    if dmg > 0-plyrobj.getModifier("minDamage"):
                        dmg = 0-plyrobj.getModifier("minDamage")
                    if (self.VERBOSE == True):
                        print enemy, "was hit by ",plyr, " for ", dmg, " damage!!"
                    #  normalize incoming attack angle   #
                    inComingDirection = target.direction + 180
                    while inComingDirection >360:
                        inComingDirection -=360
                    #  NOTIFY HIT TARGET OF DAMAGE  #
                    Ehealth = enemyobj.adjustHealth(Damage(eStance.type,dmg,inComingDirection))
                    hitobj = enemyobj.getAvatar()
                    if Ehealth <=0 and Ehealth - dmg >0:
                        plyrobj.botstats.add("kills" ,1)
                    plyrobj.botstats.add("damageDone",dmg)
            return [Shot(plyrobj.position,target.position,plyrstance.type,dmg),hitobj]
        #   GUARDING   #
        elif plyrobj.getStance().isA("Guard"):
            plyrobj.botstats.add("numGuards",1)
            return [None,None]
        else:
            return [None,None]
                 
    def resolveRound(self):
        """ Tie up any loose ends at the end of each round """
        outPlayers = []
        
        #Dispense Environment damage
        if self.round >200:
            for plyr in self.activePlayers:
                self.playersDict[plyr].adjustHealth(Damage("Environment",-5,90))
            
        
        #Find dead players
        for plyr in self.activePlayers:
            if self.playersDict[plyr].getHealth() <1:
                outPlayers.append(plyr)
        #Delete dead Players and update visually
        for p in outPlayers:
            self.playersDict[p].botstats.add("points",self.currentPoints)
            self.playersDict[p].botstats.tallyTournamentStats()
            self.activePlayers.remove(p)
            if 1:
                self.send("updateBot",-1,(self.playersDict[p].getAvatar(),))
        self.currentPoints += len(outPlayers)
                
        #notify of endRound            
        for plyrobj in self.playersDict.values():
            plyrobj.endRound(self.round)
        if (self.VERBOSE == True):
            print "end of round:",self.round
        self.round +=1
   
    def reset(self,y):
        """Reset the game engine for another game """
        self.activePlayers = copy.copy(self.playersDict.keys())
        self.round = 1
        self.currentPoints =0
        #reset healths
        for plyrobj in self.playersDict.values():
            plyrobj.reset(self.STARTHEALTH)
            self.setPlayerPositions(self.playArea, 80)
        self.send("reset",-1,(None,))
               
    def run(self,y):
        """ This begins a game and follows it through to the end """
        self.VERBOSE=BotWars.VERBOSE
        self.isRunning = True
        self.send("init",-1,self.packageAvatars())
        self.setWoF((self.WOF,)) #This is used here to broadcast the wof to the gui's
        while self.isGameOn():
            print "=============================== Round ",self.round," ============================="
            #=============== Dispatch Commands ===========
            self.doCommandStage()
            #================ Look Round=================
            time.sleep(self.SLEEPTIME*2)
            for plyr in self.activePlayers:
                view = self.doLookRound(plyr)
                if (self.VERBOSE == True):
                    print plyr," looks toward ",view.getTheta()," degrees"
                if 1:
                    self.send("drawView",-1,(view,))# self.playArea))
                    #self.send("updatePlayer",self.playersDict[plyr].getAvatar(),(None,None)]))
                time.sleep(self.SLEEPTIME)
            time.sleep(self.SLEEPTIME*2)
            #================= Prepare Round==================    
            time.sleep(self.SLEEPTIME*2)
            for plyr in self.activePlayers:
                stance = self.doPrepareRound(plyr)
                if (self.VERBOSE == True):
                    print plyr," is going to ",stance
                time.sleep(self.SLEEPTIME)
            time.sleep(self.SLEEPTIME*2)
            #===================Move Round====================
            for plyr in self.activePlayers:
                avatar = self.doMoveRound(plyr)
                if avatar:
                    if (self.VERBOSE == True):
                        #print plyr," moves by ",avatar.getPosition()
                        pass
                    if 1:
                        self.send("updateBot",-1,(avatar,))
            #===================Fire Round====================
            for plyr in self.activePlayers:
                shot,hitobj = self.doFireRound(plyr)
                if shot:
                    self.send("drawShot",-1,(shot,hitobj))
                if hitobj:
                    self.send("updateBot",-1,(hitobj,))
                    
                time.sleep(self.SLEEPTIME)
            time.sleep(self.SLEEPTIME*2)
            #===================Resolve Round=================
            self.resolveRound()
        for plyrobj in self.playersDict.values():
            plyrobj.endGame()
        self.displayStats()
        if 1:
            self.send("displayStats",-1,self.packageStats())
            #self.parentFrame.displayStats()
        self.isRunning = False
            
    def findObjects(self,view):
        """Returns a list of objects seen by the given view """
        foundObjects = []
        for targetobj in self.playersDict.values():
            if view.isInView(targetobj.position):
                xp,yp = targetobj.position
                x0,y0 = view.position
                dx = xp-x0 
                dy = yp-y0 
                foundObjects.append(GameObject(direction = view.getVisibleAngle(xp,yp),\
                                                   distance = math.sqrt((dx)**2+(dy)**2),\
                                                   measuredFrom = [x0,y0],\
                                                   measuredFromName = view.name,\
                                                   name = targetobj.getName(),\
                                                   health = targetobj.getHealth(),
                                                   type = "Enemy"))
        foundObjects.append(view.getRectIntersection([0,0],self.playArea))
        return foundObjects
                   
    def isGameOn(self):
        """Determines whether the current game should contiue running """
        if len(self.activePlayers) >=2:
            return True
        elif len(self.activePlayers) == 1:
            self.playersDict[self.activePlayers[0]].botstats.add("numFires",1)
            self.playersDict[self.activePlayers[0]].botstats.add("points",self.currentPoints +1)
            self.playersDict[self.activePlayers[0]].botstats.tallyTournamentStats()
            return False
        else:
            return False
            
    def setPlayerPositions(self,area,threshold):
        for plyr in self.activePlayers:
            ok = False
            xp = 0
            yp = 0
            while not ok:
                xp = random.randint(threshold,area[0]-threshold)
                yp = random.randint(threshold,area[1]-threshold)
                ok = True
                for check in self.activePlayers:
                    xc,yc = self.playersDict[check].getPosition()
                    if math.sqrt((xp-xc)**2+(yp-yc)**2) < 2*threshold:
                        ok = False
            self.playersDict[plyr].setPosition([xp,yp])

    def setSleepTime(self,y):
        self.SLEEPTIME=y[0]
        self.send("updateSleepTime",-1,(self.SLEEPTIME,))
        
    def setWoF(self,y):
        self.WOF = y[0]
        for plyrobj in self.playersDict.values():
            plyrobj.setWoF(self.WOF)
        self.send("updateWoF",-1,(self.WOF,))
 
#==========================================================================================
#====================================== I/O METHODS =======================================
#========================================================================================== 
    
    def send(self,msg,id,datum):
        '''This function pickles and sends messages to gui's
            id's: -1 is broadcast , 0 is local gui head, # is socket that made the request'''
        data = pickle.dumps((msg,0,datum))
        if id <0:
            self.queue.broadcast(data)
        elif id ==0:
            self.queue.putLocal(data)
        else:
            self.queue.putTCP(id, data)
    
    def packageAvatars(self,y=None):
        x=[]
        for plyr in self.activePlayers:
            x.append(self.playersDict[plyr].getAvatar())
        return x
    
    def packageStats(self):
        x=[]
        for plyr in self.playersDict.keys():
            x.append(self.playersDict[plyr].getStats())
        return x

 #   def processCommand(self,command):
#        self.commandDict[command]()
        
    def processCommands(self):
        self.queue.monitorIncoming()
        while 1:
            id,data = self.queue.get()
            cmd,id,args = pickle.loads(data)
            print cmd
            if (cmd == "run" and self.isRunning == False):
                #@TODO: Perhaps remove the new thread here and scatter calls to processCommands(non blocking version) throughout the run method.
                self.reset(None)
                thread.start_new_thread(self.commandDict[cmd][1],(args))
            elif cmd in self.commandDict.keys():
                if self.commandDict[cmd][0] =="":
                    self.commandDict[cmd][1](args) 
                else:
                    self.send("setAvailableBots",id,self.commandDict[cmd][1](args))

    def displayStats(self):
        print " * "+ "Player" + "\t\t" + "Dmg" + "\t" + "Kills" + "\t" + \
            "Rounds" + "\t" + "Fired" + "\t" + "Guarded" + "\t" + "% firing"+"\t"+"Pts"+"\t"+"Merits\n"
        for plyrobj in self.playersDict.values():
            print plyrobj.botstats.getstat("All"),"\n"
            
    def drawHealIcon(self,avatar):
        self.send("updateBot",-1,(avatar,))
        
    def sendStats(self,type,*x):
        if 1:
            self.send("displayStats",-1,self.packageStats())
            #self.parentFrame.displayStats()
        
    def getAvailableBots(self,y):
        return self.playersDict.keys()

    def botCommand(self, args):
        self.botCommands.put(args)
            
if __name__ == "__main__":
    x = GameEngine(verbose = True)
    t = float(raw_input("Enter sleep time between actions: (0 for error testing)(0.3 to see what's happening)"))
    x.setSleepTime(0)
    while 1:
        x.run(1)
        x.reset(1)