'''
Created on Nov 28, 2009

@author: 373jlovitt
'''
from Tkinter import *
from Dialogs import *
from GameEngine4 import GameEngine
from gui import *
import thread



VERBOSE = True
DEBUG = False

isServer = True
host = "Localhost"
isGraphical = True
botList = ()

# Callback passed to init Dailog box to set Server and host values
def initCallback(isS, hst):
    global isServer, host
    isServer = isS
    host = hst

# Callback passed to Server dialog box to set Graphical and botList values
def serverCallback(botlst, isG):
    global isGraphical, botList
    isGraphical = isG
    botList = botlst
    print botList
    
   
    
def standardInit():    
    # Create the root window manager  
    root = Tk()
    # Open Init dialog to determine ip and server/client status
    initdialog = InitDialog(root,initCallback)
    root.wait_window(initdialog)
    if(isServer):
        # Create the Gameengine and open Server dialog
        gameengine = GameEngine(host = host)
        serverdialog = ServerDialog(root,serverCallback)
        root.wait_window(serverdialog)
        gameengine.loadBots(botList)
        if(isGraphical ==  True):
            # TODO: Make a server gui
            root.destroy()
            BotWars.VERBOSE = False
            gui = ServerGui() 
            gui.connectGame(gameengine.connectGui())
            #thread.start_new_thread(gui.run,())
            gameengine.setSleepTime((0.03,))
            gameengine.setWoF((10,))
            #thread.start_new_thread(gameengine.run,(-1,(None,None)))
            thread.start_new_thread(gameengine.processCommands,())
            gui.run()
        else:
            root.destroy()
            test = False
            tst = raw_input("Is this a test Server? (Y/N): ")
            if (tst == "Y"):
                test = True
            if( not test ):
                t = float(raw_input("Choose a game speed (0-2): "))
            else:
                t = 0
            w = int(raw_input("Choose a robot view width of field: "))                  
            BotWars.VERBOSE = True
            gameengine.setWoF(w)
            gameengine.setSleepTime(t)
            if (test):
                while (1):
                    gameengine.run(None)
                    gameengine.reset(None)
            else:
                gameengine.run(None)
        
    else:
        #TODO: Create Client Gui with netclient queue
        root.destroy()
        gui = ClientGui()
        gui.connectGame("localhost")
        gui.run()
        print "Client"
        
def testingInit():
    # Create the Gameengine and open Server dialog
    gameengine = GameEngine(host = host)
    botList = ['Jesse_bot', 'Kimo_bot', 'Bob_bot']
    gameengine.loadBots(botList)
    BotWars.VERBOSE = False
    gui = ServerGui() 
    gui.connectGame(gameengine.connectGui())
    #thread.start_new_thread(gui.run,())
    gameengine.setSleepTime((0.03,))
    gameengine.setWoF((10,))
    #thread.start_new_thread(gameengine.run,(-1,(None,None)))
    thread.start_new_thread(gameengine.processCommands,())
    gui.run()
        
if __name__ == '__main__':
    x = raw_input("Run a Testing Setup Y/N (N is default)")
    if x == "Y":
        testingInit()
    else:
        standardInit()