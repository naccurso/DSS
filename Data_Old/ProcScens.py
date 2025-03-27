import csv
import matplotlib.pyplot as plt

n5Gs = [200,400,600]
nNBs = [10000,20000,30000]
nPRBs = [80,85,90,95,99]


linestyles = ['-', '--', ':']

AllDelays = []
AllSuccesses = []
usersList = []

for n5G in n5Gs:
    for nNB in nNBs:
        successRates = []
        NBDelays = []
        success_file_name = f'NBSuccess_{n5G}_{nNB}.csv'
        delay_file_name = f'NBDelays_{n5G}_{nNB}.csv'
        with open(success_file_name) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            for row in reader:
                if row:
                    successRates.append(float(row[0]))

        with open(delay_file_name) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            for row in reader:
                if row:
                    NBDelays.append([int(row[0]), int(row[1])])
        
        avgDelays = []
        for prb in nPRBs:
            tempDelays = []
            for nbd in NBDelays:
                if nbd[0] == prb:
                    tempDelays.append(nbd[1])

            avgDelays.append(sum(tempDelays) / len(tempDelays))

        plt.plot(nPRBs, successRates, label=f'{n5G} 5G Users, {nNB} NB-IoT Users', linestyle=linestyles[int(n5G/200) - 1], marker='o')
        usersList.append([n5G, nNB])
        AllDelays.append(avgDelays)
        AllSuccesses.append(successRates)

plt.title("NB-IoT Success Rates vs Number of 5G PRBs")
plt.xlabel("Number of 5G PRBs")
plt.ylabel("NB-IoT Success Rate")
plt.xticks([80,85,90,95,100])
plt.legend()
plt.grid()
plt.savefig("../Figures/NBSuccessRate.pdf")
plt.clf()

with open("NBDSSDelays.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(["5G PRBs", "Number of 5G Users", "Number of NB-IoT Users", "NB Raw Latency (ms)", "NB SuccessRate"])
    for i, ds in enumerate(AllDelays):
        users = usersList[i]
        ss = AllSuccesses[i]
        for j in range(len(ds)):
            writer.writerow([nPRBs[j], users[0], users[1], ds[j], ss[j], ds[j]*ss[j] + 30000*(1-ss[j])])
        plt.plot(nPRBs, [ds[j]*ss[j] + 30000*(1-ss[j]) for j in range(len(ds))], label=f'{users[0]} 5G Users, {users[1]} NB-IoT Users', linestyle=linestyles[int(users[0]/200)-1], marker='o')

plt.title("NB-IoT Delay vs Number of 5G PRBs")
plt.xlabel("Number of 5G PRBs")
plt.ylabel("NB-IoT Delay (ms)")
plt.xticks([80,85,90,95,100])
plt.legend()
plt.grid()
plt.savefig("../Figures/NBDelayScenarios.pdf")
plt.clf()