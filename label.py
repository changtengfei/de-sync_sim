'''

This module implement a label which beacons and listens right after in an interval fashion.

Assume channel ch_0, ch_1 and ch_2 are the three beacons channel used by label,  
label sends 3 beacons on each of the three channels.
At the end of each 3 beacons, label turns to listen mode for a short duration to listen for command.

If nothing is heard during each of the three listenning duration, the label continuous the beaconing 
until a command is heard.

'''

import time
import random
import threading
import timeline_engine as te
import radio as r
import lfsr_random as lr

import logging
log = logging.getLogger('label')
import logging.config

class label(r.radio, threading.Thread):
     
    DEAD_TIME                   = 99999999
    TX_RX_TURNAROUND_TIME       = 0.001
    
    NAME                        = 'label_{0}'
    
    def __init__(self, deviceId, interval, timeline_engine):
    
        self.deviceId           = deviceId
        self.name               = self.NAME.format(deviceId)
        self.timeline           = timeline_engine
        
        self.interval           = interval
        self.eb_interval        = 5*interval
        self.dio_interval       = 2*interval
        self.next_event_time    = 0
        
        self.isSynced           = False
        self.gotParent          = False
        
        self.next_event         = None
        self.isRunning          = True
        self.event_to_handle    = None
        
        self.rxEnded            = threading.Event()

        self.terminatedTime     = self.DEAD_TIME
            
        # initialize the parent class
        threading.Thread.__init__(self)
        
    def terminate(self):
        
        self.next_event.eventProcessed.set()
        self.isRunning = False
        
    def getTerminatedTime(self):
        
        terminated = False
        if self.terminatedTime != self.DEAD_TIME:
            terminated = True
            
        return terminated, self.terminatedTime

    def getNextEventTime(self):

        return self.next_event_time

    def getConfigurations(self):

        return self.num_beacon_to_send

    def run(self):
    
        while self.isRunning:
        
            if self.deviceId == 0 or self.gotParent == True:
            
                # schedule EB and DIO               
                self.eb_event_time  = self.next_event_time + self.eb_interval  + random.random() 
                self.dio_event_time = self.next_event_time + self.dio_interval + random.random()   

                if self.eb_event_time>self.dio_event_time:
                    self.next_event_time = self.eb_event_time
                else:
                    self.next_event_time = self.dio_event_time                   
                
                # ---- sending EB
                self.next_event      = te.event(self.eb_event_time, self.deviceId, te.event.EVENT_T_EB)
                self.next_event.eventProcessed.clear()
                self.timeline.newEvent(self.next_event_time, self.next_event)
                
                log.info('[{0}] tx EB event generated at {1}!'.format(self.deviceId, self.next_event_time))
                
                # wait until the event is processed
                self.next_event.eventProcessed.wait()                
                if self.isRunning is False:
                    # stop here
                    return
                                                    
                # ---- sending DIO
                self.next_event      = te.event(self.dio_event_time, self.deviceId, te.event.EVENT_T_DIO)
                self.next_event.eventProcessed.clear()
                self.timeline.newEvent(self.next_event_time, self.next_event)
                
                log.info('[{0}] tx DIO event generated at {1}!'.format(self.deviceId, self.next_event_time))
                
                # wait until the event is processed
                self.next_event.eventProcessed.wait()                
                if self.isRunning is False:
                    # stop here
                    return
                    
    '''
    propagation rx event processing interface implementation
    '''
    def notify_rx_event(self, event):
    
        self.event_to_handle = event
        if self.event_to_handle.deviceId == event.deviceId:
        
            self.rxPkt  = event.message            
            src, _      = self.rxPkt
            
            if self.parent == None or self.parent == src:
                # resync here

            # check the event type
            if event.eventType == te.event.EVENT_R_EB:
                pass

            elif event.eventType == te.event.EVENT_R_DIO:
            
                src, rank = self.rxPkt                
                self.updateparent(src, rank)

    def updateparent(self, src, rank):
    
        self.neighbor_rank[src] = rank
        self.neighbor_rank = dict(sorted(self.neighbor_rank.items(), key=lambda item: item[1]))
        
        self.parent = self.neighbor_rank.keys()[0]

# =========================== test ===========================================

if __name__ == '__main__':

    logging.config.fileConfig('logging.conf')
        
    num_labels = 5
    t = te.timelineEngine(num_labels)
        
    label_list = []
    for i in range(num_labels):
        l = label(i, t)
        label_list.append(l)
        l.start()
        
    time.sleep(5)
    
    for i in label_list:
        i.terminate()
    