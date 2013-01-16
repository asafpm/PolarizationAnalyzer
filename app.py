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

import sys

global lock
lock = threading.Lock()


class Widget():
    def __init__(self, rect):
        self.left, self.top, self.width, self.height = rect
        
    def draw(self, surface):
        pass
        
class Oscilloscope(Widget):
    def __init__(self,rect,(x,y)):
        Widget.__init__(self,rect)
        self.x = x
        self.y = y
      
    def draw(self, surface):
        surface.fill((255,255,255))
        self.plot(surface, 0,np.pi, 0,1)
        
    def plot(self, surface, xmin, xmax, ymin, ymax):
        
        w, h = surface.get_size()
        lock.acquire()
        x = np.array(self.x)
        y = np.array(self.y)
        lock.release()
        si = np.argsort(x)
        x = x[si]
        y = y[si]
        

        xspan = abs(xmax-xmin)
        yspan = abs(ymax-ymin)
        xsc = 0.9*w/xspan
        ysc = 0.9*h/yspan
        xp = (x-xmin+0.05)*xsc
        yp = (y-ymin+0.05)*ysc
        for i in range(len(xp)-2):
            #pygame.draw.circle(surface, (0, 255, 0), (int(xp[i]),int(yp[i])), 1)
            pygame.draw.line(surface, (0, 0, 255), (int(xp[i]),int(yp[i])), (int(xp[i+1]),int(yp[i+1])), 1)
            
        #pygame.draw.line(surface, (180, 180, 180), (0,int(h*0.5)), (w-1,int(h*0.5)), 1)
        
class WireframeDecorator():
    def __init__(self, wireframe, **kwargs):
        self._wireframe = wireframe
        self.nodeColor = (0,0,255)
        self.edgeColor = (0,255,0)
        self.nodeRadius = 2
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
    def __init__(self,rect):
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
                for node in nodes:
                    if self.perspective:
                        if node[2] > -self.perspective:
                            z = self.perspective/ (self.perspective + node[2])
                            x = 0.5  + z*(node[0] - 0.5)
                            y = 0.5 + z*(node[1] - 0.5)
                            pygame.draw.circle(surface, wireframe.nodeColor, (int(x*w), int(y*h)), wireframe.nodeRadius, 0)
                    else:
                        pygame.draw.circle(surface, wireframe.nodeColor, (int(node[0]*w), int(node[1]*h)), wireframe.nodeRadius, 0)
                        
                        
class DataReader(threading.Thread):
    
    #Thread event, stops the thread if it is set.
    stopthread = threading.Event()
    
    def __init__(self, data,wireframe):
        threading.Thread.__init__(self) #Call constructor of parent
        self.wireframe = wireframe
        self.x = data[0]
        self.y = data[1]
        self.i = 0
        self.j = 0
        self.tht = 0
        self.ser = Serial("/dev/ttyACM0",115200)
        self.ths = []
        self.vals = []

    def stokes(self, th, i):
    
        th = np.array(th)
        i = np.array(i)
        signal0 = i
        
        signal1 = i*np.sin(2*th)
        signal2 = i*np.cos(4*th)
        signal3 = i*np.sin(4*th)
       

        a = np.trapz(signal0, th)*2/np.pi
        b = np.trapz(signal1, th)*4/np.pi
        c = np.trapz(signal2, th)*4/np.pi
        d = np.trapz(signal3, th)*4/np.pi
    
        s0 = a-c
        s1 = 2*c
        s2 = 2*d
        s3 = b
        
        phi = 0.5*np.arctan(s2/s1)
        xi = 0.5*np.arctan(s3/np.sqrt(s1**2+s2**2))
        
        return phi, xi
    
    def run(self):
        """Run method, this is the code that runs while thread is alive."""
        
        (x,y,z), r = (0.5,0.5, 0.5), 0.4
        while not self.stopthread.isSet():
            """
            th = 2*self.i*np.pi/200
            phi, xi = (np.pi*np.cos(self.j/300.)/20.,np.pi*np.sin(self.j/300.)/20.)
            #phi, xi = (0,-np.pi*0.25*self.j/1000.)
            S0,S1,S2,S3 = (1,np.cos(2*phi)*np.cos(2*xi),np.sin(2*phi)*np.cos(2*xi),np.sin(2*xi))
            A,B,C,D = (S0+0.5*S1, S3, S1*0.5, S2*0.5)
            I = 0.5*(A-B*np.sin(2*th)+C*np.cos(4*th)+D*np.sin(4*th))
            """
            th = 0
            I = 0
            s =  self.ser.readline().strip()

            try:
                n = np.loadtxt(StringIO(s))
                if n.shape[0] == 2:
                    th = n[0]
                    I = n[1]      
                    self.ths.append(th)          
                    self.vals.append(I)
            except ValueError:
                print "Value Error"
            except IndexError:
                print "Index Error"
                
            lock.acquire()
            self.x.append(np.mod(th, np.pi))
            self.y.append(I)
            
            if len(self.x) > 100:
                self.x.pop(0)
                self.y.pop(0)
                
            lock.release()

            
            if np.mod(th, np.pi) < np.mod(self.tht, np.pi):
                phi, xi = self.stokes(self.ths,self.vals)
                self.wireframe.addNodes([(x + r*np.sin(2*phi)*np.sin(np.pi*0.5-2*xi), y - r*np.cos(np.pi*0.5-2*xi), z - r*np.cos(2*phi)*np.sin(np.pi*0.5-2*xi) )])
                self.ths = []
                self.vals = []

            self.i += 1
            self.j += 1
            #time.sleep(0.001)
            self.wireframe.discardOldNodes(60)
            self.tht = th
            
            
    def stop(self):
        """Stop method, sets the event to terminate the thread's main loop"""
        self.stopthread.set()


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
        w = Window()
        data = ([1],[1])
        osc = Oscilloscope((0.1, 0.05, 0.8, 0.4),data)
        self.wfv = WireframeViewer((0.1,0.55,0.8,0.4))
        self.wfv.addWireframe('sphere', shape.Sphere((0.5,0.5, 0.5), 0.4, resolution=24), displayNodes=False)
        
        dwf = wf.Wireframe()
        self.wfv.addWireframe('sphere_points', dwf, displayEdges=False)
        self.dr = DataReader(data,dwf)
        
        w.add(osc)
        w.add(self.wfv)
        
        w.connect('mouse-motion', self.on_mouse_motion)
        w.connect('mouse-button-down', self.on_mouse_button_down)
        w.connect('quit', self.on_quit)
        
        self.dr.start()
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
