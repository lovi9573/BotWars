from Wrappers import *
import random
import BotWars  

class Bot(object):
    nameCount = 0
    
    def __init__(self,health,parentclass):
        self.health = health
        self.parent = parentclass
        self.name = "JLO"+ str(Bot.nameCount)
        self.enemies = []
        self.roundsSinceLook = []
        self.lookingForKnownEnemy = -1
        Bot.nameCount += 1
        self.currentStance = Stance("Fire","Burning")
        self.scanPoint = 0
        self.priorityLook = 0
        self.type = "Piercing"
        self.madeItFullRound = False
        self.shouldMove = False
        self.moveDir = "N"
        
    def command(self,command):
        if command == "Burning":
            self.type = "Burning"
        if command == "Piercing":
            self.type = "Piercing"
    
    def endRound(self,n):
        for i in range(len(self.roundsSinceLook)):
            self.roundsSinceLook[i] += 1

    #@Purpose: Informs the game of your bot's flag color
    #@return: 3-tuple: in the form (R,G,B) 0-255 for each color
    def getColor(self):
        return (0,200,200)
    
    def getImages(self):
        return {"Guard":"JG.gif","Fire":"JF.gif"}
    
    def getMoveDirection(self):
        return random.randint(9,360)
        
    def getName(self):
        return self.name
    
    def getLookDirection(self):
        if self.priorityLook:
            x = self.priorityLook
            self.priorityLook = 0
            return x
        for i in range(len(self.roundsSinceLook)):
            if self.roundsSinceLook[i] >5:
                self.roundsSinceLook[i] = 0
                self.lookingForKnownEnemy = i
                return self.enemies[i].getPolarCoordinates()[1]
        if self.madeItFullRound and self.enemies:
            enemy = random.choice(self.enemies)
            return enemy.getPolarCoordinates()[1]
        self.scanPoint += 2*self.WoF
        if self.scanPoint >360:
            self.madeItFullRound = True
        return self.scanPoint
    
    def setLookResults(self,obj):
        if obj:
            if obj.type == "Enemy" and obj.name != self.name:
                alreadyHave = False
                for e in self.enemies:
                    if e.name == obj.name:
                        alreadyHave = True
                        id = e
                if obj.health <= 0 and alreadyHave:
                    i = self.enemies.index(id)
                    self.enemies.remove(id)
                    self.roundsSinceLook.pop(i)
                elif alreadyHave:
                    i = self.enemies.index(id)
                    self.enemies[i]=obj
                    self.roundsSinceLook[i] = 0
                elif obj.health >0:
                    self.enemies.append(obj)
                    self.roundsSinceLook.append(0)
        if self.lookingForKnownEnemy >=0 and not obj:
            self.enemies.pop(self.lookingForKnownEnemy)
            self.roundsSinceLook.pop(self.lookingForKnownEnemy)
            self.madeItFullRound = False
            self.scanPoint = 0
        self.lookingForKnownEnemy = -1
  
    def getEnemies(self):
        return self.enemies
                
    def prepare(self,n):
        a = "Guard"
        b = self.type
        if 0:
            a == "Move"
            b = self.moveDir
        elif self.enemies:
            a = "Fire"
            b = random.choice(("Piercing","Burning"))
        self.currentStance = Stance(a,b)
        return self.currentStance
    
    def getTarget(self):
        if (BotWars.DEBUG == True):
            print "__",self.name,"__  target requested from: "
        if len(self.enemies)>0:
            for e in self.enemies:
                if BotWars.VERBOSE:
                    print "##",e
        if len(self.enemies)>0:
            target = self.enemies[0]
            return target
        else:
            x = random.randint(0,360)
            y = random.randint(60,400)
            return GameObject(x,y)
    
    def adjustHealth(self,damage):
        self.health += damage.getDamage()
        match = False
        for obj in self.enemies:
            if obj.direction == damage.getDirection():
                match = True
        if match == False:
            self.priorityLook = damage.getDirection()
        if self.health <50:
            self.parent.HealMe()
        if BotWars.DEBUG:
            print "lllllllllllllllll",damage.action,damage.getDamage(),self.name,self.health
        if damage.action == "Fire":
            moveDir = {-1:"W",0:"S",1:"E",2:"N",3:"W",4:"S"}
            self.shouldMove = True
            region = int((int(damage.getDirection())-45)/90)
            self.moveDir = moveDir[region]
            
        return self.health
    
    def getHealth(self):
        return self.health
    
    def getStance(self):
        return self.currentStance
    
    def setWoF(self,WoF):
        if BotWars.DEBUG:
            print "Thank you for letting bot know: WoF =:",WoF
        self.WoF = WoF
    
    def reset(self,h):
        self.health = h
        self.enemies = []
        self.roundsSinceLook = []
        self.madeItFullRound = False
        self.shouldMove = False
        