#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#

import pygame
from pygame.locals import *
import numpy as np
import wireframe as wf
import basicShapes as shape

import threading
from serial import Serial
from StringIO import StringIO
import time
from struct import unpack

import sys


class Widget():
    def __init__(self, rect):
        self.left, self.top, self.width, self.height = rect
        
    def draw(self, surface):
        pass
        
class Oscilloscope(Widget):
    def __init__(self,rect, data_reader):
        Widget.__init__(self,rect)
        data_reader.add_point_listener(self.point_added)
        data_reader.add_turn_listener(self.turn_finished)
        
        self.datacx = np.zeros(data_reader.data_buff_size) #Current data
        self.datacy = np.zeros(data_reader.data_buff_size)
        
        self.datapx = self.datapy = None #Previous data
        self.i = 0
        
        
    def point_added(self,x,y,i):
        self.datacx[i] = x
        self.datacy[i] = y
        self.i = i
        
    def turn_finished(self,xs, ys):
        self.datapx = xs
        self.datapy = ys
      
    def draw(self, surface):
        surface.fill((255,255,255))
        xc = self.datacx[:self.i]
        yc = self.datacy[:self.i]
        self.draw_grid(surface)
        
        if self.datapx != None: #If there is any previous data to draw
            if len(xc>0):
                xmax = xc.max()
                q = np.nonzero(self.datapx > xmax) #Find where should we display previous data
                xp = self.datapx[q]
                yp = self.datapy[q]
            else:
                xp = np.array([])
                yp = np.array([])
                
            self.plot(surface,xp,yp, 0,2*np.pi, 0,1024) #Plot previous data
        self.plot(surface,xc,yc, 0,2*np.pi, 0,1024) #Plot current data
        
    def draw_grid(self, surface):
        w, h = surface.get_size()
        w, h = w-1, h-1
        #Draw grid
        for i in range(11):
            pygame.draw.line(surface, (210, 210, 210), (0,int(h*0.1*i)), (w-1,int(h*0.1*i)), 1)
            pygame.draw.line(surface, (210, 210, 210), (int(w*0.1*i),0), (int(w*0.1*i),h-1), 1)
       
        
        
    def plot(self, surface, x, y, xmin, xmax, ymin, ymax):
        w, h = surface.get_size()
        w, h = w-1, h-1
        
        #Scale data
        xspan = abs(xmax-xmin)
        yspan = abs(ymax-ymin)
        xsc = 1.0*(w+1)/xspan
        ysc = 1.0*h/yspan
        xp = (x-xmin)*xsc
        yp = h-(y-ymin)*ysc
            
        #Plot data
        try:
            for i in range(len(xp)-1):
                pygame.draw.line(surface, (0, 0, 255), (int(xp[i]), int(yp[i])), 
                                                        (int(xp[i+1]),int(yp[i+1])), 1)
        except IndexError:
            print "Error: ",i
    
class StokesCalculator():
    def __init__(self,data_reader, wireframe):
        data_reader.add_turn_listener(self.turn_finished)
        self.wireframe = wireframe
        self.s0 = [0]*5
        self.s1 = [0]*5
        self.s2 = [0]*5
        self.s3 = [0]*5
        
    def stokes(self,th, i):

        th = np.array(th)
        i = np.array(i)
        signal0 = i
        
        signal1 = i*np.sin(2*th)
        signal2 = i*np.cos(4*th)
        signal3 = i*np.sin(4*th)
       

        a = np.trapz(signal0, th)*1/np.pi
        b = np.trapz(signal1, th)*2/np.pi
        c = np.trapz(signal2, th)*2/np.pi
        d = np.trapz(signal3, th)*2/np.pi

        s0 = a-c
        s1 = 2*c
        s2 = 2*d
        s3 = b

        phi = 0.5*np.arctan2(s2,s1)
        xi = 0.5*np.arccos(s3/np.sqrt(s1**2+s2**2+s3**2))
        
        return s0, s1, s2, s3
        
    def turn_finished(self,xs, ys):

        size = len(ys)
        
        s0, s1, s2, s3 = self.stokes(np.linspace(0,2*np.pi,size),ys)
        # Calculate 5 point moving average
        """
        self.s0.pop()
        self.s1.pop()
        self.s2.pop()
        self.s3.pop()
        self.s0.insert(0,s0)
        self.s1.insert(0,s1)
        self.s2.insert(0,s2)
        self.s3.insert(0,s3)
        s0 = sum(self.s0)/len(self.s0)
        s1 = sum(self.s1)/len(self.s1)
        s2 = sum(self.s2)/len(self.s2)
        s3 = sum(self.s3)/len(self.s3)
        """
        (x,y,z), r = (0.5,0.5, 0.5), 0.4
        if s0 > 0: #If the intensity is greater than zero
            l = np.sqrt(s1**2+s2**2+s3**2)
            self.wireframe.addNodes([(x + r*s1/l, y + r*s3/l, z + r*s2/l )])
        self.wireframe.discardOldNodes(60)
        
class WireframeDecorator():
    def __init__(self, wireframe, **kwargs):
        self._wireframe = wireframe
        self.nodeColor = (0,0,255)
        self.edgeColor = (0,255,0)
        self.nodeRadius = 4
        self.displayNodes = True
        self.displayEdges = True
        
        if kwargs.has_key('displayNodes'):
            self.displayNodes = kwargs['displayNodes']
        elif kwargs.has_key('nodeColor'):
            self.nodeColor = kwargs['nodeColor']
        elif kwargs.has_key('edgeColor'):
            self.edgeColor = kwargs['edgeColor']
        
        
    def __getattr__(self, name):
        return getattr(self._wireframe, name)
    
        
class WireframeViewer(Widget,wf.WireframeGroup):
    def __init__(self,rect,data_reader):
        Widget.__init__(self,rect)
        self.wireframes = {}
        self.object_to_update = []
        
        self.displayNodes = False
        self.displayEdges = True
        
        self.perspective = False #0.5
        self.eyeX = 0.5
        self.eyeY = 0.5
        self.view_vector = np.array([0, 0, -1])
        
        
        self.background = (255,255,255)
        
        self.control = 0
        
    def addWireframe(self, name, wireframe,**kwargs):
        self.wireframes[name] = WireframeDecorator(wireframe,**kwargs)

        
    def rotate(self, axis, amount):
        (x, y, z) = self.findCentre()
        translation_matrix1 = wf.translationMatrix(-x, -y, -z)
        translation_matrix2 = wf.translationMatrix(x, y, z)
        
        if axis == 'x':
            rotation_matrix = wf.rotateXMatrix(amount)
        elif axis == 'y':
            rotation_matrix = wf.rotateYMatrix(amount)
        elif axis == 'z':
            rotation_matrix = wf.rotateZMatrix(amount)
            
        rotation_matrix = np.dot(np.dot(translation_matrix1, rotation_matrix), translation_matrix2)
        self.transform(rotation_matrix)
        
    def scale(self, scale):
        """ Scale wireframes in all directions from the centre of the group. """
        (x, y, z) = self.findCentre()
        scale_matrix = wf.scaleMatrix(scale, x, y, z)
        self.transform(scale_matrix)
        
    def draw(self, surface):
        surface.fill(self.background)
        w, h = surface.get_size()
        for name, wireframe in self.wireframes.items():
            nodes = wireframe.nodes
            
            if wireframe.displayEdges:
                for (n1, n2) in wireframe.edges:
                    if self.perspective:
                        if nodes[n1][2] > -self.perspective and nodes[n2][2] > -self.perspective:
                            z1 = self.perspective/ (self.perspective + nodes[n1][2])
                            x1 = 0.5  + z1*(nodes[n1][0] - 0.5)
                            y1 = 0.5 + z1*(nodes[n1][1] - 0.5)
                
                            z2 = self.perspective/ (self.perspective + nodes[n2][2])
                            x2 = 0.5  + z2*(nodes[n2][0] - 0.5)
                            y2 = 0.5 + z2*(nodes[n2][1] - 0.5)
                            
                            pygame.draw.aaline(surface, wireframe.edgeColor, (x1*w, y1*h), (x2*w, y2*h), 1)
                    else:
                        
                        pygame.draw.aaline(surface, wireframe.edgeColor, (nodes[n1][0]*w, nodes[n1][1]*h), (nodes[n2][0]*w, nodes[n2][1]*h), 1)
            if wireframe.displayNodes:
                n = 0
                for node in nodes:
                    
                    #Hack so that the last node is red
                    if n == nodes.shape[0]-1:
                        color = (255,0,0)
                    else:
                        color = (0,0,255)
                    n += 1

                    if self.perspective:
                        if node[2] > -self.perspective:
                            z = self.perspective/ (self.perspective + node[2])
                            x = 0.5  + z*(node[0] - 0.5)
                            y = 0.5 + z*(node[1] - 0.5)
                            pygame.draw.circle(surface, color, (int(x*w), int(y*h)), wireframe.nodeRadius, 0)
                    else:
                        pygame.draw.circle(surface, color, (int(node[0]*w), int(node[1]*h)), wireframe.nodeRadius, 0)
                        
                        
class DataReader(threading.Thread):
        
    #Thread event, stops the thread if it is set.
    stopthread = threading.Event()
    
    def __init__(self):
        threading.Thread.__init__(self)                     #Call constructor of parent
        self.ser = Serial("/dev/ttyACM0",115200)            #Initialize serial port
        self.data_buff_size = 1024                          #Buffer size
        
        #Data buffers for current values
        self.datax = np.zeros(self.data_buff_size)          
        self.datay = np.zeros(self.data_buff_size)
        
        #Data buffers for previous turn
        self.datax2 = np.zeros(self.data_buff_size)         
        self.datay2 = np.zeros(self.data_buff_size)
        
        #Lists to store the callbacks
        self.point_listeners = []
        self.turn_listeners = []
        
        self.x = 0 #Most recent x
        self.y = 0 #Most recent y
        self.oldx = 0 # oldx is used to keep track of when a new turn starts
        self.i = 0 #Current index
        self.size = 1 #Size of previous turn
        self.start()
        
    def stop(self):
        #Stop method, sets the event to terminate the thread's main loop
        self.stopthread.set()
        
    #Add a function to be called each time a new data point is read.
    #listener should have x,y,i as arguments where x,y is the new point read and i is the point index.
    def add_point_listener(self,listener):
        self.point_listeners.append(listener)
        
    #Add a function to be called each time a new turn is finished.
    #listener should have xs, ys as arguments where xs,ys are lists of numbers
    def add_turn_listener(self,listener):
        self.turn_listeners.append(listener)
        
    
    #Run method, this is the code that runs while thread is alive.
    def run(self):      

        num_bytes = 16 #Number of bytes to read at once
        val = 0 #Read value
        
        while not self.stopthread.isSet() :
            rslt = self.ser.read(num_bytes)             #Read serial data
            byte_array = unpack('%dB'%num_bytes,rslt)   #Convert serial data to array of numbers

            j = 1
            first = False #Flag to indicate weather we have the first byte of the number
            for byte in byte_array:
                if 224 <= byte <= 255: #If first byte of number
                    val = (byte & 0b11111) << 5
                    first = True
                elif 96 <= byte <= 127: #If other byte of number
                    if first:
                        if j == 1:
                            val |= (byte & 0b11111)
                            self.x = val
                        elif j == 2:
                            val = (byte & 0b11111) << 5
                        else:
                            val |= (byte & 0b11111)
                            self.y = val
                            self.nums_read()
                            j = 0
                        j += 1


                    
        self.ser.close()
        
    def nums_read(self):
        # If a turn of the waveplate is complete
        if self.oldx > self.x:
            self.size = self.i
            #print self.size
            self.i = 0
            self.datax2 = self.datax[:self.size].copy() #angle
            self.datay2 = self.datay[:self.size].copy() #intensity
            for turn_listener in self.turn_listeners:
                #Turn finished so call all of the turn listeners
                turn_listener(self.datax2,self.datay2)
        if self.i < self.data_buff_size:
            self.datax[self.i] = self.x/1024.0*2*np.pi
            self.datay[self.i] = self.y
            
            for point_listener in self.point_listeners:
                #New point measured so call all of the point listensers
                point_listener(self.x/1024.0*2*np.pi,self.y,self.i)
            self.oldx = self.x
        else:
            print "ERROR: buffer overrun ",self.x,self.y,self.i
        
        self.i += 1                       


class Window():
    
    def __init__(self, width=640, height=480, fps=15):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height),HWSURFACE|DOUBLEBUF|RESIZABLE)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.widgets = []
        self.surfaces = {}
        self.callbacks = {
            "mouse-motion":[],
            "mouse-button-down":[],
            "quit":[]
        }

    def add(self, widget):
        self.widgets.append(widget)
        w = int(self.screen.get_width()*widget.width)
        h = int(self.screen.get_height()*widget.height)
        self.surfaces[widget] = pygame.Surface((w,h),HWSURFACE|DOUBLEBUF)
        
    def connect(self, signal_name, callback):
        self.callbacks[signal_name].append(callback)
        
    def emmit(self, signal_name, *args):
        for callback in self.callbacks[signal_name]:
            callback(*args)

    def run(self):
        while 1:
            event_list = pygame.event.get(MOUSEMOTION)
            if len(event_list) > 0:
                event = event_list[-1] #Using only the last event makes it more responsive
                if event.type == MOUSEMOTION:
                    self.emmit('mouse-motion',event)
            event = pygame.event.poll()
            if event.type == QUIT:
                self.emmit('quit')
                pygame.quit()
                sys.exit()
            elif event.type == VIDEORESIZE:
                screen=pygame.display.set_mode(event.size,HWSURFACE|DOUBLEBUF|RESIZABLE)
                for widget in self.widgets:
                    w = int(event.w*widget.width)
                    h = int(event.h*widget.height)
                    self.surfaces[widget] = pygame.Surface((w,h),HWSURFACE|DOUBLEBUF)
            elif event.type == MOUSEBUTTONDOWN:
                self.emmit('mouse-button-down', event)

                    
            self.screen.fill((255,255,255))
            
            for widget in self.widgets:
                widget.draw(self.surfaces[widget])
                l = int(widget.left*self.screen.get_width())
                t = int(widget.top*self.screen.get_height())
                self.screen.blit(self.surfaces[widget],(l,t))
                
            pygame.display.flip()
            self.clock.tick(self.fps)
            

class PolarisationAnalyser():
    def __init__(self):
        w = Window(800,400)
        
        self.dr = DataReader()
        self.wfv = WireframeViewer((0.4,0.1,0.5,0.8),self.dr)
        self.wfv.addWireframe('sphere', shape.Sphere((0.5,0.5, 0.5), 0.4, resolution=24), displayNodes=False)
        
        dwf = wf.Wireframe()
        self.wfv.addWireframe('sphere_points', dwf, displayEdges=True)
        
        StokesCalculator(self.dr,dwf)
        
        """
        owf = wf.Wireframe()
        self.wfv.addWireframe('target', owf, nodeColor=(200,0,200))
        
        
        #TODO: add target node (need Stokes parameters of target node)
        s1 = 0.93
        s2 = -0.36
        s3 = 0
        (x,y,z), r = (0.5,0.5, 0.5), 0.4
        l = np.sqrt(s1**2+s2**2+s3**2)
        owf.addNodes([(x + r*s1/l, y + r*s3/l, z + r*s2/l )])
        """
        
        
        osc = Oscilloscope((0.05, 0.1, 0.3, 0.8), self.dr)
        
        w.add(osc)
        w.add(self.wfv)
        
        w.connect('mouse-motion', self.on_mouse_motion)
        w.connect('mouse-button-down', self.on_mouse_button_down)
        w.connect('quit', self.on_quit)
        
        w.run()
        
    def on_mouse_motion(self,event):
        if event.buttons[0]:
            self.wfv.rotate('y',event.rel[0]*np.pi/86)
            self.wfv.rotate('x',-event.rel[1]*np.pi/86)
            
    def on_mouse_button_down(self,event):
        if event.button == 4:
            self.wfv.scale(1.25)
        elif event.button == 5:
            self.wfv.scale(0.8)
            
    def on_quit(self):
        self.dr.stop()

PolarisationAnalyser()
