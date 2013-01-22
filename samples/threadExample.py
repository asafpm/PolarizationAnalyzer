## {{{ http://code.activestate.com/recipes/409244/ (r1)
#!/usr/bin/python
import gtk
import gtk.glade
import sys   
import threading
import Queue
import time
import random


class aJob:
    """this is a container for jobs"""

    def __init__(self,id,label):
        """
          instance variables:
          id: a unique job id
          label: a label (url to fect, file to read, whatever)
          result: this will store the result (content of the file, whatever)
        """
        self.id=id
        self.label=label
        self.result=None
    

class GuiPart:
    """ this is the gui class, that is called in the main thread"""

    def __init__(self,qIn,qOut):
        """
        qIn in a Queue.Queue that store jobs to be done
        qOut is a Queue.Queue that store result of completed jobs
        The GuiPart is supposed to push stuff in qIn ,and regularly check
        if new result are available in qOut
        """
        self.qIn=qIn
        self.qOut=qOut
        self.jobCounter=0
        self.currentJobId=None
        self.xml=gtk.glade.XML("threadExample.glade")
        self.timeoutHandler=gtk.timeout_add(100,self.processOutcoming)
        
        dic={"on_quitButton_clicked":self.quitButton_clicked,
             "on_goButton_clicked":self.goButton_clicked,
             "on_entry1_activate":self.goButton_clicked,
             "on_window1_destroy_event":self.endApplication,
             "on_window1_delete_event":self.window1_delete
             }
        self.xml.signal_autoconnect(dic)


        self.treeview1=self.xml.get_widget('treeview1')
        #TreeStore column: job id, job label, status
        self.treestore1=gtk.TreeStore(int,str,str)
        self.treeview1.set_model(self.treestore1)
        
        cellLabel=gtk.CellRendererText()
        colLabel=gtk.TreeViewColumn('job')
        colLabel.pack_start(cellLabel,True)
        colLabel.add_attribute(cellLabel,'text',1)
        self.treeview1.append_column(colLabel)


        cellStatus=gtk.CellRendererText()
        colStatus=gtk.TreeViewColumn('status')
        colStatus.pack_start(cellStatus,True)
        colStatus.add_attribute(cellStatus,'text',2)
        self.treeview1.append_column(colStatus)

        self.progressbar1=self.xml.get_widget('progressbar1')
        
    def processOutcoming(self):
        """Handle all jobs currently in qOut, if any"""
        
        #        print "processOutcoming called"
        if self.currentJobId!=None:
            path=str(self.currentJobId)
            treeiter=self.treestore1.get_iter(path)
            self.treestore1.set_value(treeiter,2,'processing')

        
        if self.qIn.qsize() or self.currentJobId!=None:
            #self.progressbar1=self.xml.get_widget('progressbar1')
            self.progressbar1.show()
            self.progressbar1.pulse()
        else:
            self.progressbar1.hide()

        while self.qOut.qsize():
            try:
                job=self.qOut.get(0)
#                print "We have to deal with job",job.label
                self.processResult(job)
            except Queue.Empty:
                print "qOut is empty"
                pass

        return gtk.TRUE
   
    def processResult(self,job):
        """a new job has been processed, we have to display the result"""
        id=job.id
        path=str(id)
        treeiter=self.treestore1.get_iter(path)
        self.treestore1.set_value(treeiter,2,'done')


    def goButton_clicked(self,widget):
        label=self.xml.get_widget('entry1').get_text()
        self.xml.get_widget('entry1').set_text('')
        id=self.jobCounter
        self.jobCounter+=1
        job=aJob(id,label)
        self.treestore1.append(None,[id,label,'pending'])
        self.qIn.put(job)
    


    def quitButton_clicked(self,widget):
        self.endApplication()

    def window1_delete(self,widget,event):
        self.endApplication()



    def endApplication(self):
        print "time to die"
        gtk.timeout_remove(self.timeoutHandler)
        gtk.main_quit()
        
class ThreadedClient:
    """
    This class launch the GuiPart and the worker thread.
    """

    def __init__(self):
        """
        This start the gui in a asynchronous thread. We are in the "main" thread of the application, wich will later be used by the gui as well. We spawn a new thread for the worker.
        
        """
        gtk.threads_init()
        self.qIn=Queue.Queue()
        self.qOut=Queue.Queue()
        self.gui=GuiPart(self.qIn,self.qOut)
        self.running=True
        self.incomingThread=threading.Thread(target=self.processIncoming)
        #print "plop=",self.incomingThread
        self.incomingThread.setDaemon(True)
        self.incomingThread.start()
         #print "pika=",pika
        #gtk.threads_enter()
        gtk.main()
        self.running=False
        #gtk.threads_leave()



    def processIncoming(self):
       """
       This is where the blocking I/O job is being done.
       """
       while self.running:
           while self.qIn.qsize():
#               print "There are stuff in qIn"
               try:
                   job=self.qIn.get(0)
                   self.gui.currentJobId=job.id
#                   print "Let s process job",job.label
                   time.sleep(random.random()*6)
                   job.result='we would store the resutl here'
                   self.gui.currentJobId=None
                   self.qOut.put(job)
               except Queue.Empty:
                   pass
           time.sleep(2)   

    def endApplication(self):
        self.running=False

plop=ThreadedClient()

## end of http://code.activestate.com/recipes/409244/ }}}
