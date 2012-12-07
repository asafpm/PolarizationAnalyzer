# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 10:32:33 2012

@author: Tom
"""

## {{{ http://code.activestate.com/recipes/82965/ (r1)
"""
This recipe describes how to handle asynchronous I/O in an environment where
you are running Tkinter as the graphical user interface. Tkinter is safe
to use as long as all the graphics commands are handled in a single thread.
Since it is more efficient to make I/O channels to block and wait for something
to happen rather than poll at regular intervals, we want I/O to be handled
in separate threads. These can communicate in a threasafe way with the main,
GUI-oriented process through one or several queues. In this solution the GUI
still has to make a poll at a reasonable interval, to check if there is
something in the queue that needs processing. Other solutions are possible,
but they add a lot of complexity to the application.

Created by Jacob Hallén, AB Strakt, Sweden. 2001-10-17
"""
import Tkinter
from Tkinter import *
import time
import threading
import random
import Queue
import serial
import numpy as np
from numpy import *
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import  axes3d,Axes3D

# start serial port
serialport = "com3"
ser = serial.Serial(serialport, 9600)
ser.flushInput()

class GuiPart:
        
        
    def __init__(self, master, queue, endCommand,variables):
        self.queue = queue
        self.queueA = queue
        self.queueI = queue
        self.variables = variables
        
        # Set up the GUI
  
        #console = Button(master, text='Done', command=endCommand)
 
        app = master

        

        Extext = DoubleVar()
        Eytext = DoubleVar()
        Phasetext = DoubleVar()
        S0text = DoubleVar()
        S1text = DoubleVar()
        S2text = DoubleVar()
        S3text = DoubleVar()
        clicked = IntVar()
        
        self.mb=  Menubutton (master, text="Control", relief=RAISED )
        self.mb.grid()
        self.mb.menu  =  Menu ( self.mb, tearoff = 0 )
        self.mb["menu"]  =  self.mb.menu
            
        menuvar  = IntVar()

          
        self.mb.menu.add_checkbutton ( label="Exit",
                                  variable=menuvar, command=endCommand )
                                  
        
        self.lblVarIp = Tkinter.DoubleVar()
        self.lblVarM = Tkinter.DoubleVar()
        self.lblVarC = Tkinter.DoubleVar()
        self.lblVarS = Tkinter.DoubleVar()
        self.lblVarDOP = Tkinter.DoubleVar()
        #self.labelStokes0p.set(0)
        
        
        app.grid_columnconfigure(5,minsize=5)
        frame1 = Frame(app,bg='cyan',padx=10,pady=10)
        frame1.grid(column=0,row=1,columnspan=5)
        #console.grid(column=0,row=6,sticky='W',padx=10,pady=10)
        
        labelTitle = Label(frame1, text="Normalized Stokes parameters").grid(column=0,row=0,sticky='W',padx=10,pady=20,columnspan=2)
        labelIP = Label(frame1, text="IP").grid(column=0,row=1,sticky='W',padx=10,pady=10)
        labelM = Label(frame1, text="M").grid(column=0,row=2,sticky='W',padx=10,pady=10)
        labelC = Label(frame1, text="C").grid(column=0,row=3,sticky='W',padx=10,pady=10)
        labelS = Label(frame1, text="S").grid(column=0,row=4,sticky='W',padx=10,pady=10)
        labelDOP = Label(frame1, text="DOP").grid(column=0,row=5,sticky='W',padx=10,pady=10)
        
#        labelIP2 = Label(frame1,textvariable=self.lblVarIp).grid(column=1,row=1,sticky='W',padx=10,pady=10)
#        labelM2 = Label(frame1, textvariable=self.lblVarM).grid(column=1,row=2,sticky='W',padx=10,pady=10)
#        labelC2 = Label(frame1, textvariable=self.lblVarC).grid(column=1,row=3,sticky='W',padx=10,pady=10)
#        labelS2 = Label(frame1, textvariable=self.lblVarS).grid(column=1,row=4,sticky='W',padx=10,pady=10)
#        labelDOP2 = Label(frame1, textvariable=self.lblVarDOP).grid(column=1,row=5,sticky='W',padx=10,pady=10)
#        

#        
        
        Extext.set(2)
        Eytext.set(4)
        Phasetext.set(pi/3)
        clicked = 0
        
        f = Figure(figsize=(5,4), dpi=100)
        fSignal = Figure(figsize=(5,4), dpi=100)
        
        self.canvasStokes = FigureCanvasTkAgg(f, master=app)
        self.canvasStokes.show()
        self.canvasStokes.get_tk_widget().grid(column=11, row=5, columnspan = 10)
        self.axesStokes = Axes3D(f)
#        
        self.axesSignal = fSignal.add_subplot(111)
        self.canvasSignal = FigureCanvasTkAgg(fSignal, master=app)
        self.canvasSignal.show()
        self.canvasSignal.get_tk_widget().grid(column=0, row=5, columnspan = 10)
        # Add more GUI stuff here
    

    
    def processIncoming(self):
        """
        Handle all the messages currently in the queue (if any).
        """
        
        #self.labelvar.set(self.variables[0])

            #Afound = 0
#        Ifound = 0        
#        while self.queue.qsize():
#            #try:
#                val = self.queue.get(0)
#                # Check contents of message and do what it says
#                # As a test, we simply print it
#                                     
#                if val<0:
#                    A = -val
#                    Afound = 1
#                else:
#                    I = val
#                    Ifound = 1
#                if Afound+Ifound==2:
#                    Afound=0
#                    Ifound=0
#                    
#                    #ThreadedClient.plotThread(A,I)
#                    print A,I
#            #except Queue.Empty:
               #pass

class ThreadedClient:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI. We spawn a new thread for the worker.
        """
        self.master = master

        # Create the queue
        self.queue = Queue.Queue()
        self.queueA = Queue.Queue()
        self.queueI = Queue.Queue()
        #self.Amultloops = Queue.Queue()
        #self.Imultloops = Queue.Queue()
        self.queueindex = Queue.Queue()
        self.A = []
        self.I = []
        self.beginAverageing=False
        self.Amultloops = []
        self.Imultloops = []
        self.hasReset = False
        self.stokes0p=7
        self.s1=0
        self.s2 =0
        self.s3= 0
        self.DOP = 0
        self.variables = [self.stokes0p,self.s1,self.s2,self.s3,self.DOP]

        self.gui = GuiPart(master, self.queue, self.endApplication,self.variables)

       
        # Set up the thread to do asynchronous I/O
        # More can be made if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        #self.thread2 = threading.Thread(target=self.workerThread2)
        self.thread3 = threading.Thread(target=self.plotThread)
        self.thread4 = threading.Thread(target=self.AvgThread)
        self.thread1.start()
        #self.thread2.start()
        self.thread3.start()
        self.thread4.start()

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()
    
    

            
    def getStokes(self,I,A):
    
    
        signal0=I
        
        signal1 = signal0*sin(2*A)
        signal2 = signal0*cos(4*A)
        signal3 = signal0*sin(4*A)
       
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
        
        stokes0p = sqrt(square(stokes1)+square(stokes2)+square(stokes3))
        
        s0 = stokes0p/stokes0p
        s1 = stokes1/stokes0p
        s2 = stokes2/stokes0p
        s3 = stokes3/stokes0p
        
        DOP = stokes0p/(stokes0)
        
        return stokes0p,s1,s2,s3,DOP   
        
    def periodicCall(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        self.gui.processIncoming()
        
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            import sys
            sys.exit(1)
        self.master.after(100, self.periodicCall)

    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select()'.
        One important thing to remember is that the thread has to yield
        control.
        """

        Afound=0
        Ifound=0
        indexa = 0
        indexi = 0
        index=0
        i=0
        numresets=0
        while self.running:
            
            try:
            
                val = float(ser.readline())
                   
                self.queue.put(val)

                if val<0:
                    indexa+=1
                    AA = -val
                
                    Afound = 1
                else:
                    indexi+=1
                    II = val
        
                    
                    Ifound = 1
                if Afound+Ifound==2:
                    Afound=0
                    Ifound=0
                    
                    #self.A.append(AA)
                    #self.I.append(II)
                    self.queueA.put(AA)
                    self.queueI.put(II) 

                    #print AA, II
                    index+=1
                    if i==0:
                        Acompare = AA
                        i+=1
                        
                    elif AA<Acompare:
                        #print 'poo'
                        i=0
                        
                        self.I=[]
                        self.A=[]
                        
                        for x in range(0,index-1):
                            self.I.append( self.queueI.get(0))
                            self.A.append( self.queueA.get(0))
                            
                            self.Imultloops.append(self.I[-1])
                            self.Amultloops.append(self.A[-1])
                        print self.A[0], self.A[-1]
                        #if self.beginAverageing==False:
                            
                            
                            
                        
                        self.queueindex.put(index)
                        self.hasReset = True
                        numresets+=1
                        if numresets>10:
                            numresets=0
                            self.beginAverageing = True
                        
                        
                        index=1
                        #print 'poo'
                    Acompare=AA     
                        
    
                    
    
                
            except:
                print 'data read fail'
                pass
                    
    def AvgThread(self):
        
        Aavg = []
        
        index=0
        degrees = int
        while self.running:
            angles = []
            Iavg = []
            while self.beginAverageing:
                        
                I = np.array(self.Imultloops)
                A = np.array(self.Amultloops)
                
                #print A
                A = map(round,A)
                A = map(int,A)
                #print A
                degrees=0
                A = np.array(A)
                
                for i in range(0,360):
                    degrees+=1
                    #print degrees
                    indices = np.where(A==degrees)[0]
                    #print indices
                    #print len(indices)
                    if len(indices)>0:
                        
                        Iavg.append(np.mean(I[indices]))
                        angles.append(i+1)
                        index+=1
                self.gui.axesSignal.clear()   
                self.gui.axesSignal.plot(angles,Iavg)
                self.gui.canvasSignal.show()
                self.beginAverageing=False
                angles = map(float,angles)
                angles = np.array(angles)*2*pi/360
                (self.stokes0p,self.s1,self.s2,self.s3,self.DOP)=self.getStokes(Iavg,angles)
                print self.stokes0p,self.s1,self.s2,self.s3,self.DOP
                #self.gui.lblVarIp.set(self.stokes0p)
                #self.gui.lblVarM.set(self.s1)
                #self.gui.lblVarC.set(self.s2)
                #self.gui.lblVarS.set(self.s3)
                #self.gui.lblVarDOP.set(self.DOP)
    
    def plotThread(self):
        
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        
        x = 1 * np.outer(np.cos(u), np.sin(v))
        y = 1 * np.outer(np.sin(u), np.sin(v))
        z = 1 * np.outer(np.ones(np.size(u)), np.cos(v))

        self.gui.axesStokes.plot_wireframe(x, y, z,  rstride=4, cstride=4, color='lightgreen',linewidth=1)
        self.gui.canvasStokes.show()
        while self.running:
            time.sleep(1)
            #print self.stokes0p,self.s1,self.s2,self.s3,self.DOP
            
            
            
            self.gui.axesStokes.plot3D([0,self.s1],[0,self.s2],[0,self.s3])
            self.gui.canvasStokes.show()
            
    
    def rtplotThread(self):
        skip = -1
        skipcounter = 0
        Afound = 0
        Ifound = 0
        index=0
        
        
        while self.running:
            
           
            while self.queue.qsize():
                
                val = self.queue.get(0)
                skipcounter+=1
                # Check contents of message and do what it says
                # As a test, we simply print it
                if skipcounter>skip:
                    #print 'running'
                    skipcounter=0
                    #print 'notskipped'
                    #print index
                    if val<0:
                        A = -val
                        Afound = 1
                    else:
                        I = val
                        Ifound = 1
                    if Afound+Ifound==2:
                        #print 'found'
                        Afound=0
                        Ifound=0
                        if index==0:
                            Afirst=A
                            Ifirst=I
                            index+=1
                        if index==1:
                            if self.hasReset:
                                self.hasReset=False
                                
                                self.gui.axesSignal.clear()
                                self.gui.canvasSignal.show()
                                print 'cleared'
                            else:    
                                self.gui.axesSignal.plot([Afirst,A],[Ifirst,I])
                                self.gui.canvasSignal.show()
                            #print 'plotted'
                            Afirst=A
                            Ifirst=I
    
    
                        #print A,I

                
                
                
    
    def workerThread2(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select()'.
        One important thing to remember is that the thread has to yield
        control.
        """

        while self.running:
            # To simulate asynchronous I/O, we create a random number at
            # random intervals. Replace the following 2 lines with the real
            # thing.

            while self.queueindex.qsize():
                
                try:
                    index = self.queueindex.get(0)
                    I1=self.I
                    A=self.A
  
                    
                    #A = mapself.running = 0(float,A1)
                    I = map(float,I1)
                    
                    A = np.array(A)
                    A = A*2*pi/360
                    I = np.array(I)
                    #self.gui.axesSignal.clear()
                    #self.gui.canvasSignal.show()
                    #self.gui.axesSignal.plot(A,I)
                    #self.gui.canvasSignal.show()
                    (self.stokes0p,self.s1,self.s2,self.s3,self.DOP)=self.getStokes(I,A)
                    
                    #print self.stokes0p,self.s1,self.s2,self.s3,self.DOP
                    self.gui.lblVarIp.set(self.stokes0p)
                    self.gui.lblVarM.set(self.s1)
                    self.gui.lblVarC.set(self.s2)
                    self.gui.lblVarS.set(self.s3)
                    self.gui.lblVarDOP.set(self.DOP)
                    
                except:
                    print 'plot failed'
                        


            

    def endApplication(self):
        
        self.running = 0
        root.quit()     # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate


root = Tkinter.Tk()
root.title("Polarimeter")
root.geometry('800x600+100+100')

client = ThreadedClient(root)
root.mainloop()
## end of http://code.activestate.com/recipes/82965/ }}}
