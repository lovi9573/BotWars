

class IDs(object):
    
    def __init__(self,name,guard=None,fire=None):
        self.__ids = {}
        self.__name=name
        self.images = {"Guard":guard,"Fire":fire}
    
    def getId(self,name):
        return self.__ids[name]
    
    def setId(self,name,n):
        self.__ids[name]=n 
        
    def getName(self):
        return self.__name 
    
    def getNames(self):
        return self.__ids.keys()
    
    def getIds(self):
        return self.__ids.values()   
    
    def setImage(self,name,image):
        #TODO:image transparency testing
        if name in self.images.keys():
            h = image.height()
            w = image.width()
            if BotWars.DEBUG:
                print "Id image size:",[w,h]
            if True:# w == 140 and h == 140:
                self.images[name]= image
            
    def getImage(self,name):
        return self.images[name]
        
    

class Avatar(object):
    
    def __init__(self,name,pos =[0,0],imagesDict={"":""}):
        self.__position = pos
        self.name=name
        self.stance = None
        self.health = 0
        self.heal = False
        self.enemies = []
        self.modifiers = ""
        self.imagesDict = imagesDict
        self.color = (127,0,0)
        
         
    def getEnemies(self):
        return self.enemies
        
    def getPosition(self):
        return self.__position
    
    def setPosition(self,pos):
        self.__position[0] = pos[0]
        self.__position[1] = pos[1]
    
    def getHealth(self):
        return self.health 
        
    def getName(self):
        return self.name
        
        
    position = property(getPosition,setPosition) 
    