#!/usr/bin/python

import os
import sys
import re

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import gio
import threading
import time

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas

from mpl_toolkits.mplot3d import  axes3d,Axes3D

import numpy as np

from numpy import pi

from serial import Serial
from StringIO import StringIO

gtk.gdk.threads_init()

def get_stokes(A, I):


    signal0=I
    
    signal1 = signal0*np.sin(2*A)
    signal2 = signal0*np.cos(4*A)
    signal3 = signal0*np.sin(4*A)
   
    denom = float(len(I))/360

    area0 = np.trapz(signal0)/denom
    area1 = np.trapz(signal1)/denom;
    area2 = np.trapz(signal2)/denom;
    area3 = np.trapz(signal3)/denom;

    A = area0/pi;
    B = -area1*2/pi;
    C = area2*2/pi;
    D = area3*2/pi;

    stokes0 = ((A-C))
    stokes1 = (2*C)
    stokes2 = (2*D)
    stokes3 = (B)
    
    stokes0p = np.sqrt(stokes1**2+stokes2**2+stokes3**2)
    
    s0 = stokes0p/stokes0p
    s1 = stokes1/stokes0p
    s2 = stokes2/stokes0p
    s3 = stokes3/stokes0p
    
    DOP = stokes0p/(stokes0)
    
    return stokes0p,s1,s2,s3,DOP 

class PlotUpdater(threading.Thread):
    """This class sets the fraction of the progressbar"""
    
    #Thread event, stops the thread if it is set.
    stopthread = threading.Event()
    
    def __init__(self, gui):
        threading.Thread.__init__(self) #Call constructor of parent
        self.gui = gui
        self.frac = 0
        self.ser = Serial("/dev/ttyACM0",115200)
        #self.ser.timeout = 1
        self.i = 0
    
    def run(self):
        """Run method, this is the code that runs while thread is alive."""
        
        #self.ser.readline()
        #self.ser.readline()
        
        #While the stopthread event isn't setted, the thread keeps going on
        while not self.stopthread.isSet() :
            # Acquiring the gtk global mutex
            #gtk.threads_enter()
            #Setting the fraction
            self.frac += 0.01
            self.i += 1
            #self.gui.line.set_data((t, np.sin(3*np.pi*(t+self.frac))))
            
            rslt = ''
            self.ser.write("d\n")
            s =  self.ser.readline().strip()
            while s != '' :
                rslt += s+'\n'
                s =  self.ser.readline().strip()
                #print repr(s)
            
            try:
                n = np.loadtxt(StringIO(rslt))
            
                angles = n[:,1]
                intensities = n[:,2]
                
                #(self.gui.s0p, self.gui.s1, self.gui.s2, self.gui.s3, self.gui.dop)=get_stokes(angles,intensities)
                
                self.gui.line.set_data((angles, intensities))

            except ValueError:
                print "Value Error"
                
            # Releasing the gtk global mutex
            #gtk.threads_leave()
            
            #Delaying 100ms until the next iteration
        
        self.ser.close()
            
    def stop(self):
        """Stop method, sets the event to terminate the thread's main loop"""
        self.stopthread.set()



class MultithreadedApp:
    def __init__(self):
        #Gui bootstrap: window and progressbar
        self.builder = gtk.Builder()
        self.builder.add_from_file("polarisation_analyser.glade")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")

        self.main_fig = Figure()
        self.main_axes = self.main_fig.add_axes((0.1,0.1,0.8,0.84))
        t = np.linspace(0,360,361)
        self.line, = self.main_axes.plot(t,0.5*np.sin(3*np.pi*t/360)+0.5)
        self.main_axes.set_ylim(0,1 )
        self.main_canvas = FigureCanvas(self.main_fig)
        self.builder.get_object("plot_container").add(self.main_canvas)
        
        self.sphere_fig = Figure()
        self.sphere_axes = Axes3D(self.sphere_fig)
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x = 1 * np.outer(np.cos(u), np.sin(v))
        y = 1 * np.outer(np.sin(u), np.sin(v))
        z = 1 * np.outer(np.ones(np.size(u)), np.cos(v))
        self.sphere_axes.plot_wireframe(x, y, z,  rstride=4, cstride=4, color='lightgreen',linewidth=1)
        self.sphere_canvas = FigureCanvas(self.sphere_fig)
        self.sphere_axes.mouse_init()
        self.builder.get_object("sphere_container").add(self.sphere_canvas)
        
        self.s1 = self.s2 = self.s3 = self.dop = self.s0p = 0

        #Creating and starting the thread
        self.pu = PlotUpdater(self)
        self.pu.start()
        
        gtk.idle_add(self.update_plot)

        self.window.show_all()
        gtk.main()
        
    def update_plot(self):
        #self.sphere_axes.plot3D([0,self.s1],[0,self.s2],[0,self.s3])       
        #self.main_axes.relim() #Update axis limits
        #self.main_axes.autoscale_view() #Updat
        self.main_canvas.draw() #Redraw main image
        #self.sphere_canvas.draw()
        return True

        
    def on_window_destroy(self, widget):
        self.pu.stop()
        gtk.main_quit()


MultithreadedApp()
