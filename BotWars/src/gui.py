'''
Created on Dec 4, 2009

@author: 373jlovitt

@note:  pygame.image.load returns a surface that is the image
'''
import threading 
import sys
import pygame
import pickle
import random
import Queue
import math
from tcp2 import TCPClient
from Avatar import Avatar
from Wrappers import *
from pygame import QUIT,MOUSEBUTTONDOWN
from pygame.locals import *
pygame.init()


class ShotSprite(pygame.sprite.Sprite):
    
    def __init__(self, shot, *groups):
        pygame.sprite.Sprite.__init__(self, groups)
        self.pos = shot.origin
        self.desiredPos = shot.destination
        self.prefix = ""
        if shot.type == "Burning" :
            self.setImage(pygame.image.load("assets/BurningShot.gif"))
        elif shot.type == "Piercing" :
            self.prefix = "P"
            self.setImage(pygame.image.load("assets/PiercingShot.gif"))
        else:
            self.image = pygame.Surface((1,1))
            self.image.fill((255,255,255))
        self.explosioncount = 0
        self.speed = 30
        
    def setImage(self,image):
        image.convert()
        image.convert_alpha()
        x,y = self.pos
        xd , yd = self.desiredPos
        dx = xd-x
        dy = yd-y
        self.image = pygame.transform.rotate(image, -math.degrees(math.atan2(dy,dx)) - 90)
        
    def update(self):
        x,y = self.pos
        xd , yd = self.desiredPos
        dx = xd-x
        dy = yd-y
        d = math.sqrt(dx**2 + dy**2)
        if (d < self.speed ):
            if (self.explosioncount > 16):
                self.kill()
            else:
                x = xd
                y = yd
                self.image = pygame.image.load("assets/"+self.prefix+"explosion"+str(self.explosioncount)+".gif").convert_alpha()
                self.image.fill((0,0,0,64),None,BLEND_RGBA_SUB) 
                self.pos = [x,y]   
                self.rect = (x-61,y-90,x+81,y+110)
                self.explosioncount += 1
        else:
            x = x + dx*self.speed/d
            y = y + dy*self.speed/d           
            self.pos = [x,y]   
            self.rect = (x-10,y-10,20,20) 


class BotSprite(pygame.sprite.Sprite):
    
    def __init__(self,av, *groups):
        pygame.sprite.Sprite.__init__(self, groups)
        self.avatar = av
        self.desiredPos = []
        self.pos = av.getPosition()
        self.image = pygame.Surface((96,96)).convert_alpha()
        self.botsurface = pygame.Surface((96,96)).convert_alpha()
        self.healsurface = pygame.image.load("assets/Heal.png").convert_alpha()
        self.healalpha = 0
        self.update(av)
        
    def update (self, av = False):
        if av:
            self.botsurface.fill((150,150,150,0))
            self.avatar = av
            self.desiredPos = av.getPosition()
            #blit in the Heal cloud
            if self.avatar.heal == True :
                self.healalpha = 200
                
            self.botsurface.blit(pygame.image.load("assets/Bot.png"), (16,16))
            #Blit in the gun or shield
            file = "assets/"
            a=b=False
            if (av.stance.isA("Burning")):
                file += "Burning"
                a= True
            elif (av.stance.isA("Piercing")):
                file += "Piercing"
                a=True
            if(av.stance.isA("Fire")):
                file += "Fire"
                b=True
                inspos = (36,33)
            elif(av.stance.isA("Guard")):
                file += "Guard" 
                b=True  
                inspos = (24,18) 
            file += ".gif"
            if a and b:
                self.botsurface.blit(pygame.image.load(file),inspos)
             
            if self.avatar.health <1:
                self.botsurface.fill((100,100,100),(16,16,64,64),BLEND_SUB) 
            
            color = []
            for c in self.avatar.color:
                color.append(c)
            color.append(200)
            pygame.draw.rect(self.botsurface,(0,0,0,200),(2,0,22,15),2)
            pygame.draw.rect(self.botsurface,color, (3,1,20,13))
            h = self.avatar.health
            if h <0:
                h=0
            r = 512 - 5.12 *h
            g = 5.12*h
            if r >255:
                r = 255
            elif r <0:
                r= 0
            if g >255:
                g = 255
            elif g <0:
                g = 0
            color = (r,g,0,200)
            pygame.draw.rect(self.botsurface,(0,0,0,200),(26,4,69,8),2)
            if h>1:
                pygame.draw.rect(self.botsurface,color,(27,5,0.67*h,6))
            
        self.image.fill((0,0,0,0))    
        if  self.healalpha > 0:
            self.healsurface.fill((0,0,0,10), None, BLEND_RGBA_SUB)
            self.image.blit(self.healsurface, (0,0))
            self.healalpha -= 10
        
        self.image.blit(self.botsurface,(0,0))
        
        x,y = self.pos
        xd , yd = self.desiredPos
        x = x + math.ceil((xd-x)/10)
        y = y + math.ceil((yd - y)/10) 
        self.pos = [x,y]   
        self.rect = (x-32,y-32,96,96)
        
    def isWithin(self,pos):
        x = pos[0]
        y = pos[1]
        if (x > self.rect[0] and x < self.rect[0]+self.rect[2] and y > self.rect[1] and y < self.rect[1]+self.rect[3]):
            return True
        else:
            return False         


class ViewSprite(pygame.sprite.Sprite):
    
    def __init__(self,view,botgroup, *groups):
        pygame.sprite.Sprite.__init__(self, groups)
        self.botgroup = botgroup
        self.pimage = pygame.Surface((1000,650)).convert_alpha()
        self.pimage.fill((0,0,0,0))
        self.alpha = 80
        self.fadespeed = 4
        self.view = view
        self.rect = self.calcViewRect()
        self.image = self.pimage.subsurface(self.calcViewRect())
        self.update()
        
    def update (self):
        if self.alpha <0 :
            self.kill()
        else:
            colr = (255,255,255)
            for sprite in self.botgroup.sprites():
                if sprite.avatar.name == self.view.name:
                    colr = sprite.avatar.color
            color = []
            for c in colr:
                color.append(c)
            color.append(self.alpha)
            try:
                pygame.draw.polygon(self.pimage, color, self.view.getViewPoly((0,0),(1000,650)), 0)
            except ValueError :
                print "failing view poly: ",self.view.getViewPoly((0,0),(1000,650))," at: ",self.view.getPosition()," looking at: ", self.view.getTheta()
            self.alpha -=self.fadespeed
            
    def calcViewRect(self):
        coords = self.view.getViewPoly((0,0),(1000,650))
        pos = self.view.getPosition()
        mx = Mx = pos[0]
        my = My = pos[1]
        for coord in coords:
            if coord[0] < mx:
                mx = coord[0]
            if coord[0] > Mx:
                Mx = coord[0]
            if coord[1] < my:
                my = coord[1]
            if coord[1] > My:
                My = coord[1]
        dx = Mx-mx
        dy = My-my
        return (mx,my,dx,dy)
    
    
class HoverSprite(pygame.sprite.Sprite):
    
    def __init__(self,avatar,*groups):
        pygame.sprite.Sprite.__init__(self,groups)
        self.font = pygame.font.Font(None,32)
        self.image = pygame.Surface((245,190)).convert()
        self.image.fill(avatar.color)
        self.image.set_alpha(150)
        self.rect = self.image.get_rect()
        self.update(avatar)
        
    def update(self, av = False):
        if av:
            self.avatar = av
            txts = self.avatar.modifiers.split("\n")
            txts[:0]=["Name: "+av.getName()]
            y = 16
            for txt in txts:
                self.image.blit(self.font.render(txt , True, (0,0,0)),(16,y))
                y +=20
    
    def setpos(self,pos):
        if pos[0] + self.rect.width > 1000:
            self.rect.right = pos[0]
        else:
            self.rect.left = pos[0]
        if pos[1] + self.rect.height > 650:
            self.rect.bottom = pos[1]
        else:
            self.rect.top = pos[1]
        
        
        

class TxtButton(pygame.sprite.Sprite):
    
    def __init__(self,txt,pos,*groups):
        pygame.sprite.Sprite.__init__(self, groups)
        self.fontSize = 64
        self.txt= txt
        if self.txt == "":
            self.txt = "error"
        self.x = pos[0]
        self.y = pos[1]
        self.update(txt)
        
    def update(self ,newtxt = False):
        if newtxt:
            font = pygame.font.Font(None,self.fontSize)
            txt = font.render(newtxt , True, (200,0,0))
            self.rect = txt.get_rect(left = self.x,top = self.y)
            self.image = pygame.Surface((self.rect.w,self.rect.h))
            self.image.fill((0,64,64))
            self.image.blit(txt,(0,0))
        pygame.draw.rect(self.image,(0,0,0), self.image.get_rect(), 2)
        
    def isWithin(self,pos):
        x = pos[0]
        y = pos[1]
        if (x > self.rect[0] and x < self.rect[0]+self.rect[2] and y > self.rect[1] and y < self.rect[1]+self.rect[3]):
            return True
        else:
            return False 
    
    def setFontSize(self,x):
        self.fontSize = x
        self.update(self.txt)

class ImageButton(TxtButton):
    
    def update(self,image = False):
        if image:
            self.image = image
            self.rect = self.image.get_rect(left=self.x,top = self.y)
            

class TxtSprite(pygame.sprite.Sprite):
    
    def __init__(self,txt,pos,*groups):
        pygame.sprite.Sprite.__init__(self, groups)
        self.x = pos[0]
        self.y = pos[1]
        self.image = pygame.Surface((1,1))
        self.rect = self.image.get_rect()
        self.update(txt)
        
    def update(self ,newtxt = False):
        if newtxt:
            font = pygame.font.Font(None,32)
            self.image = font.render(newtxt , True, (200,150,0))
            self.rect = self.image.get_rect(left = self.x,top = self.y)
        
        
        


class Gui:

    def __init__(self):
        self.bgcolor = (110,110,110)
        self.notificationHeight = 0
        self.commandQueue = None
        
        self.botSprites = {}
        self.botGroup = pygame.sprite.RenderUpdates()
        self.shotSprites = []
        self.shotGroup = pygame.sprite.RenderUpdates() 
        self.viewSprites = {}
        self.viewGroup = pygame.sprite.RenderUpdates()
        self.hoverSprites = {}
        self.hoverGroup = pygame.sprite.RenderUpdates()
        self.activeHoverGroup = pygame.sprite.RenderUpdates()
        
        self.surfacesGroup = pygame.sprite.RenderUpdates()
        self.playSurface = pygame.image.load("assets/Playsurface.jpg")#
        self.cleanPlaySurface = pygame.image.load("assets/Playsurface.jpg")
        self.notificationSurface = pygame.Surface((1000,0))
        self.notificationsGroup = pygame.sprite.RenderUpdates()
        self.statsSurface = pygame.Surface((1000,650))
        self.drawStatsSurface = False
        self.commands = {"init": self.init,
                         "updateBot" : self.updateBot,
                         "drawShot" : self.drawShot,
                         "drawView" : self.drawView,
                         "displayStats" : self.displayStats}
    
    def init(self,avatars):
        ''' Used to initialize the bot Sprites to start a new game'''
        print "Gui got an init"
        self.drawStatsSurface = False
        self.playSurface = pygame.image.load("assets/Playsurface.jpg")
        self.botSprites = {}
        self.botGroup.empty()
        self.shotSprites = []
        self.shotGroup.empty() 
        #add bot sprites to the group
        for avatar in avatars:
            s = BotSprite(avatar,self.botGroup)
            self.botSprites[avatar.getName()] = s
            self.botGroup.add(s)
            h = HoverSprite(avatar,self.hoverGroup)
            self.hoverSprites[avatar.getName()] = h
            self.hoverGroup.add(h) 
        self.botGroup.draw(self.playSurface)
         
    def clear_Callback(self,surf,rect):
        surf.fill((0,127,127),rect)
        
    def updateBots(self):
        for bot in self.botSprites.values():
            bot.update()
        self.botGroup.clear(self.playSurface,self.cleanPlaySurface)
        #self.botGroup.draw(self.playSurface)
        
    def updateShots(self):
        self.shotGroup.update()
        self.shotGroup.clear(self.playSurface,self.cleanPlaySurface)
        #self.shotGroup.draw(self.playSurface)
 
    def updateViews(self):
        self.viewGroup.update()
        self.viewGroup.clear(self.playSurface,self.cleanPlaySurface)
        
    def updateHovers(self):
        self.activeHoverGroup.update()
        self.activeHoverGroup.clear(self.playSurface,self.cleanPlaySurface)
        
    def updateNotifications(self):
        self.notificationsGroup.update()
        self.notificationsGroup.clear(self.notificationSurface,self.clear_Callback)
                   
    def updateBot(self, botav):
        """look in bot list for bot with same name...and update."""
        av = botav[0]
        self.botSprites[av.getName()].update(av)
        self.hoverSprites[av.getName()].update(av)
        #@todo:  OPTIMIZE clear and draw only the bot that was updated
        self.botGroup.clear(self.playSurface,self.cleanPlaySurface)
        self.botGroup.draw(self.playSurface)
        
        
    def drawShot(self, shots):
        shot = shots[0]
        s = ShotSprite(shot,self.shotGroup)
        self.shotSprites.append(s)
        self.shotGroup.add(s)    
        
    def drawView(self, vw):
        view = vw[0]
        s = ViewSprite(view,self.botGroup,self.viewGroup)
        name = view.getName()
        if name in self.viewSprites.keys():
            self.viewGroup.remove(self.viewSprites[name])
        self.viewSprites[name]=s
        if s not in self.viewGroup.sprites():
            self.viewGroup.add(s)
            
    def displayStats(self,args):
        self.drawStatsSurface = True
        self.statsSurface.fill((0,200,200))
        self.statsSurface.set_alpha(200)
        font = pygame.font.Font(None,32)
        x = y = 10
        spacings = (120,60,65,85,75, 100,100,75,0)
        i=0
        #Draw Headings
        txts = ("Player" ,"Dmg" ,"Kills" ,"Rounds" ,"Fired" ,"Guarded" ,"% firing","Pts","Merits")
        
        for txt in txts:
            self.statsSurface.blit(font.render(txt , True, (0,0,0)),(x,y))
            x += spacings[i]
            i +=1
        y += 25
        x = 10
        i=0
        for arg in args:
            txts = arg.getstat("All").split("\t")
            txts.insert(0,arg.name)
            for txt in txts:
                self.statsSurface.blit(font.render(txt , True, (0,0,0)),(x,y))
                x += spacings[i]
                i+=1
            y += 25
            x = 10
            i=0
    
    def run(self):
        clock = pygame.time.Clock()
        #TODO: Fix Me !!!
        #self.commandQueue.put(pickle.dumps(("getInit",-1,(None,))))
        while (not pygame.event.peek([QUIT])):
            #print "fps: ",clock.get_fps()
            pygame.event.pump()
            self.activeHoverGroup.empty()
            mousehoverlist = pygame.event.get([MOUSEMOTION])
            if mousehoverlist:
                mousepost = mousehoverlist[-1].dict["pos"]
                mousepos = [mousepost[0],mousepost[1]-self.notificationHeight]
            for bot in self.botGroup.sprites():
                if bot.isWithin(mousepos):
                    name = bot.avatar.getName()
                    hover = self.hoverSprites[name]
                    hover.setpos(mousepos)
                    self.activeHoverGroup.add(hover)
            self.runSupplement()
            pygame.event.clear()
            clock.tick(20)
            ismore = True
            while ismore :
                try:
                    command, id, args = pickle.loads( self.commandQueue.get(False))
                except Queue.Empty:
                    command = False
                    ismore = False
                except EOFError:
                    command = False
                    ismore = False
                if (command in self.commands.keys()):
                    #print "=========== gui loop ============: " , command
                    try:
                        self.commands[command](args)
                    except:
                        pass
            self.updateBots()
            self.updateShots()
            self.updateViews()
            self.updateHovers()  
            self.updateNotifications()   
                
            self.botGroup.draw(self.playSurface)
            self.shotGroup.draw(self.playSurface)
            self.viewGroup.draw(self.playSurface)
            self.activeHoverGroup.draw(self.playSurface)
            self.notificationsGroup.draw(self.notificationSurface)  
             
            self.screen.blit(self.playSurface,(0,self.notificationHeight))
            if self.drawStatsSurface:
                self.screen.blit(self.statsSurface,(0,self.notificationHeight))
            self.screen.blit(self.notificationSurface,(0,0))
            pygame.display.flip()
            
    def runSupplement(self):
        pass
           


class ServerGui(Gui):
    '''
    Gui Connected to a GameEngine
    '''

    def __init__(self):
        '''
        Constructor
        '''
        Gui.__init__(self)
        #Setup screen
        self.notificationHeight = 50
        self.screen = pygame.display.set_mode((1000,650 + self.notificationHeight))
        self.screen.fill((255,0,0))        
        #Setup notification Surface
        self.notificationSurface = pygame.Surface((1000,self.notificationHeight))
        self.notificationSurface.fill((0,127,127))
        #setup Buttons
        self.runbutton = TxtButton("run",(10,0), self.notificationsGroup)
        self.notificationsGroup.add(self.runbutton)
        self.wof = 0
        self.wofubutton = ImageButton(pygame.image.load("assets/upButton.gif").convert(),(270,0),self.notificationsGroup)
        self.notificationsGroup.add(self.wofubutton)
        self.wofdbutton = ImageButton(pygame.image.load("assets/dnButton.gif").convert(),(270,25),self.notificationsGroup)
        self.notificationsGroup.add(self.wofdbutton)
        self.delay = 0
        self.delayubutton = ImageButton(pygame.image.load("assets/upButton.gif").convert(),(530,0),self.notificationsGroup)
        self.notificationsGroup.add(self.delayubutton)
        self.delaydbutton = ImageButton(pygame.image.load("assets/dnButton.gif").convert(),(530,25),self.notificationsGroup)
        self.notificationsGroup.add(self.delaydbutton)        
        #Setup Texts
        self.notificationSurface.blit(pygame.font.Font(None,32).render("View Angle:" , True, (200,150,0)),(100,15))
        self.woftxt = TxtSprite(str(self.wof),(230,15),self.notificationsGroup)
        self.notificationsGroup.add(self.woftxt)
        self.notificationSurface.blit(pygame.font.Font(None,32).render("Delay Time:" , True, (200,150,0)),(330,15))
        self.delaytxt = TxtSprite(str(self.delay),(460,15),self.notificationsGroup)
        self.notificationsGroup.add(self.delaytxt)        
        #Setup Communications library
        self.commands["updateWoF"] = self.updateWoF
        self.commands["updateSleepTime"] = self.updateSleepTime
        print ("ServerGui Constructor")
        
    def connectGame(self, game):
        self.commandQueue = game
        
    def runSupplement(self):
        
        mouseeventlist = pygame.event.get([MOUSEBUTTONDOWN])
        for event in mouseeventlist:
            if self.runbutton.isWithin(event.dict["pos"]):
                self.commandQueue.put(pickle.dumps(("run",-1,(None,))))
            elif self.wofubutton.isWithin(event.dict["pos"]):
                self.commandQueue.put(pickle.dumps(("setWoF",-1,(round(self.wof*1.1,1),))))
            elif self.wofdbutton.isWithin(event.dict["pos"]):
                self.commandQueue.put(pickle.dumps(("setWoF",-1,(round(self.wof*0.9,1),))))
            elif self.delayubutton.isWithin(event.dict["pos"]):
                self.commandQueue.put(pickle.dumps(("setSleepTime",-1,(round(self.delay*1.1,4),))))
            elif self.delaydbutton.isWithin(event.dict["pos"]):
                self.commandQueue.put(pickle.dumps(("setSleepTime",-1,(round(self.delay*0.9,4),))))
                         
    def updateWoF(self, args):
        self.wof = args[0]
        self.woftxt.update(str(self.wof))
        
    def updateSleepTime(self,args):
        self.delay = args[0]
        self.delaytxt.update(str(self.delay))
    
    
class ClientGui(Gui):
    
    def __init__(self):
        Gui.__init__(self)
        self.botConnectedTo = ""
        #Setup screen
        self.notificationHeight = 50
        self.screen = pygame.display.set_mode((1000,650 + self.notificationHeight))
        self.screen.fill((255,0,0)) 
        self.notificationSurface = pygame.Surface((1000,self.notificationHeight))
        self.notificationSurface.fill((0,127,127))
        #Setup Buttons
        self.botConnectButton = TxtButton("Connect to Bot",(10,0), self.notificationsGroup)
        self.notificationsGroup.add(self.botConnectButton) 
        self.botsDict = {}
        self.botConnectedToSprite = TxtSprite(self.botConnectedTo,(350,0),self.notificationsGroup)
        self.notificationsGroup.add(self.botConnectedToSprite)
        self.botCommandsDict = {}
        x = 850
        for letter in ("A","B","C"):
            self.botCommandsDict[letter] = TxtButton(letter,(x,0),self.notificationsGroup)
            self.notificationsGroup.add(self.botCommandsDict[letter])
            x += 50
        #setup Commands   
        self.commands["setAvailableBots"] = self.setAvailableBots    
            
    def connectGame(self,server):
        self.commandQueue = TCPClient(server)
  
    def runSupplement(self):       
        mouseeventlist = pygame.event.get([MOUSEBUTTONDOWN])
        for event in mouseeventlist:
            if self.botConnectButton.isWithin(event.dict["pos"]):
                self.commandQueue.put(pickle.dumps(("getAvailableBots",-1,(None,))))
            for bot in self.botsDict.keys():
                if self.botsDict[bot].isWithin(event.dict["pos"]):
                    self.botConnectedTo = bot
                    self.botConnectedToSprite.update(bot)
                    for sprite in self.botsDict.values():
                        self.notificationsGroup.remove(sprite)
            for letter in self.botCommandsDict.keys():
                if self.botCommandsDict[letter].isWithin(event.dict["pos"]):
                    self.commandQueue.put(pickle.dumps(("botCommand",-1,(self.botConnectedTo,letter))))
    
    def setAvailableBots(self,bots):
        x = 350
        for bot in bots:
            b = TxtButton(bot,(x,0),self.notificationsGroup)
            b.setFontSize(32)
            self.botsDict[bot]= b
            self.notificationsGroup.add(self.botsDict[bot])
            x +=75
  
if __name__ == "__main__":
    import Queue
    gui = ServerGui()
    q = Queue.Queue()
    
    #Create a list of avatars to pull from
    avs = []
    for b in range(0,21):
        a = "av" + str(b)
        av = Avatar(a,(random.randint(0,800),random.randint(0,600)))
        print "init queuing: ", av
        av.stance = Stance("Fire",random.choice(("Burning","Piercing")))
        avs.append(av)
    i = 0
    # Fill the queue with init requests
    for l in range(0,7):
        q.put( pickle.dumps( ["init",-1,[avs[i],avs[i+1],avs[i+2]]] ) )
        i = i +3
        
    #Fiill the queue with updateBot requests
    av = Avatar("av19", [200,200])
    av.stance = Stance("Fire",random.choice(("Burning","Piercing")))
    #av.heal = random.choice((True,False))
    q.put( pickle.dumps( ["updateBot", -1, [av]]))    
    p = [500,300]
    for l in range(0,10):
        p = [p[0]+random.randint(-8,8),p[1]+random.randint(-8,8)]
        a = Avatar("av20",p)
        if l ==1:
            a.heal = True
        else:
            a.heal = False
        print "updateBot queueing: " ,a
        a.stance = Stance("Fire",random.choice(("Burning","Piercing")))
        q.put( pickle.dumps( ["updateBot", -1, [a] ]   ) )
        
    #Fill the queue with drawView requests
    q.put(pickle.dumps(("drawView", -1, [View((200,200),225,20)])))
    for l in range(0,10):
        v = View((random.randint(0,1000),random.randint(0,650)), random.choice((45,135,225,315)), random.randint(1,45))
        q.put(pickle.dumps(("drawView", -1, [v])))
    #Fill the queue with drawShot requests
    for l in range(0,20):
        orig = []
        s = Shot(  (random.randint(0,800),random.randint(0,600)) , (random.randint(0,800),random.randint(0,600)), random.choice(("Burning", "Piercing")) )
        q.put( pickle.dumps( ["drawShot", -1, [s,None]]   ))
    s = Shot(  (600,600) , (200,200), "Burning" )
    q.put( pickle.dumps( ["drawShot", -1, [s,None]]   ))    
    gui.connectGame(q)
    gui.run()  
