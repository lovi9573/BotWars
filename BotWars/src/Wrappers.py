#TODO: Returned Gameobjects on a find objects do not know which direction they are from the viewer

from Avatar import Avatar
import math
import copy
import random


class GameObject(object):
    """A GameObject can represent anything that has a position on the playfield"""
        
    #@param int direction: The degree direction This GameObject was located at.
    # 
    def __init__(self,direction =0,distance=0,measuredFrom=[0,0],\
                 measuredFromName="",name="",type = "",health =0,position = [0,0]):
        self.measuredFrom = measuredFrom
        self.measuredFromName = measuredFromName
        self.name = name
        self.type = type
        self.health = health
        if position[0]!=0 or position[1]!=0 and direction ==0 and distance ==0:
            #set by coordiantes
            self.position = position
            self.distance, self.direction = self.calcPolarCoordinates()
        else:
            #set by dir and dist
            self.direction =direction
            self.distance = distance
            self.position = self.calcCoordinates()
        
        
    def __str__(self):
        return self.type +" "+self.name+" "+str(self.distance)+"@"+str(self.direction)+\
                " from "+self.measuredFromName
    
    
    # Return: Float distance from measuredFrom origin    
    def getDistance(self,pos):
        return math.sqrt((pos[0]-self.position[0])**2+(pos[1]-self.position[1])**2)
    
    def getCoordinates(self):
        return list(self.position)
    
    def getPolarCoordinates(self):
        return [self.distance,self.direction]
    
    # Return: tuple Coordinates of this object
    def calcCoordinates(self):
        rad =  math.radians(self.direction)
        x = int(self.measuredFrom[0]+ math.cos(rad)*self.distance)
        y = int(self.measuredFrom[1]- math.sin(rad)*self.distance)
        return [x,y]
    
    #Return: tuple containing (distance, angle) from the measuredFrom location
    def calcPolarCoordinates(self):
        dy = self.position[1]-self.measuredFrom[1]
        dx = self.position[0] -self.measuredFrom[0]
        dist = math.sqrt((dx)**2+(dy)**2)
        angle = int(math.atan2(dy, dx)*180/math.pi)
        return [dist,angle]
    
    def translate(self,offset):
        self.position[0] += offset[0]
        self.position[1] += offset[1]
        self.distance, self.direction = self.calcPolarCoordinates()

class Shot(object):
    """This class represents a shot taken by a bot on field"""
    
    def __init__(self,origin=[0,0],destination=[0,0],type=None,damage=0):
            self.origin = origin
            self.destination = destination
            self.type = type
            self.damage = damage


class Stance(object):
    """This class represents the stance of a bot on field"""
    
    def __init__(self,action = "",type = ""):
        self.action = action
        if (type == "Burning" or type == "Piercing"):
            self.type = type
        else:
            self.type = "Piercing"
        
    def __str__(self):
        return self.action + " : " + self.type
    
    #Return: Boolean (True/False)
    #returns true if arg matches either the action or type represented by this object    
    def isA(self,arg):
        if arg == self.action or arg == self.type:
            return True
        else:
            return False
    
    #Return: Boolean
    #returns true if the stance object given matches this on BOTH in action and type    
    def equals(self,stance):
        if self.action == stance.action and self.type == stance.type:
            return True
        else:
            return False

class Damage(Stance):
    """This class represents damage done"""
    
    def __init__(self,type = "",damage = 0,direction = 0,action = "Fire"):
        self.action = action
        self.type = type
        self.damage = damage
        self.direction = direction
    
    #Return: integer damage amount    
    def getDamage(self):
        return self.damage
    
    #Return: float direction the damage came from
    def getDirection(self):
        return self.direction
    
    #Return: String type of damage: "Burning"/"Piercing"
    def getType(self):
        return self.type

class View(object):
    """This class represents the area visible to a bot"""
    
    def __init__(self,pos=[0,0],theta = 0,WoF = 0,name = ""):
        self.__position = pos
        self.normalizeAngle(theta)
        self.__theta = self.normalizeAngle(theta)
        self.__WoF = WoF
        self.__name = name
    
    def getName(self):
        return self.__name
    
    def setName(self,n):
        self.__name = n
        
    def getPosition(self):
        return self.__position
    
    def setPosition(self,pos):
        self.__position = pos
        
    def getRadians(self):
        return float(self.__theta)*math.pi/180.0
    
    def setRadians(self,r):
        self.__theta = r*180.0/math.pi
    
    #Return: Float angle of viewing in degrees        
    def getTheta(self):
        return self.__theta
    
    #Return: none
    #set the angle of viewing to t
    def setTheta(self,t):
        self.__theta = t
    
    #Return: integer Width of Field.
    #returns the width of what can be seen in this view in degrees.    
    def getWoF(self):
        return self.__WoF
    
    #Return: none
    #set the Width of Field in degrees
    def setWoF(self,w):
        self._WoF = w
    
    #Return: float angle
    #will take a large or small angle and normalize it to be between 0 and 360    
    def normalizeAngle(self,t):
        while not(0<=t<360):
            if t <0:
                t += 360
            else:
                t -= 360
        return t
    
    #Return: Boolean
    #will return true if c is between a and b
    def isBetween(self,a,c,b):
        if a>b:
            if b<=c<=a:
                return True
            else:
                return False
        elif a<b:
            if a<=c<=b:
                return True
            else:
                return False
        else:
            if a==c==b:
                return True
            else:
                return False    
   
    #Return: Boolean
    #will return true if a and b have the same sign ie: both negative
    def hasSameSign(self,a,b):
        if a==0 or b==0:
            return True
        elif a>0:
            if b>0:
                return True
            else:
                return False
        elif a<0:
            if b<0:
                return True
            else:
                return False
        
    #Return: Boolean
    #will return True if the position tuple (x,y) is within this object's view
    def isInView(self,position):
        dx = position[0] - self.position[0]
        dy = self.position[1] - position[1]
        t = self.normalizeAngle(math.degrees(math.atan2(dy, dx)))
        mt = self.normalizeAngle(self.theta - self.woF)-0.1
        Mt = mt + 2*self.woF+0.2
        for a in (-360,0,360):
            if (self.isBetween(mt, t+a, Mt)):
                return True
        return False
        
        
    #Return: float angle in degrees
    #this will return the angle to (xp,yp) from this view's current position
    def getVisibleAngle(self,xp,yp):
        dy = self.__position[1]-yp
        dx = xp-self.__position[0]
        theta = math.degrees( math.atan2(dy, dx))
        theta = self.normalizeAngle(theta)
        mt = self.normalizeAngle(self.theta - self.woF)-0.1
        Mt = mt + 2*self.woF+0.2
        visible = False
        for a in (-360,0,360):
            if self.isBetween(mt ,theta+a,Mt):
                visible = True
        if visible == True:
            return theta
        else:
            raise ValueError("Angle Not Visible in this View")
        
    
    #@summary: Determines where an infinite view angle intersects a definite rectangle
    def getRectIntersection(self,a,b,theta=None):
        # a_________________
        # -                -
        # _________________b
        if not theta:
            theta = self.theta
        self.normalizeAngle(theta)
        testObjects = []
        
        if theta not in [0,90,180,270]:
            m = -math.tan(theta*math.pi/180.0)
            for y in [a[1],b[1]]:
                x = ((y-self.position[1])/m)+self.position[0]
                #print x,",",y
                testObjects.append(GameObject(position = [x,y],\
                                              name = "Wall",\
                                              type="Inert",\
                                              measuredFrom = self.__position,\
                                              measuredFromName = self.__name))
            for x in [a[0],b[0]]:
                y = m*(x-self.position[0])+self.position[1]
                testObjects.append(GameObject(position = [x,y],\
                                              name = "Wall",\
                                              type="Inert",\
                                              measuredFrom = self.__position,\
                                              measuredFromName = self.__name))
        elif theta in [0,180]:
            for x in [a[0],b[0]]:
                y = self.position[1]
                testObjects.append(GameObject(position = [x,y],\
                                              name = "Wall",\
                                              type="Inert",\
                                              measuredFrom = self.__position,\
                                              measuredFromName = self.__name))
        else:
            for y in [a[1],b[1]]:
                x = self.position[0]
                testObjects.append(GameObject(position = [x,y],\
                                              name = "Wall",\
                                              type="Inert",\
                                              measuredFrom = self.__position,\
                                              measuredFromName = self.__name))
        rectInt = None
        distance = 1000000
        
        for rectint in testObjects:
            #if v:
                #print rectint.position , "In view: ",self.isInView(rectint.position)
            d = rectint.getDistance(self.position)
            if ((self.isInView(rectint.position) and d< distance)or (rectint.position[0] == self.position[0] and rectint.position[1] == self.position[1] )):
                distance = d
                rectInt = rectint
        if rectInt == None:
            print "(",a,",",b,") ","position: ", self.position,theta
            for obj in testObjects:
                print obj.position , self.isInView(obj.position)
            assert 1==0
        return rectInt
            
        
    
    def getViewPoly(self,a,b):
        # a_________________
        # -                -
        # _________________b
        finalPoly =[]    
        cornerangles = []
        cornerangles.append(self.theta-self.__WoF)
        x1= a[0]
        x2= b[0]
        y1= a[1]
        y2= b[1]
        for x in (x1,x2):
            for y in (y1,y2):
                try:
                    t = self.getVisibleAngle(x, y)
                    cornerangles.append(t)
                except ValueError:
                    pass
            
        cornerangles.append(self.theta+self.__WoF)
        
        
        for theta in (cornerangles):
            n = self.getRectIntersection(a, b, theta)
            if n:
                finalPoly.append(n.position)
        
                    
        
        #list above coords with double listed self.position and return
        for pos in [self.position,self.position]:
            finalPoly.append(pos)
        return finalPoly
                
    
    position = property(getPosition,setPosition)
    theta = property(getTheta,setTheta)
    radians = property(getRadians,setRadians)
    woF = property(getWoF,setWoF)
    name = property(getName,setName)
  
class BotModifiers(object):
    
    def __init__(self,name):
        self.name = name
        self.modifiers ={"numHeals":2,
                         "maxDamage":10,
                         "minDamage":0,
                         "guardPercentageOff":0.75,
                         "guardPercentageOn":0.75}
        #self.numHeals = 2
        #if self.parent.VERSION ==2:
        #self.maxDamage = 20
        #self.minDamage = 0
        #self.guardDivider = 4
        #elif self.parent.VERSION ==3:
        #self.maxDamage = 10
        #self.minDamage = 0
        #self.guardPercentageOff = 0.75
        #self.guardPercentageOn = 0.75
            
            
    def getModifiers(self,isFormatted):
        if isFormatted:
            a = "Damage\n   Min: "+str(self.modifiers["minDamage"])+"\n   Max:"+str(self.modifiers["maxDamage"])+\
                   "\nDamage Reduction\n   Off Guard:"+str(100-self.modifiers["guardPercentageOff"]*100)[0:2]+"%\n   On Guard:"+str(100-self.modifiers["guardPercentageOn"]*100)[0:2]+\
                   "%\nHeals:"+str(self.modifiers["numHeals"])
            if self.modifiers["minDamage"] <10:
                return a
            else:
                return a
        else :
            return [self.modifiers["minDamage"],self.modifiers["maxDamage"],self.modifiers["guardPercentageOff"],self.modifiers["guardPercentageOn"]]
    
    def getModifier(self,name):
        return self.modifiers[name]
    
    def setModifier(self,name,value):
        if name in self.modifiers.keys():
            self.modifiers[name]=value
            
    def adjustModifier(self,*mod):
        name,operation,amount = mod
        if name in self.modifiers.keys():
            if operation == "+":
                self.modifiers[name] = self.modifiers[name] + amount
            elif operation == "-":
                self.modifiers[name] = self.modifiers[name] - amount
            elif operation == "*":
                self.modifiers[name] = self.modifiers[name] * amount
            elif operation == "/":
                self.modifiers[name] = self.modifiers[name] / amount
        if self.modifiers["maxDamage"] > 20:
            self.modifiers["maxDamage"] = 20
                
                     
    def createModifier(self,name,value):
        if name not in self.modifiers.keys():
            self.modifiers[name] = value
    
    def reset(self):
        self.modifiers["numHeals"] = 2
                
class BotStats(object):
    
    def __init__(self,name,botmodifier):
        #Game Stats variables
        self.name = name
        self.stats = {"points":[0,0],
                      "numHits":[0,0],
                      "roundsSurvived":[0,0],
                      "numFires":[0,0],
                      "numGuards":[0,0],
                      "numGuardsOnFire":[0,0],
                      "numGuardsCorrect":[0,0],
                      "damageDone":[0,0],
                      "kills":[0,0]}
        
        self.__merits = "" 
        self.modifiers = []      
        
        
        
    def reset(self):
        for stat in self.stats.values():
            stat[0] = 0
        self.__merits = ""
        
            
    def add(self,variable, amount):
        self.stats[variable][0] += amount
        self.calculateDerivedMeasures()
    
    def calculateDerivedMeasures(self):
        self.stats["roundsSurvived"][0] = self.stats["numFires"][0] + self.stats["numGuards"][0]      
    
    def endgame(self):
        #killed more than two of the players
        if self.stats["kills"][0] > 2: #len(self.parent.playersDict.keys())/2.0:
            self.__merits += "Finisher! "
            self.modifiers.append(("guardPercentageOn", "*",0.75))
        #done more than 250 damage
        if self.stats["damageDone"][0] < -200:  #(len(self.parent.playersDict.keys())/2.0)*100:
            self.__merits += "MarksMan! "
            self.modifiers.append(("guardPercentageOff", "*", 0.75))
        # guarded when being fired on more than 50% of the time
        if self.stats["numHits"][0] and float(self.stats["numGuardsOnFire"][0])/float(self.stats["numHits"][0]) > .5 :
            self.__merits += "Defender! "
            self.modifiers.append(("maxDamage", "+",2))
        # guarded against correct damage more than 75% of your hit guards
        if self.stats["numGuardsOnFire"][0] and float(self.stats["numGuardsCorrect"][0])/float(self.stats["numGuardsOnFire"][0]) > .65 :
            self.__merits += "Predicter! "
            self.modifiers.append(("minDamage", "+",1))
            #print self.parent.getName()+" : " , float(self.stats["numGuardsCorrect"][0])/float(self.stats["numGuardsOnFire"][0])
        #print self.bot.getName(),"GoF: ", self.numGuardsOnFire,"GC: ", self.numGuardsCorrect,"nH: ",self.numHits," : ",self.minDamage,self.maxDamage,self.guardPercentageOff, self.guardPercentageOn
        #print self.parent.getName()+" : " , float(self.stats["numGuardsOnFire"][0])/float(self.stats["numHits"][0])
        self.tallyTournamentStats()
        
    def getstat(self,variable,type="Round"):
        if type=="Tournament":
            i=1
        elif type == "Round":
            i=0

        if variable in self.stats.keys():
            return self.stats[variable][i] 

        elif variable == "All":
            if(self.stats["roundsSurvived"][i] == 0):
                self.stats["roundsSurvived"][i] = 1
            percentFiring = (self.stats["numFires"][i]*100)/self.stats["roundsSurvived"][i]
            return str(self.stats["damageDone"][i]) + "\t" + str(self.stats["kills"][i]) + "\t" + \
            str(self.stats["roundsSurvived"][i]) + "\t" + str(self.stats["numFires"][i]) + "\t" + str(self.stats["numGuards"][i]) + "\t" +\
            str(percentFiring)+ "%" + "\t" + str(self.stats["points"])+"\t"+self.__merits
        
    
        
    def tallyTournamentStats(self):
        for stat in self.stats.values():
            stat[1] += stat[0]
   
   
    def getNextModifier(self):
        if self.modifiers:
            return self.modifiers.pop(0)
        else:
            return ()

        
#BotWrapper...................................    

class BotWrapper(object):
    """Provides access to user bot methods and keeps meta-data for user bots"""
    
    def __init__(self,plyr,parent=None):
        #Bot __init__ is given starthealth, parent class
        self.bot = __import__(plyr).Bot(parent.STARTHEALTH,self)
        self.name = self.bot.getName()
        self.imagesDict = self.bot.getImages()
        self.parent = parent
        self.VERSION = self.parent.VERSION
        self.botmodifiers = BotModifiers(self.name)
        self.botstats = BotStats(self.name,self.botmodifiers)
        self.__position = [0,0]
        self.__ids = [0,0,0,0,0]
        self.resetStats()
        self.avatar = Avatar(self.name,self.__position,self.imagesDict)
        
    #def addEnemy(self,enemy):
    #    self.bot.addEnemy(enemy)
        
    def addPoints(self,n):
        self.botstats.add("points",n)
    
    #args: Damage object
    #Return: integer health
    def adjustHealth(self,damage):
        return self.bot.adjustHealth(damage)
    
    #args: string command
    #Return: none
    #executes user inputted commands
    def command(self,command):
        print "COMMAND: ",command," , made it to the botwrapper of: ",self.name
        self.bot.command(command)       
    #args integer round number
    #Return: none    
    def endRound(self,roundnumber):
        self.bot.endRound(roundnumber)
        if self.bot.getHealth() <= 0:
            self.__stance = "OUT!!"
    
    #args: none
    #return: none        
    def endGame(self):
        self.botstats.endgame()
        mod = self.botstats.getNextModifier()
        while mod:
            self.botmodifiers.adjustModifier(*mod)
            mod = self.botstats.getNextModifier()
            
    def getAvatar(self):
        self.avatar.stance = self.getStance()
        self.avatar.setPosition(self.__position)
        self.avatar.health = self.getHealth()
        self.avatar.enemies = self.getEnemies()
        self.avatar.modifiers = self.botmodifiers.getModifiers(True)
        try:
            self.avatar.color = self.bot.getColor()
        except AttributeError:
            self.avatar.color = (255,255,255)
        return copy.copy(self.avatar)
    
    #args: none
    #Return: list of enemies' names    
    def getEnemies(self):
        return self.bot.getEnemies()
    
    #args: none
    #Return: integer health    
    def getHealth(self):
        return self.bot.getHealth()
    
    
    def getIds(self):
        return self.__ids
    
    #args: none
    #Return: float angle to look    
    def getLookDirection(self):
        return self.bot.getLookDirection()
 
    
    def getModifier(self,name):
        return self.botmodifiers.getModifier(name)
    
    def getMoveDirection(self):
        return self.bot.getMoveDirection()
    
    #args: none
    #Return: string name
    def getName(self):
        return self.name
    
    def getPosition(self):
        return self.__position

    #args: none
    #Return: Stance object
    def getStance(self):
        if self.__stance:
            return self.__stance 
        else:
            return self.bot.getStance()
        
    def getStats(self):
        return copy.copy(self.botstats)
    
    #args: none
    #Return: GameOjbect object with position set
    def getTarget(self):
        t =  self.bot.getTarget()
        t.measuredFrom = self.position
        return t
    
    def HealMe(self):
        if self.botmodifiers.getModifier("numHeals") > 0:
            self.bot.adjustHealth(Damage("HEAL",25,0,"HEAL"))
            self.botmodifiers.adjustModifier("numHeals", "-",1)
            avatar = self.getAvatar()
            avatar.heal = True
            self.parent.drawHealIcon(avatar)
            
    
    #args: int round number
    #Return: Stance object    
    def prepare(self,n):
        st = self.bot.prepare(n)
        if st.isA("fire"):
            self.botstats.add("numFires",1)
        elif st.isA("guard"):
            self.botstats.add("numGuards",1)
        return st
    
    #def removeEnemy(self,e):
    #    self.bot.removeEnemy(e)
    
    #args: health to reset to
    #Return: none
    def reset(self,health):
        self.bot.reset(health)
        self.botstats.reset()
        self.botmodifiers.reset()
        self.resetStats()
        
    def resetStats(self):
        self.botstats.reset()
        self.__stance = ""
    
    def setDamage(self,n):
        self.__damageDone = n
        
    #def setEHealth(self,p,h,s):
    #    self.bot.setEHealth(p,h,s)
    
    
    def setIds(self,i):
        for index in range(0,len(i)):
            if i[index]:
                self.__ids[index]=i[index]
    
    #args: GameObject found
    #Return: none    
    def setLookResults(self,gameobject):
        self.bot.setLookResults(gameobject)       
             
    def setPosition(self,pos):
        #print "I, ",self.name," , just got moved to: ",pos
        self.__position[0] = pos[0]
        self.__position[1] = pos[1]
    
    #args: integer width of field
    #Return: none
    #used to tell your bot what its viewing width is    
    def setWoF(self,WoF):
        self.bot.setWoF(WoF)
        
    
        
    def test(self):
        try:
            #Testing checklist --> [enemy adding, stance, health, enemy, reset]
            testingCheck= 0
            testingList = ["a stance operation", "a health operation", "a targeting operation", "reset"]
                        
            for i in range(0,10):            
                assert  isinstance(self.bot.prepare(i), Stance)
                assert isinstance(self.bot.getStance(), Stance)
            testingCheck +=1
            
            assert self.bot.getHealth() == self.parent.STARTHEALTH
            assert self.bot.adjustHealth(Damage("Piercing", -5, 20))==self.parent.STARTHEALTH-5
            assert self.bot.adjustHealth(Damage("Burning", -15, 220))==self.parent.STARTHEALTH-20
            testingCheck +=1
            
            assert isinstance(self.bot.getTarget(), GameObject)
            testingCheck +=1
            
            self.bot.reset(self.parent.STARTHEALTH)
            assert self.bot.getHealth() == self.parent.STARTHEALTH
            return True
                
                    
        except AttributeError, attre:
            print self.bot.getName()," has been removed."
            print attre
            print "Error occured during: ",testingList[testingCheck]
            print "=================================================="
            return False
                
        except AssertionError, asse:
            print self.bot.getName()," has been removed."
            print "One of your functions does not return the correct value"
            print "Error occured during: ",testingList[testingCheck]
            return False
        
    #Properties______________________
    position = property(getPosition,setPosition) 
    ids = property(getIds,setIds)      
      

def test():
    go = GameObject(measuredFrom = [2000,0],position = [1000,1000])
    
    print go.getDistance([10,10]) #dist = 1400.07  polar (1414.21,45) 
    print go.getDistance([450,10]) #dist = 1132.51
    print go.getPolarCoordinates()
    print go.calcCoordinates()


if __name__ == "__main__":
    for i in range(0,10000):
        x = random.randint(0,1000)
        y = random.randint(0,650)
        pos = (x,y)
        t = random.randint(0,360)
        w = random.randint(1,45)
        v = View(pos, t, w)
        assert v.getPosition() == pos
        assert v.getTheta() == v.normalizeAngle(t)
        assert v.getWoF() == w
        r = math.radians(t)
        dr = math.radians(w)
        try:
            for ddr in (-dr,0,dr):
                xs = x + 100*math.cos(r+ddr)
                ys = y - 100*math.sin(r+ddr)
                assert v.isInView((xs,ys)) == True
        except AssertionError :
            print i
            print x,y," : ",xs,ys , "angle: ",t, "+- ",math.degrees(ddr)
            raise AssertionError
        
        a = random.randint(-1000,1000)
        b = random.randint(-1000,1000)
        c = random.randint(-1000,1000)
        try:
            if ((a < c and c < b) or (b<c and c<a)):
                assert v.isBetween(a, c, b) == True
            else:
                assert v.isBetween(a, c, b) == False
        except AssertionError:
            print a,c,b, v.isBetween(a, c, b)
        try:
            intersection = v.getRectIntersection((0,0), (1000,650)).getCoordinates()
            position = v.getPosition()
        
            assert intersection[0] <= 1000 and intersection[0] >= 0
            assert intersection[1] <= 650 and intersection[1] >= 0
            #assert not (intersection[0] == position[0] and intersection[1] == position[1])
        except AssertionError , a:
            print a
            print "\tint: ",intersection," Position: ", v.getPosition() ," angle: ", v.getTheta()
            v.getRectIntersection((0,0), (1000,650), True)
            print "_____________________________________________________________"
        except AttributeError , a:
            print a
            print "\tMissing View: ", v ,"x: ",x,"y: ",y,"t: ",t,"w: ",w
            v.getRectIntersection((0,0), (1000,650), True)
            print "_____________________________________________________________"
    print "The View class has passed its Tests with the above errors"
    for i in range(0,100):
        pos = (random.randint(0,1000), random.randint(0,650))
        angle = random.randint(0,360)
        rangle = math.radians(angle)
        distance = random.randint(0,1000)
        go = GameObject(angle, distance,pos)
        coords = go.calcCoordinates()
        actualcoords = (int(pos[0] + distance*math.cos(rangle)) ,int(pos[1] - distance*math.sin(rangle)) )
        try:
            assert coords[0]== actualcoords[0]
            assert coords[1]== actualcoords[1]
        except AssertionError:
            print i
            print "\tdistance: ", distance, " angle: ", angle, " from: ", pos
            print "\tcalculated: ",coords ," actual: ", actualcoords