"""
TEST
"""
import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from node_vec import *

def gen_base_indicator_features():
    ret = {}
    print("GEN INDICATOR FEATURES")
    for name, node in BASE_GRAPH.node_dict.items():
        if name[0] == "$":
            continue
        print("generating", name)
        temp = BASE_GRAPH.traverse_vectorize(id_set_conditioner(name),
                                             breadth_manager_full, [],
                                             node_entropy_initializer,
                                             node_dummy_top_down,
                                             node_indicator_bottom_up)
        ret[name] = temp[1]

    return ret


def gen_base_entropy_features():
    """
    Generate entropy features
    """
    ret = {}
    print("GEN ENTROPY FEATURES")
    for name, node in BASE_GRAPH.node_dict.items():
        if name[0] == "$":
            continue
        print("generating", name)
        temp = BASE_GRAPH.traverse_vectorize(id_set_conditioner(name),
                                             breadth_manager_full, [],
                                             node_entropy_initializer,
                                             node_entropy_top_down,
                                             node_entropy_top_down)
        ret[name] = temp[1]

    return ret




def calculate_cosine_similarity(items_dict):
    items = list(items_dict.keys())
    vectors = np.array(list(items_dict.values()))

    similarity_matrix = cosine_similarity(vectors)

    similarity_results = {}
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            similarity_results[(items[i], items[j])] = similarity_matrix[i, j]

    return similarity_results

if __name__ == '__main__':
    try:
        with open("./temp_data/indicator_features.pkl", "rb") as fptr:
            indicator_features = pickle.load(fptr)
    except:
        with open("./temp_data/indicator_features.pkl", "wb") as fptr:
            indicator_features = gen_base_indicator_features()
            pickle.dump(indicator_features, fptr)

    try:
        with open("./temp_data/entropy_features.pkl", "rb") as fptr:
            entropy_features = pickle.load(fptr)
    except:
        with open("./temp_data/entropy_features.pkl", "wb") as fptr:
            entropy_features = gen_base_entropy_features()
            pickle.dump(entropy_features, fptr)

    for k, v in indicator_features.items():
        print(k, v)

    indicator_similairty = calculate_cosine_similarity(indicator_features)
    with open("./temp_data/indicator_similairty.pkl", "wb") as fptr:
        pickle.dump(indicator_similairty, fptr)
