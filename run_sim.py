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
    
    # topology
    with open(config['topology_file'], 'r') as topo:
        topology = json.load(topo)
        config['num_tags'] = len(topology)
        
    topology = {int(outer_key): {int(inner_key): value for inner_key, value in inner_values.items()}
                        for outer_key, inner_values in topology.items()}
        
    print('run exp using {0}'.format(config['topology_file']))

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
    print('propagation ends')

    # tags
    for t in tag_list:
        t.terminate()
    print('tags ends')

    te_instance.terminate()
    print('timeline ends')

    # ======================= get result from each tags =====================

    # ==== summary

    result = {
        'expId'                 : config['expId'],
        'time_to_desync'        : te_instance.next_event.timestamp,
    }
    
    print("exp ends at {0}s".format(result['time_to_desync']))

    return result

if __name__ == '__main__':

    config = {
        'expId': 0,
        'interval': 2,
        'topology_file': "topology/topology_100_50.json",
        'wake_delay':   0.01,
        'mode': 'rapdad'
    }
    
    run_sim(config)

        
                