'''

This module implement a tag which beacons and listens right after in an interval fashion.

Assume channel ch_0, ch_1 and ch_2 are the three beacons channel used by tag,  
tag sends 3 beacons on each of the three channels.
At the end of each 3 beacons, tag turns to listen mode for a short duration to listen for command.

If nothing is heard during each of the three listenning duration, the tag continuous the beaconing 
until a command is heard.

'''

import time
import random
import threading
import timeline_engine as te

import logging
log = logging.getLogger('tag')
import logging.config

class tag(threading.Thread):
     
    MAX_DESYNC_TIMEOUT          = 30
    DEAD_TIME                   = 99999999
    TX_RX_TURNAROUND_TIME       = 0.001
    
    PARENT_UPDATE_PERIOD        = 60
    
    MAX_RANK                    = 65536
    DAGROOT_RANK                = 256
    NAME                        = "tag_{0}"
    
    MODE0                       = '6tisch'
    MODE0                       = 'rapdad'      # 
    MODE2                       = 'gw_battery'  # battery powered gateway, no need run
    MODE3                       = 'shmg'        # single hop multiple gateway, no need run
    
    SYNCNESS                    = 12
    
    def __init__(self, deviceId, interval, timeline_engine, topology, mode='6tisch'):
    
        # initialize the parent class
        threading.Thread.__init__(self)
        self.daemon = True
    
        self.deviceId           = deviceId
        self.name               = self.NAME.format(deviceId)
        self.timeline           = timeline_engine
        self.topology           = topology
        self.neighbor_rank      = {}
        self.mode               = mode 
        
        self.parent             = None
        self.gotParent          = False
        
        self.interval           = interval
        self.eb_interval        = 5*interval
        self.dio_interval       = 2*interval
        self.next_event_time    = 0
        self.lastParentUpdateTime = 0
        self.syncnessUpdateInterval   = 10.0 
        self.lastSyncnessUpdate = self.next_event_time
        
        self.lastSynced         = 0
                
        if self.deviceId == 0:
            self.isSynced       = True
            self.rank           = self.DAGROOT_RANK
            self.syncness       = self.SYNCNESS
        else:
            self.isSynced       = False
            self.rank           = self.MAX_RANK
            self.syncness       = 0
        
        self.next_event         = None
        self.isRunning          = True
        self.event_to_handle    = None
        
        self.rxEnded            = threading.Event()

        self.terminatedTime     = self.DEAD_TIME
            
        
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
        
    def sending_pkt(self, eventType, payload=[]):
        
        # ---- sending pkt
        self.next_event      = te.event(self.next_event_time, self.deviceId, eventType, payload)
        self.next_event.eventProcessed.clear()
        self.timeline.newEvent(self.next_event_time, self.next_event)
        
        if eventType == te.event.EVENT_T_EB:
        
            log.info('[tag_{0}] tx EB event generated at {1}!'.format(self.deviceId, self.next_event_time))
            
        elif eventType == te.event.EVENT_T_DIO:
        
            log.info('[tag_{0}] tx DIO event generated at {1}!'.format(self.deviceId, self.next_event_time))
        
        # wait until the event is processed
        self.next_event.eventProcessed.wait()
        if self.isRunning is False:
            # stop here
            return

    def run(self):
    
        while self.isRunning:
        
            if self.deviceId == 0 or (self.gotParent == True and self.isSynced):
            
                # ==== this is DAGROOT
            
                diff_time = 0
            
                # ---- schedule EB, DIO
                
                self.eb_event_time  = self.next_event_time + self.eb_interval  + random.random() 
                self.dio_event_time = self.next_event_time + self.dio_interval + random.random()   

                if self.eb_event_time>self.dio_event_time:
                    self.next_event_time = self.dio_event_time
                    self.sending_pkt(te.event.EVENT_T_DIO, [self.rank, self.syncness])
                    self.next_event_time = self.eb_event_time
                    self.sending_pkt(te.event.EVENT_T_EB, [self.syncness])
                else:
                    self.next_event_time = self.eb_event_time
                    self.sending_pkt(te.event.EVENT_T_EB, [self.syncness])
                    self.next_event_time = self.dio_event_time
                    self.sending_pkt(te.event.EVENT_T_DIO, [self.rank, self.syncness])
                    
                if self.deviceId != 0 and self.mode == 'rapdad':
                
                    timePassed = self.next_event_time - self.lastSyncnessUpdate
                    decrements = timePassed/self.syncnessUpdateInterval
                    if self.syncness <= decrements:
                        self.syncness = 0
                        self.isSynced = False
                        self.rank     = self.MAX_RANK
                        
                        log.info('[tag_{0}] syncness reach to zero at {1}!'.format(self.deviceId, self.next_event_time))
                        
                    else:
                        self.syncness           -= decrements
                        self.lastSyncnessUpdate += decrements*self.syncnessUpdateInterval
                        
                        log.info('[tag_{0}] syncness updates to {2} at {1}!'.format(self.deviceId, self.next_event_time, self.syncness))
                    
            else:
                
                # ---- insert idle event
                
                self.lastSynced      = self.next_event_time
                self.next_event      = te.event(self.next_event_time, self.deviceId, te.event.EVENT_IDLE)
                self.next_event.eventProcessed.clear()
                self.timeline.newEvent(self.next_event_time, self.next_event)
                
                log.info('[tag_{0}] listening for pkt at {1}!'.format(self.deviceId, self.next_event_time))
                
                # wait until the event is processed
                self.next_event.eventProcessed.wait()
                if self.isRunning is False:
                    # stop here
                    return
                    
                self.next_event_time += 10
                
            # update parent if not hear DIO from parent for PARENT_UPDATE_PERIOD seconds
            
            if self.next_event_time - self.lastParentUpdateTime > self.PARENT_UPDATE_PERIOD:
                
                if self.gotParent:
                    
                    self.updateparent(self.parent, self.MAX_RANK, self.next_event_time)
                    
    '''
    propagation rx event processing interface implementation
    '''
    def notify_rx_event(self, event):
    
        if event.deviceId == event.deviceId:
        
            self.rxPkt  = event.message
            src         = self.rxPkt[0]
            
            if self.isSynced == False:
                
                if event.eventType == te.event.EVENT_T_EB:
                
                    self.isSynced = True
                    self.lastSynced = event.timestamp
                    self.syncness = self.rxPkt[1]
                    
                    log.info('[tag_{0}] Synchronized to network at {1}!'.format(self.deviceId, event.timestamp))
                
            else:
            
                if event.timestamp - self.lastSynced > self.MAX_DESYNC_TIMEOUT:
                    
                    if self.deviceId != 0:
                        self.isSynced = False
                    
                        log.info('[tag_{0}] Desynchronized from network at {1}!'.format(self.deviceId, event.timestamp))
                    
                else:
                
                    if self.parent == src:
                    
                        self.lastSynced = event.timestamp
                        
                    if event.eventType == te.event.EVENT_T_DIO:
                    
                        log.info('[tag_{0}] DIO received from {2} at {1}!'.format(self.deviceId, event.timestamp, src))
                        
                        src, rank, syncness = self.rxPkt
                        
                        # donot process dio on dagroot
                        if self.deviceId == 0:
                            return
                        else:
                            self.syncness = syncness
                        
                        self.updateparent(src, rank, event.timestamp)
    
    def updateparent(self, src, rank, timestamp):
    
        if len(self.topology[src])>0:
            pdr = self.topology[src][self.deviceId]
    
        self.neighbor_rank[src] = rank + self.cost(pdr)
        self.neighbor_rank      = dict(sorted(self.neighbor_rank.items(), key=lambda item: item[1]))
        
        self.parent = list(self.neighbor_rank.keys())[0]
        self.rank   = list(self.neighbor_rank.values())[0]
        if self.rank >= self.MAX_RANK:
            self.rank       = self.MAX_RANK
            self.parent     = None
            self.gotParent  = False
            log.info('[tag_{0}] Rank updated to {2} at {1}, none Parent!'.format(self.deviceId, timestamp, self.rank))
        else:
            self.gotParent            = True
            self.lastParentUpdateTime = timestamp
            log.info('[tag_{0}] Rank updated to {2} with parent {3} at {1}!'.format(self.deviceId, timestamp, self.rank, self.parent))
        
    def cost(self, pdr):
    
        if pdr == 0:
        
            return self.MAX_RANK
    
        return ((3/pdr-2) * 256)
        
    def get_rank(self):
        
        return self.rank

# =========================== test ===========================================

if __name__ == '__main__':

    logging.config.fileConfig('logging.conf')
        
    num_tags    = 5
    t           = te.timelineEngine(num_tags)
        
    tag_list = []
    for i in range(num_tags):
        l = tag(i, t)
        tag_list.append(l)
        l.start()
        
    time.sleep(5)
    
    for i in tag_list:
        i.terminate()
    