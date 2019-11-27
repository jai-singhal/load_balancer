import os
import subprocess
import re
import matplotlib.pyplot as plt
import pandas as pd

""" 
    To read the dumps: 
    $ tcpdump -r dump.pcap
"""
def getLogs(folder, switch, port):
    si_ethj = subprocess.Popen(
        ["tcpdump", "-r", "logs/{}/s{}-eth{}.pcap".format(folder, switch, port)],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    stdout, stderr = si_ethj.communicate()
    return stdout.split("\n")

s1eth4 = getLogs("2019-11-27-19-04", 1, 4)
s1eth5 = getLogs("2019-11-27-19-04", 1, 5)
s1eth6 = getLogs("2019-11-27-19-04", 1, 6)

print(len(s1eth4))
print(len(s1eth5))
print(len(s1eth6))

log_data = list()
for line in s1eth4:
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

        # ip_dst_src = re.findall(r"[0-9\.]+\.http > [0-9\.]+", line)
        # if ip_dst_src:
        #     data["type"] = "ack"
        #     data["src"], data["dst"] = ip_dst_src[0].split(">")
        #     data["src"] = data["src"].replace(".http", "").strip()
        #     data["dst"] = data["dst"].replace(".http", "").strip()
        #     data["dst"] = re.sub(r"\.[0-9]{5}", "", data["dst"]).strip()

# print(log_data)
# https://stackoverflow.com/questions/31649669/pandas-groupby-count-string-occurrence-over-column
df = pd.DataFrame(log_data)
df["count"] = df.groupby(["src", "dst"])["time"].transform(lambda x: x).count()
print(df)


# print(log_data)

# plt.plot(x, y) 
  
# plt.xlabel('time') 
# plt.ylabel('y - axis') 
  
# plt.title('My first graph!') 
  
# plt.show() 


# for line in lines:
#     print(line)
#     print("\n\n")