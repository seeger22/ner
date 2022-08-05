import pickle


def _main_merge(res1, res2, merge_map = None):
    if merge_map == None:
        raise ValueError('No Merge Map given.')
    merge_map = _refine_map(merge_map)
    final_cluster = {}
    #key1_merged = {}
    key2_merged = {}
    id = 0
    
    for key1 in res1.keys():
        if key1 in merge_map.keys():
            new_set = res1[key1]
            for key2 in merge_map[key1]:
                new_set |= res2[key2]
                if key2 in key2_merged:
                    key2_merged[key2].append(key1)
                else:
                    key2_merged[key2] = [key1]
                    
            final_cluster[id] = new_set
        else:
            final_cluster[id] = res1[key1]
        id += 1
    
    for key in res2.keys():
        if key not in key2_merged:
            final_cluster[id] = res2[key]
            id += 1
    
    print('Length of Final Cluster:\t', len(final_cluster))
    print('Length of Cluster1:\t', len(res1))
    print('Length of Cluster2:\t', len(res2))
    return final_cluster

def _store_cluster(final_cluster, outfile):    
    print(final_cluster)
    with open(outfile, "wb") as F:
        pickle.dump(final_cluster, F)
    F.close()
    print('Done')