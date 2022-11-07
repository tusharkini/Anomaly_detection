import numpy as np
import random
import matplotlib.pyplot as plt
import time
from scipy.sparse import csr_matrix
from scipy.sparse import lil_matrix
from scipy.sparse import eye
from scipy.sparse.linalg import spsolve
from scipy.sparse import diags
import os, os.path
import sys



def get_number_nodes(text_file_path):
    f = open(text_file_path, 'r')
    #read first line of file and get the 1st number which is the number of vertices
    n = int(next(f).split(" ")[0])
    f.close()
    return n

def get_adjacency_matrix(text_file_path):
    f = open(text_file_path, 'r')
    # n is number of vertices
    n = int(next(f).split(" ")[0])
    A = lil_matrix((n,n),dtype=float)
    for i in f.readlines():
        edge = i.split(" ")
        n1 = int(edge[0])
        n2 = int(edge[1])
        # we assume the graph is undirected in nature as stated and assumed in the experimentation part of the paper
        A[n1,n2] = 1
        A[n2,n1] = 1
    f.close()
    return A

def partition (list_in, n):
    random.shuffle(list_in)
    return [list_in[i::n] for i in range(n)]

def get_s(groups,g,n):
    s = np.zeros((n,g))
    for k in range(0,g):
        for i in groups[k]:
            s[i][k] = 1
    return s

def moving_range_average(x):
    n = len(x)
    M = []
    for i in range(1,n):
        M.append(abs(x[i]-x[i-1]))
    return np.sum(M)/(n-1)

def calculate_sim(dataset_path, dataset_file_suffix,num_graphs):
    sim_values = []
    for graph_num in range(0,num_graphs-1):
        start = time.time()
        # get the graphs in adjacency matrix representation
        A1 = get_adjacency_matrix(dataset_path+str(graph_num)+dataset_file_suffix)
        A2 = get_adjacency_matrix(dataset_path+str(graph_num+1)+dataset_file_suffix)
        # D are the diaginal degree matrices
        D1 = diags(np.array(A1.sum(axis = 0)).flatten(),dtype=float)
        D2 = diags(np.array(A2.sum(axis = 0)).flatten(),dtype=float)
        # n is the number of vertices in the graph
        n = get_number_nodes(dataset_path+str(graph_num)+dataset_file_suffix)
        # I is a identity matrix of size n
        I = eye(n)
        
        nodes = list(range(0,n))
        #this is the g value from the paper and we take it to be min 10
        num_groups = max(int(n/100),10)
        groups = partition(nodes,num_groups)
        # s is the sum of affinity unit vectors e with 1 in the vertex position 
        s = np.array(get_s(groups,num_groups,n))
        # getting compressed row matrices for efficient processing.
        I = csr_matrix(I)
        D1 = csr_matrix(D1)
        D2 = csr_matrix(D2)
        A1 = csr_matrix(A1)
        A2 = csr_matrix(A2)
        # value of epsilon belongs to (0,1) and given by formula in table 1 in paper
        #max_dii_1 = max(np.array(D1.toarray()).sum(axis=0))
        max_dii_1 = D1.max()
        print(max_dii_1)
        e_1 = 1/(1+max_dii_1)
        max_dii_2 = D2.max()
        e_2 = 1/(1+max_dii_2)
        print(e_1,e_2)
        # solve the equation introduced in section 2.2
        S1 = spsolve((I+(D1*e_1**2)-(A1*e_1)),s)
        S2 = spsolve((I+(D2*e_2**2)-(A2*e_2)),s)
        # using euclidian distance as mentioned in the paper
        d = np.sum(np.square(np.sqrt(S1)-np.sqrt(S2)))
        # calculating the similarity sim that belongs in [0,1]
        sim = 1/(1+d)
        # append the sim values to a list so that they can be saved
        sim_values.append(sim)
        end = time.time()
    print('Time elapsed: '+str(end-start)+' seconds')
    return sim_values
    
def calculate_threshold(sim_timeline):
    median = np.median(sim_timeline)
    mean = moving_range_average(sim_timeline)
    # calculating the thresholds according to formula given in project objective
    upper_threshold = median + 3*mean
    lower_threshold = median - 3*mean
    return lower_threshold, upper_threshold

def save_plot(lower_threshold, upper_threshold, sim_values, dataset_name):
    fig = plt.figure()
    plt.axhline(y=upper_threshold,linestyle='--',color='red')
    plt.axhline(y=lower_threshold,linestyle='--',color='red')
    plt.xlabel('Time Elapsed')
    plt.ylabel('sim(G_t,G_{t+1}')
    plt.style.use('default')
    plt.plot(sim_values,'.')
    fig.savefig('../results/'+dataset_name+'_time_series.png')
    return None



def main():
    # Input validation
    if len(sys.argv) != 2:
        print("IMPROPER INPUT FORMAT!\n Please enter as python anomaly.py <name_of_dataset_directory>")
        exit(1)
    
    dataset_name = str(sys.argv[1])    
    dataset_path = "../datasets/" + dataset_name+"/"
    # get the number of graph screenshots given in the dataset folder for given graph
    number_graphs = len([name for name in os.listdir(dataset_path) if os.path.isfile(os.path.join(dataset_path, name))])
    print(number_graphs)
    dataset_file_suffix = "_"+dataset_name+".txt"    
    sim_values = calculate_sim(dataset_path,dataset_file_suffix,number_graphs)
    # save the sim values in txt file
    np.savetxt('../results/'+dataset_name+'_time_series.txt',sim_values)
    lower_threshold, upper_threshold = calculate_threshold(sim_values)
    #plot and save the sim values and the threshold lines
    save_plot(lower_threshold, upper_threshold, sim_values, dataset_name)
    

if __name__ == "__main__":
    main()