'''
# This module implements a propagation model to disseminate message between radio devices.
'''

import label
import scanner
import timeline_engine as te
import threading

import logging
import logging.config
log = logging.getLogger('propagation')
    
class propagation(threading.Thread):

    NAME    = 'propagation'

    def __init__(self, timeline_engine, label_list, scanner_list):
        
        self.timeline           = timeline_engine
        self.label_list         = label_list
        
        self.radioLock          = False
        self.pkt_from_label     = None
        
        self.isRunning          = True
        
        # initialize the parent class
        threading.Thread.__init__(self)

    # ======================= private =========================================
    
    def terminate(self):
        
        self.timeline.QueueFullNotify.set()
        self.isRunning = False
        
    def run(self):
    
        
        while self.isRunning:
        
            # process only when queue is full
            self.timeline.QueueFullNotify.wait()
            if self.isRunning == False:
            
                log.debug('[{0}] Components terminated'.format(self.NAME))
                return
            
            latestEvent = self.timeline.getLatestEvent()
            
            log.info('[{0}] Components process event {2} from {1} at time {3}'.format(self.NAME, latestEvent.deviceId, latestEvent.eventType, latestEvent.timestamp))
            
            if latestEvent.eventType == te.event.EVENT_T_TX_S or latestEvent.eventType == te.event.EVENT_T_TX_E:
            
                log.info('Tx Event {1} from {0} notification to disseminate'.format(latestEvent.deviceId, latestEvent.eventType))
            
                # notify all labels
                for label in self.label_list:
                    label.notify_rx_event(latestEvent)
                
                # notify all scanners
                for scanner in self.scanner_list:
                    scanner.notify_rx_event(latestEvent)

            else:
                            
                # no need to inform radio devices for rx event
                pass
                
            # remove the event from queue and mark as done
            self.timeline.deleteEvent(latestEvent)
            self.timeline.eventProcessDone(latestEvent) 
            
# =========================== main ============================================

