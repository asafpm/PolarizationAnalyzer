#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#

import pygame
from pygame.locals import *
from numpy import *

import threading
from serial import Serial
from StringIO import StringIO

import sys

pygame.init()

class Plotter():
    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = self.screen.get_size()
        
    def plot(self, x, y):
        if len(x) == len(y) and len(x) > 0:
            x = array(x)
            y = array(y)
            #print x.shape
            span = abs(x[-1]-x[0])
            #print span
            xsc = self.w/span
            xp = (x-x[0])*xsc
            y = 70*y/2.0+240
            for i in range(len(xp)-1):
                pygame.draw.circle(self.screen, (255, 0, 0), (int(xp[i]),int(y[i])), 2)
                pygame.draw.line(self.screen, (0, 0, 255), (int(xp[i]),int(y[i])), (int(xp[i+1]),int(y[i+1])), 1)
                
            pygame.draw.line(self.screen, (100, 100, 100), (0,240), (self.w-1,240), 1)
                
        else:
            print "nothin' to plot"
            
class DataReader(threading.Thread):
    """This class sets the fraction of the progressbar"""
    
    #Thread event, stops the thread if it is set.
    stopthread = threading.Event()
    
    def __init__(self, gui):
        threading.Thread.__init__(self) #Call constructor of parent
        self.ser = Serial("/dev/ttyACM0",115200)
        self.data = (arange(100.0),arange(100.0))
        self.i = 0
    
    def run(self):
        """Run method, this is the code that runs while thread is alive."""
        
        #self.ser.readline()
        #self.ser.readline()
        
        #While the stopthread event isn't setted, the thread keeps going on
        nt = 0 
        
        while not self.stopthread.isSet() :

            s =  self.ser.readline().strip()
            
            try:
                n = loadtxt(StringIO(s))
                if n.shape[0] == 2:
                    #self.data[0][self.i] = n[0] #angle
                    if self.i < len(self.data[0]):
                        self.data[1][self.i] = n[1] #intensity
                        self.i += 1
                        nt = n[1]
                    else:
                        if nt*n[1] < 0 and n[1] < nt: #wait for trigger
                            self.data[1][0] = n[1]
                            self.i = 1
                            print "trigger %f %f"%(nt, n[1])
                        else:
                            nt = n[1]

            except ValueError:
                print "Value Error"
            except IndexError:
                print "Index Error"
                
        self.ser.close()
            
    def stop(self):
        """Stop method, sets the event to terminate the thread's main loop"""
        self.stopthread.set()

class PolarisationAnalyserGUI():
    
    def __init__(self, width=640, height=640, scale=10, fps=30):
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.scale = scale
        self.fps = fps
        #self.size = np.array([width, height])
        self.plotter = Plotter(self.screen)
        self.dr = DataReader(self)
        self.dr.start()


    def run(self):
        t = 0
        while 1:
            event = pygame.event.poll()
            if event.type == pygame.QUIT:
                pygame.quit()
                self.dr.stop()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pass
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    pass
                elif event.key == pygame.K_UP:
                    pass
                elif event.key == pygame.K_DOWN:
                    pass
                elif event.key == pygame.K_RIGHT:
                    pass
                elif event.key == pygame.K_LEFT:
                    pass
                    
                    
            self.screen.fill((255,255,255))
            
            x,y = self.dr.data
            self.plotter.plot(x,y)
            
            t += 0.1
            pygame.display.flip()
            #self.clock.tick(self.fps)
            



width = 640
height = 480
scale = 10

gui = PolarisationAnalyserGUI(width, height, scale)
gui.run()
