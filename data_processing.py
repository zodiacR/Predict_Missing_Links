#!/usr/bin/python
#-*-coding:utf-8 -*-
#Author   : Xuanli He, Lingjuan Lyu, Hao Duan
#Version  : 1.5
#Filename : data_processing.py
from os import path
from math import log
from math import sqrt
from random import shuffle
from random import sample
from random import choice
import cPickle as pickle
import csv

MAIN_PATH = "./data"
RAW = "train.txt"
INST = "train_instance.csv"
TEST = "test-public.txt"
RANK = "final_tr-2.txt"
out_edges = {}
in_edges = {}
instances = []
rank_less = []
rank_more = []
nodes = set()
edges = []
exists = []
test_instances = []
page_rank_prob = []

def ConstrRank():
    """
    read rank file and split ranked to two parts
    """
    with open(path.join(MAIN_PATH, RANK)) as f:
        ranked_data = []
        for line in f:
            ranked_data.append(line.strip().split()[0]) 

    threshold = 5000
    global rank_less
    global rank_more
    rank_less = ranked_data[:threshold]
    rank_more = ranked_data[threshold:]

    with open(path.join(MAIN_PATH, INST)) as f:
        for line in f:
            line = line.strip().split(",")
            exists.append(line[0:2])

def ConstrDict(raw_data):
    """
    construct outedges' and inedges' lists for each node
    """
    if (path.exists("processed_out.txt") and
            path.exists("processed_in.txt")):
        with open("processed_out.txt") as out:
            global out_edges
            out_edges = pickle.load(out)
        with open("processed_in.txt") as fin:
            global in_edges
            in_edges = pickle.load(fin)
            print len(in_edges.keys())
        with open("nodes.txt") as n:
            global nodes
            nodes = pickle.load(n)
            print "nodes: ", len(nodes)
    else:
        # read each line and construct a dictionary to store
        # sources and destinations
        for line in raw_data:    
            splitted_line = line.split()
            # source is the first element in a line, the rest of elements
            # are destinations
            threshold = 10000
            src, dests = splitted_line[0], splitted_line[1:threshold]
            # if src is not in the dictionary, create a key-value pair for
            # this src
            out_edges.setdefault(src, set())

            # put all destinations into the list of the corresponding src
            out_edges[src].update(set(dests))

            # construct a set to store all nodes appearing
            nodes.add(src)
            nodes.update(set(dests))

            # create the list of inedges for each node
            for i in out_edges[src]:
                in_edges.setdefault(i, set())
                in_edges[i].add(src)

        nodes = list(nodes)
        # shuffle the order of nodes
        shuffle(nodes)

        with open("processed_out.txt", "wb") as out:
            pickle.dump(out_edges, out)
        with open("processed_in.txt", "wb") as fin:
            pickle.dump(in_edges, fin)
        with open("nodes.txt", "wb") as n:
            pickle.dump(nodes, n)


    # construct edge list
    for src, dests in out_edges.iteritems():
        pairs = [(src, dest) for dest in dests if (src, dest) not in
                exists]
        edges.extend(pairs)

def ConstrFeature(upper_bound):
    """
    create positive and negative instances
    """
    #upper_bound = 20000
    steps = 0
    marked_samples = sample(edges, upper_bound)
    for src, dest in marked_samples:
        print "positive steps: %f" % (float(steps)/upper_bound)

        # construct features
        features = Features(src, dest)
        # class
        features.append(1)

        # add an instance to instance list
        instances.append(features)

        steps += 1

    # sample nodes
    dests_samples = sample(nodes, upper_bound)
    # sample 20% nodes whoes outdegrees is less than median value
    low_out_point = [choice(rank_less) for i in range(int(upper_bound*0.2))]
    # sample 80% nodes whoes outdegrees is greater than median value
    high_out_point = [choice(rank_more) for i in range(int(upper_bound*0.8))]

    # build instances with four features
    for num, val in enumerate(dests_samples):
        print "Progress: ", num / float(upper_bound)

        # 20% nodes
        if (num < upper_bound * 0.2):
            x, y = low_out_point[num], val
        # 80% nodes
        else:
            x, y = high_out_point[num-int(upper_bound*0.2)],val

        features = Features(x, y)

        if x in out_edges.keys():
            if y in out_edges.get(x):
                features.append(1)
            else:
                features.append(0)
        else:
            features.append(0)

        instances.append(features) 

def Features(src, dest):
    """
    create instances for training data
    --first feature is the amount of outedges of source node;
    --second feature is the amount of inedges of destination node;
    --third feature is jaccard value which is the intersection's
      division by union
    --fourth feature is the amount of nodes followed by both
      destination node and source node

    """ 
    # find common nodes of x and y
    common_out_x = out_edges.get(src,set())
    common_out_y = out_edges.get(dest, set())
    common_in_x = in_edges.get(src, set())
    common_in_y = in_edges.get(dest, set())


    intersection = (common_in_x|common_out_x) & \
                (common_in_y|common_out_y)
    union = (common_in_x|common_out_x) | \
                (common_in_y|common_out_y)

    # cosine similarity
    connected_x = common_out_x | common_in_x
    connected_y = common_out_y | common_in_y
    prod_xy = float(len(connected_x)*len(connected_y))
    cosine = len(intersection) / prod_xy if prod_xy != 0.0 else 0

    # jaccard
    jaccard = float(len(intersection)) / len(union) \
                if len(union) > 0 else 0

    jaccard_mutate = Jaccard(dest, out_edges.get(src))

    #
    # compute the adamic/adar value of source node and
    # destination node
    adar_set = 0
    for z in intersection:
        degrees = 0
        # degrees of a common node
        if out_edges.get(z):
            degrees += len(out_edges[z]) 
        if in_edges.get(z):
            degrees += len(in_edges[z]) 

        if degrees != 0:
            adar_set += 1 / log(degrees)

    # preferential attachment
    pref_attach = len(connected_x) * len(connected_y)

    # kn1
    w_src_out = 1 / sqrt(1+len(common_out_x))
    w_dest_in = 1 / sqrt(1+len(common_in_y))
    w_kn1 = w_src_out * w_dest_in


    #return [len(common_out_x), len(common_in_y), jaccard, adar_set]
    return [src,
            dest,
            len(common_out_x),
            len(common_in_x),
            len(common_out_y),
            len(common_in_y), 
            len(intersection),
            cosine,
            jaccard,
            jaccard_mutate,
            adar_set,
            pref_attach,
            w_kn1]

def Jaccard(dest, dests):
    """
    compute the average jaccard value of dests and dest
    """
    # find common nodes of x and y
    jaccard_sum = 0.0
    for d in dests:
        common_out_x = out_edges.get(dest,set())
        common_out_y = out_edges.get(d, set())
        common_in_x = in_edges.get(dest, set())
        common_in_y = in_edges.get(d, set())


        intersection = (common_in_x|common_out_x) & \
                    (common_in_y|common_out_y)
        union = (common_in_x|common_out_x) | \
                    (common_in_y|common_out_y)

        jaccard = float(len(intersection)) / len(union) \
                    if len(union) > 0 else 0

        jaccard_sum += jaccard

    return jaccard_sum/len(dests) if len(dests) else 0.0

    
def PersonalizedPageRank():
    """
    """
    with open(path.join(MAIN_PATH, TEST)) as f:
        for index, line in enumerate(f):
            # read each line in test file
            line = line.strip().split("\t")
            # acquire follwer and following
            src, dest = line[1:]
            pagerank = PageRank(src)
            prob = pagerank.get(dest, 0.0)
            #test_instances.append(features)
            page_rank_prob.append((index+1, prob))

            print "Progress:", index / float(2000)
    # write results of page rank to csv file
    with open(path.join(MAIN_PATH, "page_rank.csv"), "wb") as f:
        writer = csv.writer(f, delimiter=",")

        for prob in page_rank_prob:
            writer.writerow(prob)

def PageRank(start):
    """
    calculate a personalized PageRank around the given user,and return
    a list of the nodes with highest personalized PageRank scores.
    """
    probs = {}
    probs[start] = 1
    num_page_rank_iterations = 3
    maximum = 25

    PageRankProbs = PageRankHelper(start,
                                   probs,
                                   num_page_rank_iterations)

    PageRankProbs = zip(PageRankProbs.iterkeys(),
                        PageRankProbs.itervalues())

    PageRankProbs = [(node,score) for node, score in PageRankProbs\
                        if node not in out_edges.get(start) and node != start]
    PageRankProbs.sort(key=lambda x:x[1],reverse=True)

    return dict(PageRankProbs[:maximum])

def PageRankHelper(start, probs, numIterations, alpha=0.5):
    """
    Simulate running a personalized PageRank for one iterations
    """
    if numIterations <= 0:
        return probs
    else:
        ProbsPropagated = {}

        # with probability 1-alpha, we teleport back to the start
        # node
        ProbsPropagated[start] = 1 - alpha
        
        # Propagate the previous probabilities
        for node, prob in probs.iteritems():
            forwards = list(out_edges.get(node, set()))
            backwards = list(in_edges.get(node, set()))


            # With probability alpha, we move to a follwer
            # And each node distributes its current probability
            # equally to its neighbours.

            ProbtoPropagate = alpha * prob / (len(forwards)+len(backwards))

            for neighbour in (forwards+backwards):
                if not ProbsPropagated.has_key(neighbour):
                    ProbsPropagated[neighbour] = 0

                ProbsPropagated[neighbour] += ProbtoPropagate

        return PageRankHelper(start, ProbsPropagated, numIterations-1, alpha)

def ConstrTest():
    """
    read raw data from test file
    create test instances
    """
    with open(path.join(MAIN_PATH, TEST)) as f:
        for line in f:
            line = line.strip().split("\t")
            src, dest = line[1:]
            features = Features(src, dest)
            test_instances.append(features)


def Dump():
    """
    dump instances to a file
    """
    with open(path.join(MAIN_PATH, INST), "wb") as f:
        writer = csv.writer(f, delimiter=",")

        for inst in instances:
            writer.writerow(inst)
            
    with open(path.join(MAIN_PATH, "test_instances.csv"), "wb") as f:
        writer = csv.writer(f, delimiter=",")

        for inst in test_instances:
            writer.writerow(inst)

if __name__ == "__main__":
    # read raw data from train.txt and construct a src-dests
    # dictionary
    ConstrRank()
    with open(path.join(MAIN_PATH, RAW)) as raw_data:
        ConstrDict(raw_data)

    #construct instances
    ConstrFeature()
    ConstrTest()

    ##dump instances to file
    Dump()
