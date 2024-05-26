import tag
import json
import timeline_engine as te
import propagation
import time
import logging
import logging.config
log = logging.getLogger('root')

def run_sim(config):

    logging.basicConfig(filename='simlog_exp_{0}.log'.format(config['expId']),
                        format='[exp_{0}][%(levelname)s]:%(message)s'.format(config['expId']),
                        level=logging.INFO)
                        
    result          = {}
    result['expId'] = config['expId']
    result['topo']  = config['topology_file']
    result['mode']  = config['mode']
    
    # get topology
    with open(config['topology_file'], 'r') as topo:
        topology = json.load(topo)
        config['num_tags'] = len(topology)
        
    topology = {int(outer_key): {int(inner_key): value for inner_key, value in inner_values.items()}
                        for outer_key, inner_values in topology.items()}
    
    log.info("[exp_{0}] run using {1}".format(config['expId'], config['topology_file']))

    # time enginee
    te_instance = te.timelineEngine(config['num_tags'])
    te_instance.start()

    # tags
    tag_list = []
    for i in range(config['num_tags']):
        t = tag.tag(i, config['interval'], te_instance, topology, config['mode'])
        tag_list.append(t)
        t.start()

    # propagation
    pg = propagation.propagation(te_instance, tag_list, topology)
    pg.start()

    # ---- running for a while until full network established
    
    joined_tag_list = []
    while len(joined_tag_list) != config['num_tags']:
        time.sleep(config['wake_delay'])
        joined_tag_list = []
        for t in tag_list:
            if t.get_rank()<t.MAX_RANK:
                joined_tag_list.append(t)
                
        log.info("[exp_{0}] {1} tags joined network".format(config['expId'], len(joined_tag_list)))
        
    result['time_to_sync'] = te_instance.next_event.timestamp
    
    print("exp {0} deactive root at {1} under {2} mode using topo {3}".format(config['expId'], result['time_to_sync'], config['mode'], config['topology_file']))
        
    # ---- wait until have received DIOs from other neighbors
    
    multi_neighbors_tag_list = []
    while len(multi_neighbors_tag_list) != config['num_tags']:
        time.sleep(config['wake_delay'])
        multi_neighbors_tag_list = []
        for t in tag_list:
            if len(t.neighbor_rank)>=2:
                multi_neighbors_tag_list.append(t)
            elif t.deviceId == 0:
                multi_neighbors_tag_list.append(t)
                
        log.info("[exp_{0}] {1} tags has more than 2 neighbors".format(config['expId'], len(multi_neighbors_tag_list)))
        
    result['network_established'] = te_instance.next_event.timestamp
    
    print("exp {0} network established at {1} under {2} mode using topo {3}".format(config['expId'], result['network_established'], config['mode'], config['topology_file']))
    
    # ---- deactivate the root node
    
    te_instance.pause_engine(True)
    
    tag_list[0].rank = t.MAX_RANK
    for neighbor in topology[0]:
        topology[0][neighbor] = 0
        tag_list[neighbor].updateparent(0, tag.tag.MAX_RANK, te_instance.next_event.timestamp)
        
    topology[0] = {}
    pg.topology_update(topology)
        
    te_instance.pause_engine(False)
    
    # ---- wait until all tag de-sync or 1 hour
    
    terminated_list = []
    while len(terminated_list) != config['num_tags'] and (te_instance.next_event == None or (te_instance.next_event != None and te_instance.next_event.timestamp<3600)):
        time.sleep(config['wake_delay'])
        terminated_list = []
        for t in tag_list:
            if t.get_rank() == t.MAX_RANK:                
                terminated_list.append(t)
                
        log.info("[exp_{0}] {1} tags reached to max rank".format(config['expId'], len(terminated_list)))

    # --- terminating threads

    # propagation
    pg.terminate()
    while pg.is_alive():
        pass
    log.info("[exp_{0}] propagation ends".format(config['expId']))

    # tags
    for t in tag_list:
        t.terminate()
    log.info("[exp_{0}] tags ends".format(config['expId']))

    te_instance.terminate()
    log.info("[exp_{0}] timeline ends".format(config['expId']))
    
    result['time_to_desync'] = te_instance.next_event.timestamp

    # ======================= get result from each tags =====================

    # ==== summary
    
    print("exp {1} ends at {0}s under {2} mode using topo {3}".format(result['time_to_desync'], config['expId'], config['mode'], config['topology_file']))

    return result

if __name__ == '__main__':

    config = {
        'expId': 0,
        'interval': 2,
        'topology_file': "topology/topology_100_100.json",
        'wake_delay':   0.01,
        'mode': 'rapdad'
    }
    
    run_sim(config)

        
                