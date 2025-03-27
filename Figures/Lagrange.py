import numpy as np
from scipy.optimize import Bounds
from scipy.optimize import minimize
import csv
import math
import matplotlib.pyplot as plt
import random as rd

def LTEThroughput(RBTuple):
    # Objective function
    # Scipy only considers minimization, so we look to minimize the negative throughput
    LTERBs = RBTuple[0]
    return LTERBs * tbs * 1000

def NBDelay(RBTuple, nuNB):
    # Return negative number if threshold not met, positive if met

    NBRBs = RBTuple[1]

    try:
        base = math.floor(nuNB/NBRBs) # Number of NB UEs per RB
        if base == 0:
            NBDelay = NBPreComp[0]
        else:
            remainder = int((nuNB/100) % NBRBs)
            NBDelay = (NBPreComp[int(min(base+1, len(NBPreComp)-1))]*remainder + (NBRBs-remainder)*NBPreComp[int(min(base, len(NBPreComp)-1))])/NBRBs
    except:
        NBDelay = NBPreComp[-3]

    return NBDelay

NBPreComp = []
with open('../NBDelays.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    rows = list(reader)
    for row in rows:
        for elem in row:
            NBPreComp.append(float(elem))

print(NBPreComp)


uNBs = [1000*i for i in range(1,21)]
#u5Gs = [50*i for i in range(1,20)]
u5G = 400
TotalRBs = 100
tbs = 500
lams = [1000,2000,5000,10000]

for lam in lams:
    optSoln = []
    for uNB in uNBs:
        best = 0
        bestReward = -100000000000
        for NBRBs in range(1,21):
            RBTuple = (TotalRBs-NBRBs, NBRBs)
            D = NBDelay(RBTuple, uNB)
            T = LTEThroughput(RBTuple)
            print(D)
            #print(T)
            R = T - lam * D
            #print(R)
            if R > bestReward:
                best = NBRBs
                bestReward = R
        optSoln.append(best)
    plt.plot(uNBs, optSoln, label=f"\u03bb = {lam}", marker='o')

plt.title("Optimal Number of NB-IoT PRBs vs Number of NB-IoT Users")
plt.xlabel("Number of NB-IoT Users")
plt.ylabel("Optimal Number of NB-IoT PRBs")
plt.yticks([0,5,10,15,20])
plt.grid()
plt.legend()
#plt.savefig("Figures/LambdaOptSplit.pdf")
plt.clf()


# Gather effective NB-IoT delays for 600 case
effectiveDelays = []
with open("../Data/NBDSSDelays.csv") as infile:
    reader = csv.reader(infile, delimiter=',')
    next(reader)
    for row in reader:
        if row[1] == '600':
            effectiveDelays.append([int(row[0]),int(row[2]),float(row[5])])

lam = 1500
nNBs = [10000,20000,30000]
NBRBss = [1,5,10,15,20]

optSoln1 = []
optSoln2 = []
for nNB in nNBs:
    best1 = 0
    bestReward1 = -100000000000
    best2 = 0
    bestReward2 = -100000000000
    for NBRBs in NBRBss:
        RBTuple = (TotalRBs-NBRBs, NBRBs)
        D1 = NBDelay(RBTuple, nNB)
        for d in effectiveDelays:
            if d[0] == (100-NBRBs) and d[1] == nNB:
                D2 = d[2]
        T = LTEThroughput(RBTuple)
        R1 = T - lam * D1
        R2 = T - lam * D2
        if R1 > bestReward1:
            best1 = NBRBs
            bestReward1 = R1
        if R2 > bestReward2:
            best2 = NBRBs
            bestReward2 = R2
        print("Delay", D2)
        print("Throughput", T)
        print("Reward", R2)
    optSoln1.append(best1)
    optSoln2.append(best2)

plt.plot(nNBs, optSoln1, label="No DSS")
plt.plot(nNBs, optSoln2, label="DSS Enabled")
plt.title("Optimal PRB Allocation vs Number of NB-IoT Users")
plt.xlabel("Number of NB-IoT Users")
plt.ylabel("Number of 5G PRBs")
plt.grid()
plt.legend()
plt.show()