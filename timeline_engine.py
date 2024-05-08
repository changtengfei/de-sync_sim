'''
This module implement a timeline engine for simulation.

It mainly an event queue which stores events pushed by various instances.
Each event is timestampd when pushed into the queue.
Once the events from all instances are collected (queue is full), the immediate next event is marked.
The timeline engine only executes when queue is not full.
'''

import queue
import threading
import traceback

import logging
log = logging.getLogger('timelineEngine')

# =========================== typedef =========================================

class event(object):

    EVENT_T_EB           = 0
    EVENT_T_DIO          = 1
    EVENT_R_EB           = 3
    EVENT_R_DIO          = 4
    EVENT_N_DAGROOT_DOWN = 5
    
    EVENT_DEAD        = 99 # this is the last event before a radio terminate, will be in queue forever
    
    NAME                = 'event'
    
    def __init__(self, timestamp, deviceId, eventType, payload=[]):
        
        self.timestamp      = timestamp
        self.deviceId       = deviceId
        self.eventType      = eventType
        
        self.message        = [self.deviceId] + payload
        
        self.eventProcessed = threading.Event()
        
    def setEvent(self):
        
        self.eventProcessed.set()
        
    def setMessagePayload(self, payload):
        
        self.message = payload
        

class timelineEngine(threading.Thread):

    NAME                = 'timelineEngine'

    def __init__(self, queue_size):
    
        self.queue_size             = queue_size
        self.event_queue            = []
        
        self.waitForPush            = threading.Event()
        self.waitForTake            = threading.Event()
        
        self.waitForQueueBuffChange = threading.Event()
        self.waitForEventProcDone   = threading.Event()
        
        self.QueueFullNotify        = threading.Event()
        
        self.next_event     = None
        self.isRunning      = True
        
        # initialize the parent class
        threading.Thread.__init__(self)
        
    # ======================= public ==========================================
    
    def terminate(self):
        
        self.waitForQueueBuffChange.set()
        self.waitForEventProcDone.set()
        
        self.isRunning = False
        
    def newEvent(self, prio, event_to_push):
    
        log.info('[{0}] New Event Type {1} inserted at {2} by {3} !'.format(self.NAME, event_to_push.eventType, event_to_push.timestamp, event_to_push.deviceId))
    
        self.waitForPush.set()
        self.event_queue.append((prio, event_to_push))
        self.waitForPush.clear()
        
        # notify queue buffer changed
        self.waitForQueueBuffChange.set()
        
    def deleteEvent(self, event_to_delete):
    
        log.info('[{0}] Delete Event {1} at {2} (generated by {3}) !'.format(self.NAME, event_to_delete.eventType, event_to_delete.timestamp, event_to_delete.deviceId))
    
        self.waitForTake.set()
        self.event_queue.remove((event_to_delete.timestamp, event_to_delete))
        self.waitForTake.clear()
        
        # an event is removed from queue, clear queue full notify event
        self.QueueFullNotify.clear()
        
        # notify queue buffer changed
        self.waitForQueueBuffChange.set()
        
    def getLatestEvent(self):
    
        log.info('[{0}] Latest Event has been retrieved!'.format(self.NAME))
        
        self.waitForTake.set()
        self.event_queue.sort(key = lambda x: x[0])        
        self.next_event = self.event_queue[0][1]
        self.waitForTake.clear()
        
        # notify queue buffer changed
        self.waitForQueueBuffChange.set()
        
        return self.next_event
        
    def eventProcessDone(self, doneEvent):
        '''
        Call this function when event process is done.
        '''
        
        log.info('[{0}] Latest Event has been processed!'.format(self.NAME))
        
        self.waitForEventProcDone.set()
        doneEvent.setEvent()
        
    # ======================= private =========================================
        
    def run(self):
        
        while self.isRunning:
            
            while len(self.event_queue) < self.queue_size:
                self.waitForQueueBuffChange.wait()
                self.waitForQueueBuffChange.clear()
                # stop waiting is not running anymore
                if self.isRunning is False:
                    return
                
            log.info('[{0}] Queue is full!'.format(self.NAME))
            
            # notif queue full
            self.QueueFullNotify.set()
                
            # Queue is full, other thread needs to process at least one event in the queue to have timeline continue
            # set waitForEventProcDone when process is done.
            
            # wait for an event to be taken from queue
            self.waitForEventProcDone.wait()
            log.info('[{0}] event process done signal set!'.format(self.NAME))
            self.waitForEventProcDone.clear()
            if self.isRunning is False:
                return
        
        
# =========================== local ===========================================

if __name__ == '__main__':
    
    timeline_engine().start()
        
        
        