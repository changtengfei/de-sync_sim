'''
# This script is for calculating the performance of beacon mode of MonoLets labels:
#   1. how fast to calculate X number of beacons
#   2. how much energy causing to receive beacons from all labels.
'''

import label
import scanner
import timeline_engine as te
import threading

import logging
import logging.config
log = logging.getLogger('app')
    
class app(threading.Thread):

    NAME    = 'app'

    def __init__(self, timeline_engine, labels, scanner, num_labels):
        
        self.timeline           = timeline_engine
        self.labels             = labels
        
        self.radioLock          = False
        self.pkt_from_label     = None
        self.total_num_labels   = num_labels
        
        self.label_count        = 0
        self.labels_list        = []
        
        self.isRunning          = True
        
        # initialize the parent class
        threading.Thread.__init__(self)

    # ======================= private =========================================
    
    def start_components(self):
        
        # start order is 
        #   1. timeline engine
        #   2. scanner
        #   3. labels
        
        log.debug('[{0}] Components is starting...'.format(self.NAME))
        
        self.timeline.start()
        for l in self.labels:
            l.start()
            
        log.debug('[{0}] Components started'.format(self.NAME))
    
    def terminate(self):
        
        for label in self.labels:
            label.terminate()
        self.timeline.terminate()
        
        log.debug('[{0}] Components terminated'.format(self.NAME))
        
        self.isRunning = False
        
    def run(self):
    
        # start all components
        self.start_components()
        
        while self.isRunning:
            
            while self.timeline.event_queue.full() is False:
                # stop waiting is not running anymore
                if self.isRunning is False:
                    return
                
            log.debug('[{0}] Queue is full!'.format(self.NAME))
                
            # Queue is full, other thread needs to process at least one event in the queue to have timeline continue
            # set waitForEventProcDone when process is done.

            event = self.timeline.getLatestEvent()[1]           
            log.debug('[{0}] Get the latest event {1}'.format(self.NAME, event.timestampe))                    
                        
            if self.label_count == self.total_num_labels:
                self.terminate()
            
            self.timeline.eventProcessDone()
            log.debug('[{0}] The latest event is processed'.format(self.NAME))
            
            event.setEvent()
            
# =========================== main ============================================

