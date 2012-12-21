#TODO:

import BotWars
from Wrappers import *
import random

class Bot(object):
    nameCount = 0
    
    
    def __init__(self,health,parentclass):
        self.health = health
        self.parent = parentclass
        self.name = "Kimo"+ str(Bot.nameCount)
        Bot.nameCount += 1
        self.currentStance = Stance("Fire","Burning")
        self.fireStatus = 0
        self.opponentposition =[212,65]
        self.moveCount = 0
        
    def adjustHealth(self,damage):
       self.health += damage.getDamage()
       return self.health
    
    def command(self,command):
        pass
    
    def endRound(self,n):
        if (BotWars.DEBUG == True):
            print self.health,"for ",self.name
        
    def endGame(self):
        self.fireStatus = 0
        self.opponentposition =[]
        self.moveCount = 0
    
    def getEnemies(self):
        return []
    
    def getHealth(self):
        return self.health
        
    def getLookDirection(self):
        return random.randint(0,360)
    
    def getMoveDirection(self):
        return random.randint(9,360)
    
    def getName(self):
        return self.name
    
    def getStance(self):
        return self.currentStance
    
    def getTarget(self):
        return GameObject(position = self.opponentposition)
    
    def prepare(self,n):
        if self.fireStatus == 1:
           self.fireStatus = 0
           self.currentStance = Stance("Fire","Piercing") 
        else:
            if self.moveCount < 4:
                self.currentStance = Stance("Move","N")    
                self.moveCount += 1
            else:
                self.currentStance = Stance("Move","S")
                self.moveCount = 8
                self.moveCount -= 1
                
        return self.currentStance
      
    def reset(self,h):
        self.health = h
        
    def setLookResults(self,obj):
        if obj:
            if (BotWars.DEBUG == True):
                print "from KimoBot: ",obj.name,obj.getCoordinates()
            self.opponentposition = obj.getCoordinates()
            if obj.type == "Enemy":
                self.fireStatus = 1
    
    def setWoF(self,WoF):
        pass
       
    def getImages(self):
        return{"Guard":"","Fire":""}
        
    