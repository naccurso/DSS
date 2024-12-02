import csv
import math
import numpy as np
import random as rd
import matplotlib.pyplot as plt

def ReadNBDelays(filename):
    # Read in the file containing NB-IoT precomputed delays and return it
    NBDelays = []
    with open(filename, 'r') as infile:
        reader = csv.reader(infile, delimiter=' ')
        for row in reader:
            for elem in row:
                NBDelays.append(float(elem))
    return NBDelays


def DetermineNBUserCapacity(NBDelays, delayconstraint, NBRBs):
    #Calculate the NB-IoT capacity based on a delay constraint and the precomputed delay expectations
    n = 0
    while True:
        if NBDelays[round(n/NBRBs)] < delayconstraint:
            n += 1
        else:
            return n

def AssignUEPositions(n5G, nNB, radius):
    # Place users randomly around a BS within a given radius
    fgpositions = []
    nbpositions = []
    r2 = radius ** 2

    # 5G users
    for u in range(n5G):
        while True:
            x = rd.uniform(-1 * radius, radius)
            y = rd.uniform(-1 * radius, radius)
            if x ** 2 + y ** 2 < r2:
                fgpositions.append([x, y])
                break
    
    # NB users
    for u in range(nNB):
        while True:
            x = rd.uniform(-1 * radius, radius)
            y = rd.uniform(-1 * radius, radius)
            if x ** 2 + y ** 2 < r2:
                nbpositions.append([x, y])
                break
    
    return(fgpositions, nbpositions)

def ABGPathLoss(distance):
    # Calculate the alpha-beta-gamma pathloss based on the distance
    alpha = 2.8
    beta = 11.4
    gamma = 2.3
    sigma = 4.1
    frequency = 3.5

    x_sig = np.random.normal(loc=0, scale=sigma)

    return 10 * alpha * math.log10(distance) + beta + 10 * gamma * math.log10(frequency) + x_sig

def ReadMCSTable():
    # Read in the MCS table 
    # Return [MCS index, modulation order, rate, target sinr]
    MCSTable = []
    with open("MCStable.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader, None)
        for row in reader:
            MCSTable.append([int(row[0]), int(row[1]), int(row[2]), float(row[3])])

    return MCSTable

def CalcSINR(distance):
    # Calculate the SINR of a user at a given distance
    txPower = 23 # dBm
    noisePower = -80 # dBm
    pathloss= ABGPathLoss(distance)
    return txPower - noisePower - pathloss

def SINRtoMCS(SINR, MCSTable):
    # Convert SINR to MCS index
    # Return [MCS index, modulation order, rate]
    MCSidx = MCSTable[0][0:3] # Init at lowest index
    for MCS in MCSTable:
        if SINR < MCS[3]:
            return MCSidx
        else:
            MCSidx = MCS[0:3]
    # Catch in case SINR exceeds limits in file
    return MCSidx

def ReadTBSTable():
    # Read in the TBS table for Ninfo < 3824 once for efficiency
    TBSs = []
    with open("TBSTable.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader, None)
        for row in reader:
            TBSs.append([int(row[0]), int(row[1])])

    return TBSs

def MCStoTBS(MCS, nRBs, TBSTable):
    # Calculate TBS based on 5G standards
    # Input MCS = [MCS index, modulation order, rate]
    Nsc = 12
    Nsymb = 12
    NDMRS = 6
    Noh = 6

    rate = MCS[2] / 1024
    modOrder = MCS[1]

    NREprime = Nsc * Nsymb - NDMRS - Noh
    NRE = min(NREprime, 156)

    Ninfo = NRE * rate * modOrder * nRBs

    if Ninfo <= 3824:
        n = max(3, math.floor(math.log2(Ninfo))-6)
        Ninfoprime = max(24,2**n*math.floor(Ninfo/2**n))
        BestTBS = 0
        for TBS in TBSTable:
            if Ninfoprime >= TBS[1]:
                BestTBS = TBS[1]
            else:
                return BestTBS
        return BestTBS

    else:
        n = math.floor(math.log2(Ninfo - 24)) - 5
        Ninfoprime = 2**n * round((Ninfo - 24) / 2**n)

        if rate <= 0.25:
            C = math.ceil((Ninfoprime + 24) / 3816)
            return 8 * C * math.ceil((Ninfoprime + 24) / (8 * C)) - 24

        elif Ninfoprime < 8424:
            return 8 * math.ceil((Ninfoprime + 24) / 8) - 24
        
        else:
            C = math.ceil((Ninfoprime + 24) / 8424)
            return 8 * C * math.ceil((Ninfoprime + 24) / (8 * C)) - 24



if __name__ == '__main__':
    MCSTable = ReadMCSTable()
    TBSTable = ReadTBSTable()
    
    distances = []
    TBSs = []
    for i in range(1000):
        d = rd.uniform(0,1000)
        distances.append(d)
        SINR = CalcSINR(d)
        MCS = SINRtoMCS(SINR, MCSTable)
        TBS = MCStoTBS(MCS, 1, TBSTable)
        TBSs.append(TBS)

    plt.scatter(distances, TBSs)
    plt.title("TBS vs Distance")
    plt.xlabel("Distance (m)")
    plt.ylabel("TBS")
    plt.grid()
    plt.savefig("TBSvsDistance.png")