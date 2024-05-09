from run_sim import run_sim
import multiprocessing
import itertools
import json

def main():

    max_numCPUs         = multiprocessing.cpu_count()
    config_topologies   = ["topology.json" for i in range(100)]

    numCPUs         = max_numCPUs
    numRuns         = len(config_topologies)
    if numRuns < max_numCPUs:
        numCPUs = numRuns
        
    print(enumerate(config_topologies))

    # multiprocessing.freeze_support()
    # pool = multiprocessing.Pool(numCPUs)
    # async_results = pool.map_async(
        # run_sim,
        # [
            # {
                # 'expId': expId,
                # 'interval': 2,
                # 'topology_file': topology,
                # 'wake_delay':   1,
            # } for [expId, topology] in enumerate(config_topologies)
        # ]
    # )

    # results = async_results.get()
    # print("Final result = {0}".format(results))
    # # ======================= store to file ===================================
    # with open("results.json", 'w') as f:
        # json.dump(results, f, indent=4)

if __name__ == '__main__':

    main()