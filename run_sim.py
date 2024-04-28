import label
import scanner
import timeline_engine as te
import propagation
import time
import logging

def run_sim(config):

    logging.basicConfig(filename='simlog_exp_{0}.log'.format(config['expId']),
                        format='[exp_{0}][%(levelname)s]:%(message)s'.format(config['expId']),
                        level=logging.INFO)

    print('run exp with {0} labels and {1} scanners'.format(config['num_label'], config['num_scanner']))

    # time enginee
    te_instance = te.timelineEngine(config['num_label'] + config['num_scanner'])
    te_instance.start()

    # labels
    label_list = []
    for i in range(config['num_label']):
        l = label.label(i, config['beacon_interval'], config['num_beacon_to_send'], config['rx_timeout'], te_instance)
        label_list.append(l)
        l.start()

    # scanners
    scanner_list = []
    for i in range(config['num_scanner']):
        s = scanner.scanner(i, te_instance)
        scanner_list.append(s)
        s.start()

    # propagation
    pg = propagation.propagation(te_instance, label_list, scanner_list)
    pg.start()

    # ---- running for a while
    terminated_list = []
    while len(terminated_list) != config['num_label']:
        time.sleep(1)
        terminated_list = []
        for l in label_list:
            terminated, t = l.getTerminatedTime()
            if terminated is True or l.getNextEventTime()>5:
                terminated_list.append(l)
        print("[exp_{0}] {1} labels detected".format(config['expId'], len(terminated_list)))

    # --- terminating threads

    # propagation
    pg.terminate()
    while pg.is_alive():
        pass
    print('propagation ends')

    # labels
    for l in label_list:
        l.terminate()
    print('labels ends')

    # scanners
    for s in scanner_list:
        s.terminate()
    print('scanners ends')

    te_instance.terminate()
    print('timeline ends')

    # ======================= get result from each labels =====================

    detected_label_list = []
    numCollisons_list   = []
    for l in label_list:
        terminated, t = l.getTerminatedTime()
        terminated, num_collisions = l.getNumCollisions()
        if terminated:
            detected_label_list.append((l.deviceId, t))
            numCollisons_list.append(num_collisions)

    detected_label_list.sort(key=lambda x: x[1])
    for name, t in detected_label_list:
        print("{0} detected at {1}".format(name, t))

    # ==== summary

    result = {
        'expId': config['expId'],
        'label_beacon_interval': 0,
        'label_inter-beacon_interval': 0,
        'label_numBeacon': 3,
        'label_beacon_duration': 0.001,
        'label_rx_timeout': 0.002,
        'scanner_listen_duration': 0,
        'time_to_detect_all': 0,
        'number_of_collisions': 0
    }

    param_0, param_1, param_2, param_3, param_4 = label_list[0].getConfigurations()
    print("======================= label configuration ========================")
    print(
        "label_numBeacon = {0:1} inter-beacon interval {1:4}s beacons interval {2:4}s beacon_duration {3:4} rx_timeout {4:4}".format(
            param_0, param_1, param_2, param_3, param_4
        )
    )
    result['label_beacon_interval'] = param_2
    result['label_inter-beacon_interval'] = param_1
    result['label_numBeacon'] = param_0

    param_0, param_1, param_2 = scanner_list[0].getConfigurations()
    print("\n======================= scanner configuration ======================")
    print("numCh = {0:1} listen duration {1:4}s listen pause duration {2:4}s".format(
            param_0, param_1, param_2
        )
    )
    result['scanner_listen_duration'] = param_1

    print("\n======================= Result =====================================")
    print("{0} out of {1} labels are detected within {2} seconds".format(len(detected_label_list), config['num_label'],
                                                                         detected_label_list[-1][1]))
    print("{0} collisions are detected from {1} labels".format(sum(numCollisons_list), len(numCollisons_list)))

    result['time_to_detect_all'] = detected_label_list[-1][1]

    result['number_of_collisions'] = sum(numCollisons_list)

    return result

if __name__ == '__main__':

    config = {
        'expId': 0,
        'pid': 0,
        'num_label': 500,
        'num_scanner': 1,
        'beacon_interval': 2,
        'num_beacon_to_send': 3,
        'rx_timeout': 0.002
    }
    run_sim(config)

        
                