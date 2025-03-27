import csv
import DSSFunctions as DF
import random as rd
import matplotlib.pyplot as plt
import scipy.stats as stats
import argparse


# Parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--n5G')
parser.add_argument('--nNB')
parser.add_argument('--RBSet')
parser.add_argument('--Plot', default=False)
parser.add_argument('--OutputFile')

args = parser.parse_args()
n5G = int(args.n5G)
nNB = int(args.nNB)
RBSet = range(80, 90) if args.RBSet == 1 else range(91,100)
Plot = args.Plot
OutputFile = args.OutputFile

# Variables

#nNBs = [10000, 20000, 30000]
#n5Gs = [200, 400, 600]
lambdaNB = 1/30000 # Odds in each time step (ms) of generating a packet
lambda5G = 1/12.5 # Approximates video streaming traffic
PacketSizeDist = stats.truncpareto(1.2, 1000) # Bits generated

TotalRBs = 100
#nNBRBs = 5
#n5GRBs = TotalRBs - nNBRBs
n5GRBss = [80,85,90,95,99]
#n5GRBss = [90]
NBDelayConstraint = 9000 # milliseconds
simTime = 60000 # milliseconds
timeout = 10000 # NB-IoT timetout in 5G band

MCSTable = DF.ReadMCSTable()
TBSTable = DF.ReadTBSTable()


print(n5G, nNB)

[fgPositions, nbPositions] = DF.AssignUEPositions(n5G, nNB, 1000)

nbDelaysOuterLoop = []
nbSuccessRate = []
fgThroughputs = []
fgThroughputsnoShare = []

nbDelays = []
# MAIN LOOP
for n5GRBs in RBSet:
    # Stuff to be used throughout main loop
    transmissionQueue = []
    fgtxusers = [] # Each element in this array = [user, priority(5g vs nb), number of RBs for tx, number of bits, time stamp]
    fgidleusers = set()
    nbtxusers = []
    nbidleusers = set()
    for u in range(n5G):
        fgidleusers.add(u)
    for u in range(nNB):
        nbidleusers.add(u)

    [fgPositions, nbPositions] = DF.AssignUEPositions(n5G, nNB, 1000)

    # Tracker Lists
    fgutilization = []
    nbin5gutilization = []
    nbutilization = []
    queued5gusers = []
    queuednbusers = []
    TotalData = 0
    RBData = 0

    nbsuccess = 0
    nbfailure = 0


    
    nNBRBs = TotalRBs - n5GRBs
    # Determine the maximum number of supported NB-IoT users
    NBDelayList = DF.ReadNBDelays('NBDelays.csv')
    MaxNBUsers = DF.DetermineNBUserCapacity(NBDelayList, NBDelayConstraint, nNBRBs)
    print(MaxNBUsers)
    for t in range(simTime):
        #print(t)
        # Identify completed NB-IoT traffic
        doneindices = []
        for user in nbtxusers:
            if user[1] == t:
                nbidleusers.add(user[0])
                doneindices.append(user)

        # Remove completed traffic from NB-IoT queue
        for user in reversed(doneindices): # Reverse order, mutability issues
            nbtxusers.remove(user)
            nbDelays.append([n5GRBs, NBDelayConstraint])
            nbsuccess += 1

        # Generate Traffic for NB-IoT
        generatingNBusers = []
        for user in nbidleusers:
            r = rd.uniform(0,1)
            if r < lambdaNB: # Packet is generated
                if len(nbtxusers) < MaxNBUsers: # Still some nbiot resources that can be used
                    nbtxusers.append([user, t + NBDelayConstraint])
                else: # No available nbiot resources, use 5g instead
                    fgtxusers.append([user, 0, 1, 100, t]) # append with value '0' indicating low priority tx
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
                numberOfBits = PacketSizeDist.rvs(size=1) + 160 
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
                fgtxusers.append([user, 1, nRBs, numberOfBits, t])
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
                if AvailRBs >= user[2]: # Enough RBs in current time slot for tx
                    AvailRBs -= user[2]
                if AvailRBs == 0:
                    break
                TotalData += user[3] # Increment the amount of data transmitted for throughput calculation
                # Remove user from fgtxusers
                fgtxusers.remove(user)
                fgidleusers.add(user[0])
        fgutilization.append((n5GRBs - AvailRBs) / n5GRBs)
        RBsLeftforNB = AvailRBs
        
        # Loop through again for any NB-IoT users
        if AvailRBs:
            for user in fgtxusers[:]: # Any remaining user at this point in the code will be NB, so don't need to check
                #Send the packet
                RBData += user[3]
                TotalData += user[3]
                AvailRBs -= 1
                nbsuccess += 1
                if AvailRBs == 0:
                    break
                # Remove user from fgtxusers
                nbDelays.append([n5GRBs, t - user[4]])
                fgtxusers.remove(user)
        nbin5gutilization.append((RBsLeftforNB - AvailRBs) / n5GRBs)

        # Loop through any remaining NB-IoT users, looking for timeouts
        for user in fgtxusers[:]:
            if t - user[4] >= timeout: # timeout has occurred
                nbfailure += 1
                fgtxusers.remove(user)

            
        qd5g = 0
        for user in fgtxusers:
            if user[1] == 1:
                qd5g += 1
        queued5gusers.append(qd5g)
        queuednbusers.append(len(fgtxusers) - qd5g)

    nbSuccessRate.append(nbsuccess / (nbsuccess + nbfailure))

    Throughput = TotalData / (simTime / 1000)
    NBThroughputin5G = RBData / (simTime / 1000)
    #nbDelaysOuterLoop.append(sum(nbDelays)/len(nbDelays))
    print(f"Throughput with sharing = {Throughput}")
    print(f"Throughput without sharing = {Throughput - NBThroughputin5G}")

    fgThroughputs.append(Throughput)
    fgThroughputsnoShare.append(Throughput-NBThroughputin5G)

with open(f"Data/NBSuccess_{OutputFile}.csv", 'w', newline='') as outputfile:
    writer = csv.writer(outputfile, delimiter=',')
    for rate in nbSuccessRate:
        writer.writerow([rate])

with open(f"Data/NBDelays_{OutputFile}.csv", 'w', newline='') as outputfile:
    writer = csv.writer(outputfile, delimiter=',')
    for nbd in nbDelays:
        writer.writerow([nbd[0], nbd[1]])

with open(f"Data/5GUtilization_{OutputFile}.csv", 'w', newline='') as infile:
    writer = csv.writer(infile)
    writer.writerow(["Time (ms)", "5G utilization", "NB-IoT utilization in 5G band"])
    for i in range(simTime):
        writer.writerow([i, fgutilization[i], nbin5gutilization[i]])

with open(f"Data/NBUtilization_{OutputFile}.csv", 'w', newline='') as infile:
    writer = csv.writer(infile)
    writer.writerow(["Time (ms)", "NB-IoT utilization"])
    for i in range(simTime):
        writer.writerow([i, nbutilization[i]])

with open(f"Data/NBQueued_{OutputFile}.csv", 'w', newline='') as infile:
    writer = csv.writer(infile)
    writer.writerow(["Time (ms)", "Number of queued NB-IoT users in 5G band"])
    for i in range(simTime):
        writer.writerow([i, queuednbusers[i]])

'''plt.plot(n5GRBss, nbDelaysOuterLoop)
plt.xlabel("Number of 5G RBs")
plt.ylabel("Average NB-IoT Delay (ms)")
plt.title("Average NB-IoT Delay vs Number of 5G RBs")
plt.grid()
plt.xticks([80,85,90,95,100])
plt.savefig("Figures/NBDelays.pdf")
plt.clf()'''

if Plot:
    plt.plot(n5GRBss, fgThroughputs, label="With Sharing")
    plt.plot(n5GRBss, fgThroughputsnoShare, label="Without Sharing")
    plt.xlabel("Number of 5G PRBs")
    plt.ylabel("Throughput (bits/s)")
    plt.xticks([80,85,90,95,100])
    plt.title(f"5G Throughput vs Number of 5G PRBs - With and Without Sharing")
    plt.grid()
    plt.savefig("Figures/5GThroughputvsRBs.pdf")
    plt.clf()

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

'''
with open("Data/5GQueued.csv", 'w') as infile:
    writer = csv.writer(infile)
    writer.writerow(["Time (ms)", "Number of queued 5G users"])
    for i in range(simTime):
        writer.writerow([i, queued5Gusers[i]])'''