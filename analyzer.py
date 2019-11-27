from mininet.net import Mininet
from mytopo import MyTopo
from mininet.node import Controller, RemoteController
from mininet.util import custom, pmonitor
from mininet.link import TCLink, Intf

from contextlib import contextmanager
import time
import random
import shutil
import os
from subprocess import Popen, PIPE, call, check_call
import logging
import threading

fileDownloaded = []
totalFiles = 12
tock = time.time()
tick = time.time()


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
    finally:
        # time.sleep(1000)
        print("Stopping network")
        # network.stop()
    if e is not None: raise e

def thread_function(net, src, dst):
    global fileDownloaded
    global tock
    global tick

    print("Thread {}:{} starting".format(src, dst))

    while True:
        if len(fileDownloaded) == totalFiles:
            break

        fileSuffix = random.randint(1, totalFiles)
        while fileSuffix in fileDownloaded:
            fileSuffix = random.randint(1, totalFiles)
        fileDownloaded.append(fileSuffix)

        cmd = "wget 10.0.0.{}/DUMPS/file_{}.txt -O DUMPS/out_{}.txt".format(dst, fileSuffix, fileSuffix)
        print("Flow of 10.0.0." + str(src) + " to 10.0.0." + str(dst) + " of size: " + str(2*fileSuffix) + "MB" )
        out = net.hosts[src-1].cmd(cmd) 
        print("Sleeping for 1.25 sec for thread " + "10.0.0." + str(src) + " to 10.0.0." + str(dst))            
        time.sleep(1.25)
        print("Wake up: thread " + "10.0.0." + str(src) + " to 10.0.0." + str(dst)) 

    print("Thread {}:{} Finished".format(src, dst))

    if time.time() > tock:
        tock = time.time()
    
    print(tock-tick)


def main():
    global tick
    createDUMPFiles()
    check_call("sudo mn -c", shell=True)

    topology = MyTopo()
    controllerInstance = RemoteController(
        'c0', ip='127.0.0.1', port=6633,
        protocol='tcp',
    )
    net = Mininet(
        topo=topology, 
        controller=controllerInstance,
        link=TCLink,
        build=False,
        autoSetMacs = True,
        ipBase='10.0.0.0/8'

    )
    tick = time.time()
    with start_network(net) as network:
        print("Beginning experiment")

        for i in range(4, 7):
            net.hosts[i-1].cmd("python -m ComplexHTTPServer 80 &") 
        print("HTTP SERVER Created")
        
        for i in range(1, 4):
            th = threading.Thread(target=thread_function, args=(net, i, i+3))
            th.start()

        print("WGETS IS RUNNING IN BACKGROUND")

        print("Experiment complete")

if __name__ == '__main__':
    main()