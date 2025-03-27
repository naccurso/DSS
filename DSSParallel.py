import multiprocessing
import signal
import subprocess

def LaunchProcess(inst_args):
    n5G = inst_args[0]
    nNB = inst_args[1]
    RBSet = inst_args[2]
    OutputFilename = f'{n5G}_{nNB}_{RBSet}'

    ArgString = f'DSS.py --n5G={n5G} --nNB={nNB} --RBSet={RBSet} --OutputFile={OutputFilename}'
    print(ArgString)
    return_code = subprocess.call(['python', ArgString.split(' ')])
    return


n5Gs = [200, 400, 600]
nNBs = [10000, 20000, 30000]
instance_args = []

for n5G in n5Gs:
    for nNB in nNBs:
        for RBSet in range(2):
            instance_args.append([n5G, nNB, RBSet])

cpu_pool = multiprocessing.Pool(processes = len(instance_args), initializer = signal.signal, initargs = (signal.SIGINT, signal.SIG_IGN))
proc_outputs = cpu_pool.map_async(LaunchProcess, instance_args)
results = proc_outputs.get()