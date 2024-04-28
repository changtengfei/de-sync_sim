from run_sim import run_sim
import multiprocessing
import itertools
import json

def main():

    max_numCPUs         = multiprocessing.cpu_count()

    config_num_labels          = [1000 for i in range(100)]
    config_num_scanners        = [1 for i in range(1)]
    config_beacon_intervals    = [2.0, 1.0]
    config_num_beacon_to_send  = [3]
    config_rx_timeout          = [0.002]

    configs =  itertools.product(config_num_labels, config_num_scanners, config_beacon_intervals, config_num_beacon_to_send, config_rx_timeout)

    numCPUs         = max_numCPUs
    numRuns = len(config_num_labels) * len(config_num_scanners) * len(config_beacon_intervals) * len(config_num_beacon_to_send) * len(config_rx_timeout)
    if numRuns < max_numCPUs:
        numCPUs = numRuns

    multiprocessing.freeze_support()
    pool = multiprocessing.Pool(numCPUs)
    async_results = pool.map_async(
        run_sim,
        [
            {
                'expId': expId,
                'num_label': num_labels,
                'num_scanner': num_scanners,
                'beacon_interval': beacon_interval,
                'num_beacon_to_send': num_beacon_to_send,
                'rx_timeout' : rx_timeout
            } for [expId, (num_labels, num_scanners, beacon_interval, num_beacon_to_send, rx_timeout)] in enumerate(configs)
        ]
    )

    results = async_results.get()
    print("Final result = {0}".format(results))
    # ======================= store to file ===================================
    with open("results.json", 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == '__main__':

    main()