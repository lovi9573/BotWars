from Wrappers import *
import random
import BotWars

class Bot(object):
    nameCount = 0
    
    def __init__(self,health,parentclass):
        self.health = health
        self.parent = parentclass
        self.name = "BOB"+ str(Bot.nameCount)
        self.enemies = []
        Bot.nameCount += 1
        self.currentStance = Stance("Fire","Burning")
        
    def endRound(self,n):
        pass
    
    def getImages(self):
        return {"Guard":"","Fire":""}
    
    def getMoveDirection(self):
        if self.name == "BOB0" :
            return 0
        else:
            return random.randint(1,360)
 
    def getColor(self):
        return (255,150,150)
        
    def getName(self):
        return self.name
    
    def getLookDirection(self):
        return random.randint(0,360)
    
    def setLookResults(self,obj):
        if obj:
            if obj.type == "Enemy" and obj.name != self.name:
                alreadyHave = False
                for e in self.enemies:
                    if e.name == obj.name:
                        alreadyHave = True
                        id = e
                if obj.health <= 0 and alreadyHave:
                    self.enemies.remove(id)
                elif alreadyHave:
                    id = obj
                elif obj.health >0:
                    self.enemies.append(obj)
  
    def getEnemies(self):
        return self.enemies
                
    def prepare(self,n):
        a = random.choice(["Fire","Guard"])
        b = random.choice(["Burning","Piercing"])
        self.currentStance = Stance(a,b)
        self.currentStance = Stance("Fire","Piercing")
        return self.currentStance
    
    def getTarget(self):
        if BotWars.VERBOSE:
            print "__",self.name,"__  target requested from: "
        if len(self.enemies)>0:
            for e in self.enemies:
                if BotWars.VERBOSE:
                    print "##",e
                if e.name == "BOB0" :
                    print "Found a bob0 at : ",e.position
                    return e
            return GameObject(100,100)
        #if len(self.enemies)>0:
            #return self.enemies[0]
        else:
            x = random.randint(0,360)
            y = random.randint(60,400)
            return GameObject(100,100)
    
    def adjustHealth(self,damage):
        self.health += damage.getDamage()
        if self.health <50:
            self.parent.HealMe()
        return self.health
    
    def getHealth(self):
        return self.health
    
    def getStance(self):
        return self.currentStance
    
    def setWoF(self,WoF):
        if BotWars.DEBUG:
            print "Thank you for letting bot know: WoF =:",WoF
    
    def reset(self,h):
        self.health = h
        self.enemies = []
        