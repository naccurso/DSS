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
    print(RBTuple)
    LTERBs = RBTuple[0]
    return  LTERBs * tbs * 1000

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
with open('NBDelays.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    rows = list(reader)
    for row in rows:
        for elem in row:
            NBPreComp.append(float(elem))


uNBs = [5000*i for i in range(1,6)]
u5Gs = [200 + 10*i for i in range(6)]
#DelayConstraint = 9000
DelayConstraints = [8000, 8500, 9000, 9500, 10000]
TotalRBs = 100

tbs = 5000

for u5G in u5Gs:
    LTEThru = []
    for fgrbs in range(80, 101):
        demand = 2 * u5G
        LTEThru.append(min(demand, LTEThroughput((fgrbs, 0)) / 1000000))
    plt.plot(range(80, 101), LTEThru, label=f'{u5G} Users')


plt.title("5G Throughput vs Number of 5G PRBs")
plt.xlabel("Number of 5G PRBs")
plt.ylabel("5G Throughput (Mbps)")
plt.grid()
plt.xticks([80,85,90,95,100])
plt.legend()
#plt.savefig("Figures/5GThru.pdf")
plt.clf()


for uNB in uNBs:
    NBDelays = []
    for nbrbs in range(1, 21):
        NBDelays.append(NBDelay((0, nbrbs), uNB))
    plt.plot(range(1,21), NBDelays, label=f'{uNB} Users')

plt.title("NB-IoT Delay vs Number of NB-IoT PRBs")
plt.xlabel("Number of NB-IoT PRBs")
plt.ylabel("NB-IoT Delay (ms)")
plt.grid()
plt.xticks([0,5,10,15,20])
plt.legend()
#plt.savefig("Figures/NBDelay.pdf")
plt.clf()



for DelayConstraint in DelayConstraints:
    optSplit = []
    for uNB in uNBs:
        found = 0
        for NBRBs in range(1,21):
            RBTuple = (TotalRBs - NBRBs, NBRBs)
            D = NBDelay(RBTuple, uNB)
            if D < DelayConstraint: 
                optSplit.append(NBRBs)
                found = 1
                break
        if not found:
            optSplit.append(20)

    plt.plot(uNBs, optSplit, label=f"D = {DelayConstraint/1000} s", marker='o')

plt.xlabel("Number of NB-IoT Users")
plt.ylabel("Optimal Number of NB-IoT PRBs")
plt.title("Optimal Number of NB-IoT PRBs vs Number of NB-IoT Users")
plt.yticks([0,5,10,15,20])
plt.grid()
plt.legend()
#plt.savefig("Figures/OptSplit.pdf")
plt.clf()



