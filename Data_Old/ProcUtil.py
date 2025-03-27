import matplotlib.pyplot as plt
import csv


fgutil = []
nbutil = []

with open("5GUtilization.csv") as infile:
    reader = csv.reader(infile, delimiter=',')
    next(reader)
    for row in reader:
        if row:
            fgutil.append(float(row[1]))
            nbutil.append(float(row[2]))

window = 1000
start = 0

avgdfgutil = []
avgdnbutil = []


while start < len(fgutil)-1:
    avgdfgutil.append(sum(fgutil[start:min(start+window,len(fgutil)-1)])/window)
    avgdnbutil.append(sum(nbutil[start:min(start+window,len(nbutil)-1)])/window)
    start += window

windows = [window/2 + window*i for i in range(len(avgdfgutil))]

fig, (ax1, ax2, ax3) = plt.subplots(3,1)
ax1.plot(windows, avgdfgutil)
ax1.title.set_text("5G Utilization")
ax1.set_xlabel("Simulation Time (ms)")
ax1.set_ylabel("Utilization (%)")

ax2.plot(windows, avgdnbutil)
ax2.title.set_text("NB-IoT Utilization")
ax2.set_xlabel("Simulation Time (ms)")
ax2.set_ylabel("Utilization (%)")

ax3.plot(windows, [1 - avgdfgutil[i] - avgdnbutil[i] for i in range(len(avgdfgutil))])
ax3.title.set_text("Unused Spectrum")
ax3.set_xlabel("Simulation Time (ms)")
ax3.set_ylabel("Utilization (%)")

fig.tight_layout()

plt.savefig("Util3Axes.png")
plt.clf()


successRate = []
PRBs = [80,85,90,95,99]
with open("NBSuccess.csv") as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        if len(row):
            successRate.append(float(row[0]))

plt.plot(PRBs, successRate, marker='o')
plt.title("Number of 5G PRBs vs NB-IoT Success Rate")
plt.xlabel("Number of 5G PRBs")
plt.ylabel("NB-IoT Success Rate")
plt.xticks([80,85,90,95,100])
plt.grid()
plt.savefig("../Figures/NBSuccess.pdf")
plt.clf()


Delays = []
for r in successRate:
    Delays.append(9*r + 30*(1-r))

plt.plot(PRBs, Delays, marker='o')
plt.title("Number of 5G PRBs vs NB-IoT Delay")
plt.xlabel("Number of 5G PRBs")
plt.ylabel("NB-IoT Delay (s)")
plt.xticks([80,85,90,95,100])
plt.grid()
plt.savefig("../Figures/NBDelayWFailures.pdf")