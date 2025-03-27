import DSSFunctions as DF
import matplotlib.pyplot as plt

NBDelayList = DF.ReadNBDelays('NBDelays.csv')
NBUsers = 1000
Delays = []

for nRBs in range(1,21):
    Delays.append(NBDelayList[round(NBUsers / nRBs)])

plt.plot(range(1,21), Delays)
plt.title(f"NB-IoT Delay vs Number of Assigned PRBs for {NBUsers} Users")
plt.xlabel("Number of Assigned PRBs")
plt.xticks([0,5,10,15,20])
plt.ylabel("NB-IoT Delay (ms)")
plt.grid()
plt.savefig("Figures/NBDelayvsPRBs.pdf")