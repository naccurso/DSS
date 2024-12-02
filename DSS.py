import csv
import DSSFunctions as DF
import random as rd
import matplotlib.pyplot as plt
import scipy.stats as stats

# Variables

nNB = 20000
n5G = 1000
lambdaNB = 1/30000 # Odds in each time step (ms) of generating a packet
lambda5G = 1/12.5 # Approximates video streaming traffic
PacketSizeDist = stats.truncpareto(1.2, 1000) # Bits generated

TotalRBs = 100
nNBRBs = 5
n5GRBs = TotalRBs - nNBRBs
NBDelayConstraint = 9000 # milliseconds
simTime = 100000 # milliseconds

# Determine the maximum number of supported NB-IoT users
NBDelayList = DF.ReadNBDelays('NBDelays.csv')
MaxNBUsers = DF.DetermineNBUserCapacity(NBDelayList, NBDelayConstraint, nNBRBs)
print(MaxNBUsers)


# Stuff to be used throughout main loop
transmissionQueue = []
fgtxusers = []
fgidleusers = set()
nbtxusers = []
nbidleusers = set()
for u in range(n5G):
    fgidleusers.add(u)
for u in range(nNB):
    nbidleusers.add(u)

MCSTable = DF.ReadMCSTable()
TBSTable = DF.ReadTBSTable()

[fgPositions, nbPositions] = DF.AssignUEPositions(n5G, nNB, 1000)

# Tracker Lists
fgutilization = []
nbin5gutilization = []
nbutilization = []
queued5gusers = []
queuednbusers = []

# MAIN LOOP

for t in range(simTime):
    print(t)
    # Identify completed NB-IoT traffic
    doneindices = []
    for user in nbtxusers:
        if user[1] == t:
            nbidleusers.add(user[0])
            doneindices.append(user)

    # Remove completed traffic from NB-IoT queue
    for user in reversed(doneindices): # Reverse order, mutability issues
        nbtxusers.remove(user)

    # Generate Traffic for NB-IoT
    generatingNBusers = []
    for user in nbidleusers:
        r = rd.uniform(0,1)
        if r < lambdaNB: # Packet is generated
            if len(nbtxusers) < MaxNBUsers: # Still some nbiot resources that can be used
                nbtxusers.append([user, t + NBDelayConstraint])
            else: # No available nbiot resources, use 5g instead
                fgtxusers.append([user, 0, 1]) # append with value '0' indicating low priority tx
            generatingNBusers.append(user)
    nbutilization.append(len(nbtxusers) / MaxNBUsers)

    # Remove generating users from idle set
    for user in generatingNBusers:
        nbidleusers.remove(user)


    # Generate Trafic for 5G
    generating5Gusers = []
    for user in fgidleusers:
        r = rd.uniform(0,1)
        if r < lambda5G: # Packet is generated
            numberOfBits = PacketSizeDist.rvs(size=1)
            distance = (fgPositions[user][0] ** 2 + fgPositions[user][1] ** 2) ** 0.5
            SINR = DF.CalcSINR(distance)
            MCS = DF.SINRtoMCS(SINR, MCSTable)
            nRBs = 1
            while True:
                TBS = DF.MCStoTBS(MCS, nRBs, TBSTable)
                if numberOfBits < TBS:
                    break
                else:
                    nRBs += 1
            fgtxusers.append([user, 1, nRBs])
            generating5Gusers.append(user)
        
    # Remove generating users from idle set
    for user in generating5Gusers:
        fgidleusers.remove(user)

    # Send Queued Traffic

    AvailRBs = n5GRBs

    # First loop through giving priority to 5G users
    for user in fgtxusers[:]: # Iterate over a copy of tx users instead of the list itself
        if user[1] == 1: # Indicates 5G user
            # Send the packet
            AvailRBs -= 1
            if AvailRBs == 0:
                break
            # Remove user from fgtxusers
            fgtxusers.remove(user)
            fgidleusers.add(user[0])
    fgutilization.append((n5GRBs - AvailRBs) / n5GRBs)
    RBsLeftforNB = AvailRBs
    
    # Loop through again for any NB-IoT users
    if AvailRBs:
        for user in fgtxusers[:]: # Any remaining user at this point in the code will be NB, so don't need to check
            #Send the packet
            AvailRBs -= 1
            if AvailRBs == 0:
                break
            # Remove user from fgtxusers
            fgtxusers.remove(user)
    nbin5gutilization.append((RBsLeftforNB - AvailRBs) / n5GRBs)
        
    qd5g = 0
    for user in fgtxusers:
        if user[1] == 1:
            qd5g += 1
    queued5gusers.append(qd5g)
    queuednbusers.append(len(fgtxusers) - qd5g)


# Plot stuff

# Utilization between each network in the 5g band
plt.plot(range(simTime), fgutilization, label='5G Users')
plt.plot(range(simTime), nbin5gutilization, label='NB-IoT Users')
plt.title("Number of RBs used by 5G Users and NB IoT Users in 5G Band")
plt.xlabel("Simulation Time (ms)")
plt.ylabel("Percentage of Total RBs Used")
plt.legend()
plt.grid()
plt.savefig("5GUtilization.png")
plt.clf()

# Utilization of the nb-iot band
plt.plot(range(simTime), nbutilization)
plt.title("Utilization of the NB-IoT Network")
plt.xlabel("Simulation Time (ms)")
plt.ylabel("NB-IoT Utilization")
plt.grid()
plt.savefig("NBUtilization.png")
plt.clf()

# Queued NB-IoT users
plt.plot(range(simTime), queuednbusers)
plt.title("Number of queued NB-IoT users in the 5G band")
plt.xlabel("Simulation Time (ms)")
plt.ylabel("Number of Users")
plt.grid()
plt.savefig("NBQueued.png")
plt.clf()

# Queued 5G users
plt.plot(range(simTime), queued5gusers)
plt.title("Number of queued 5G users")
plt.xlabel("Simulation Time (ms)")
plt.ylabel("Number of Users")
plt.grid()
plt.savefig("5GQueued.png")