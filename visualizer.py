import os
import subprocess
import re
import matplotlib.pyplot as plt
import pandas as pd
import time
import sys

def getLogs(folder, switch, port):
    si_ethj = subprocess.Popen(
        ["tcpdump", "-r", "logs/{}/s{}-eth{}.pcap".format(folder, switch, port)],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    stdout, stderr = si_ethj.communicate()
    return stdout.split("\n")


def getLogData(data_list):
    log_data = list()
    for line in data_list:
        data = {}
        if line.find("http") != -1:
            data["time"] = re.findall(r"[0-9]+\:[0-9]+\:[0-9]+\.[0-9]+", line)[0]
            ip_src_dst = re.findall(r"[0-9\.]+ > [0-9\.]+\.http", line)
            if ip_src_dst:
                data["type"] = "seq"
                data["src"], data["dst"] = ip_src_dst[0].split(">")
                data["src"] = data["src"].replace(".http", "").strip()
                data["dst"] = data["dst"].replace(".http", "").strip()
                data["src"] = re.sub(r"\.[0-9]{5}", "", data["src"]).strip()
                # data["ack"] = re.findall(r"ack ([0-9]+)", line)[0]
                # data["win"] = re.findall(r"win ([0-9]+)", line)[0]
                log_data.append(data)
    
    df = pd.DataFrame(log_data)
    df["count"] = 1
    df["time"] = df.time.apply(lambda x: float(x[6:10]))
    df = df.groupby(["time"], as_index=False).count()
    df["type"] = "seq"
    return df

def plotter(filename, title):
    # filename = "rr_20_2019-11-27-21-44"

    s1eth4 = getLogs(filename, 1, 4)
    s1eth5 = getLogs(filename, 1, 5)
    s1eth6 = getLogs(filename, 1, 6)
    df1 = getLogData(s1eth4)
    df2 = getLogData(s1eth5)
    df3 = getLogData(s1eth6)
    ax = plt.gca()
    df1.plot(kind='line',x='time',y='count',color='red', ax = ax, label = "s1-eth4")
    df2.plot(kind='line',x='time',y='count',color='blue', ax = ax, label = "s1-eth5")
    df3.plot(kind='line',x='time',y='count',color='yellow', ax = ax, label = "s1-eth6")
    plt.xlabel('Time(in sec)')
    plt.ylabel('No. of packets')
    plt.title('{} congestion plot'.format(title))
    plt.show()

# plotter("main_20_2019-11-27-21-41", "Main Algo")
# plotter("rr_20_2019-11-27-21-44", "Round robin Algo")
# plotter("r_20_2019-11-27-21-47", "Random Algo")

plotter("main_2_2019-11-28-00-53", "Main Algo")

# plotter("rr_1_2019-11-28-00-03", "Round robin Algo")
# plotter("r_20_2019-11-27-21-47", "Random Algo")