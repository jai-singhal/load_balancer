from mininet.net import Mininet
from mytopo import MyTopo
from mininet.node import Controller, RemoteController
from mininet.util import custom, pmonitor
from mininet.link import TCLink, Intf
from mininet.log import info, error, warn, debug

from contextlib import contextmanager
import time
import random
import shutil
import os
import sys
from subprocess import Popen, PIPE, call, check_call
import logging
import threading

fileDownloaded = []
totalFiles = 12


def createDUMPFiles():
    print("Creating DUMP Files")
    try:
        os.mkdir("DUMPS")
    except OSError:
        shutil.rmtree("DUMPS")
        os.mkdir("DUMPS")

    for i in range(1, totalFiles+1):
        with open('DUMPS/file_{}.txt'.format(i), 'wb') as f:
            num_chars = 1024 * 1024 * (2*i)
            f.write(str(random.randint(1, 9)) * num_chars)


@contextmanager
def start_network(network):
    """
    A context manager which starts the Mininet network and ensures that it is
    always properly stopped, even if we have to crash the process.
    """
    print("Starting network")
    network.start()
    e = None
    try:
        yield network
    except Exception as e:
        print("Caught exception", e)

    if e is not None: raise e


def thread_function(net, src, dst):
    global fileDownloaded
    print("Thread {}:{} starting".format(src, dst))

    while True:
        if len(fileDownloaded) == totalFiles:
            break

        fileSuffix = random.randint(1, totalFiles)
        while fileSuffix in fileDownloaded:
            fileSuffix = random.randint(1, totalFiles)
        fileDownloaded.append(fileSuffix)

        cmd = "wget 10.0.0.{}/DUMPS/file_{}.txt -O DUMPS/out_{}.txt".format(dst, fileSuffix, fileSuffix)
        print("Flow starts from 10.0.0." + str(src) + " to 10.0.0." + str(dst) + " of size: " + str(2*fileSuffix) + "MB" )
        out = net.hosts[src-1].cmd(cmd) 
        print("Sleeping for 1.25 sec for thread " + "10.0.0." + str(src) + " to 10.0.0." + str(dst))            
        time.sleep(1.25)
        print("Wake up: thread " + "10.0.0." + str(src) + " to 10.0.0." + str(dst)) 

    print("Thread {}:{} Finished".format(src, dst))


def startTCPDumps():
    currtime = time.strftime("%Y-%m-%d-%H-%M")
    folder = "logs/" + currtime
    try:
        os.mkdir(folder)
    except OSError:
        pass
    for p in range(4, 7):
        os.system("sudo tcpdump -i s1-eth{} -w " + folder + "/s1-eth{}.pcap >/dev/null 2>&1 &".format(p, p))

    for p in range(1, 4):
        os.system("sudo tcpdump -i s2-eth{} -w " + folder + "/s2-eth{}.pcap >/dev/null 2>&1 &".format(p, p))

    """ 
        To read the dumps: 
        $ tcpdump -r dump.pcap
    """

def createNetwork():
    try:
        topology = MyTopo()
        ip = '127.0.0.1'
        port = 6633 
        controllerInstance = RemoteController(
            'c0', 
            ip=ip,
            port=port,
            protocol='tcp',
        )

        while not controllerInstance.isListening(ip, port):
            time.sleep(1)

        print("*"*50)
        print("Connected to remote controller at %s:%d\n" % ( ip, port ))
        print("*"*50)

        net = Mininet(
            topo=topology, 
            controller=controllerInstance,
            link=TCLink,
            build=False,
            autoSetMacs = True,
            ipBase='10.0.0.0/8'
        )
        return net

    except Exception as e:
        error("Exception caught %s" %(str(e), ))
        return None


def deleteFlows():
    os.system("sudo ovs-ofctl del-flows s1")
    os.system("sudo ovs-ofctl del-flows s2")


def main():
    print("Creating DUMP files")
    createDUMPFiles()
    print("Clearing previous topology")
    os.system("sudo mn -c")
    print("Previous topology created")

    net = createNetwork()
    if not net:
        print("Unable to create network")
        sys.exit()


    with start_network(net) as network:
        print("Beginning experiment")

        # running HTTP SERVERS
        for i in range(4, 7):
            net.hosts[i-1].cmd("python -m ComplexHTTPServer 80 &") 
        print("HTTP SERVER Created")
        
        # start tcp dumps script
        print("TCP DUMPS script starts")
        startTCPDumps()

        # running 3 threads for wgets
        tick = time.time()
        threads = []
        for i in range(1, 4):
            th = threading.Thread(target=thread_function, args=(net, i, i+3))
            th.start()
            threads.append(th)
        print("WGETS IS RUNNING IN BACKGROUND")

        print("Waiting for threads to finish their work")
        for th in threads:
            th.join()

        print("*"*50)
        tock = time.time()
        print("\nTotal time to transfer the files: " + str(round(tock-tick, 3)) + "sec\n")

        print("**Deleting flows**")
        deleteFlows()

        print("**Stopping network**")
        network.stop()
        print("***Experiment completed***")


if __name__ == '__main__':
    main()