from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr,EthAddr
from pox.lib.packet.arp import arp,ethernet
import pox.lib.packet as pkt
from pox.lib.packet.ipv4 import ipv4
import base64
import random
import time

log = core.getLogger()
mapper = {}
outFile = open("pox/misc/logs/icmp_out-" + time.strftime("%H-%M") + ".txt", "w")

count = 0
totalICMPPackets = 3
d = {}
def initializeMapper(mapper):
  mapper[("10.0.0.11","10.0.0.12")] = {
    "port": 0,
    "time": [],
    "count": 0
  }
  mapper[("10.0.0.13","10.0.0.14")] = {
    "port": 0,
    "time": [],
    "count": 0

  }
  mapper[("10.0.0.15","10.0.0.16")] = {
    "port": 0,
    "time": [],
    "count": 0
  }

initializeMapper(mapper)

class ACN_PART_2C (object):
  def __init__ (self, connection):

    self.connection = connection
    connection.addListeners(self)
    self.my_packet = 0
    self.my_packet_in = 0
    self.ips_to_interface = {"10.0.0.{}".format(i): i for i in range(1, 7)}
    self.ips_to_macs = {"10.0.0.{}".format(i): '00:00:00:00:00:0{}'.format(i) for i in range(1, 7)}

    self.ips = ["10.0.0.{}".format(i) for i in range(1, 7)] 
    self.macs = ["00:00:00:00:00:0{}".format(i) for i in range(1, 7)] 

  #this function sends a packet to a particular port
  def send_packet (self, packet_in, out_port):
    msg = of.ofp_packet_out()
    msg.data = packet_in
    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)
    # Sending message to switch
    self.connection.send(msg)

  #function to create arp response packet
  def create_icmp_custom_packet(self,src_in,dest_in,packet_type):
    #creating icmp packet
    icmp_packet=pkt.icmp()
    icmp_packet.type = packet_type

    # tick = str(round(time.time()%10**3, 9))
    tick = str(round(time.time(), 9))
    icmp_packet.payload =  base64.b64encode(tick)

    #creating ip packet
    ip_packet = pkt.ipv4()
    ip_packet.protocol=ip_packet.ICMP_PROTOCOL
    ip_packet.srcip=IPAddr("10.0.0.{}".format(src_in))
    ip_packet.dstip=IPAddr("10.0.0.{}".format(dest_in))
    ip_packet.payload=icmp_packet
    
    #Create Ethernet Payload
    ether= pkt.ethernet()
    ether.src=EthAddr("00:00:00:00:00:{}".format(src_in))
    ether.dst=EthAddr("00:00:00:00:00:{}".format(dest_in))
    ether.type=ethernet.IP_TYPE
    ether.payload=ip_packet
    return ether

  def create_arp_response_packet(self,packet,src_mac,dst_mac):
    arp_reply = arp()
    arp_reply.hwsrc =src_mac
    arp_reply.hwdst = dst_mac
    arp_reply.opcode = arp.REPLY
    arp_reply.protosrc = packet.payload.protodst
    arp_reply.protodst = packet.payload.protosrc
    ether = ethernet()
    ether.type = ethernet.ARP_TYPE
    ether.dst = dst_mac
    ether.src = src_mac
    ether.payload = arp_reply
    return ether
 
  def Printer(self,temp):
    if temp == 4 or temp == 1:
      print("Link 1 is selected")
    elif temp == 5 or temp == 2:
      print("Link 2 is selected")
    elif temp == 6 or temp == 3:
      print("Link 3 is selected")
    
  def flow_pusher(self,s_ip,d_ip,o_port,count):
    fm = of.ofp_flow_mod()
    fm.match.dl_type = 0x800
    fm.match.nw_src = s_ip 
    fm.match.nw_dst = d_ip
    fm.idle_timeout = 1
    fm.hard_timeout = of.OFP_FLOW_PERMANENT
    # h_sec = random.randint(10, 50)
    # fm.hard_timeout = h_sec
    fm.priority = 1000
    if count == 1:
      fm.match.in_port = self.ips_to_interface[str(s_ip)]
    fm.actions.append(of.ofp_action_output(port = o_port))
    self.connection.send(fm)

  @staticmethod
  def get_min(min_cost):
    min_c = 10**9
    res = None
    for key, val in min_cost.items():
        avg_ = sum(val["time"])/totalICMPPackets
        if avg_ < min_c:
            min_c = avg_
            res = val["port"]
    return res

  def my_function (self, packet, packet_in):
    global mapper
    global count
    global outFile
    global d
    if packet.type == packet.ARP_TYPE:
      length = len(self.ips)
      i = 0
      while i < length:
        j = 0
        while j < length:
          if packet.payload.opcode == arp.REQUEST and packet.payload.protosrc == IPAddr(self.ips[i]):
            if self.ips[i] == self.ips[j]:
              j+=1
              continue
            if packet.payload.protodst == IPAddr(self.ips[j]):
              arp_response = self.create_arp_response_packet(packet,EthAddr(self.ips_to_macs[self.ips[j]]),packet.src)
              self.send_packet(arp_response, self.ips_to_interface[self.ips[i]])
              break
          j+=1
        i+=1
    
    elif packet.type == pkt.ethernet.IP_TYPE  and packet.payload.srcip == IPAddr('10.0.0.11') and packet.payload.dstip == IPAddr('10.0.0.12'):
        packet.payload.srcip = IPAddr("10.0.0.12")
        packet.payload.dstip = IPAddr("10.0.0.11")
        packet.payload.type = pkt.TYPE_ECHO_REPLY
        self.send_packet(packet, packet_in.in_port)

    elif packet.type == pkt.ethernet.IP_TYPE  and packet.payload.srcip == IPAddr('10.0.0.13') and packet.payload.dstip == IPAddr('10.0.0.14'):
        packet.payload.srcip = IPAddr("10.0.0.14")
        packet.payload.dstip = IPAddr("10.0.0.13")
        packet.payload.type = pkt.TYPE_ECHO_REPLY
        self.send_packet(packet, packet_in.in_port)

    elif packet.type == pkt.ethernet.IP_TYPE  and packet.payload.srcip == IPAddr('10.0.0.15') and packet.payload.dstip == IPAddr('10.0.0.16'):
        packet.payload.srcip = IPAddr("10.0.0.16")
        packet.payload.dstip = IPAddr("10.0.0.15")
        packet.payload.type = pkt.TYPE_ECHO_REPLY
        self.send_packet(packet, packet_in.in_port)

    elif packet.type == pkt.ethernet.IP_TYPE and packet.payload.srcip in [IPAddr('10.0.0.1{}'.format(i)) for i in range(2, 7, 2)] and packet.payload.dstip in [IPAddr('10.0.0.1{}'.format(i)) for i in range(1, 7, 2)]:
        payload_temp = packet.payload.payload.payload.raw
        tick = float(base64.b64decode(str(payload_temp)))
        # tock = round(time.time()%10**3, 9)
        tock = round(time.time(), 9)
        if (str(packet.payload.dstip), str(packet.payload.srcip)) in mapper.keys():
          mapper[(str(packet.payload.dstip), str(packet.payload.srcip))]["time"].append(tock-tick)
          mapper[(str(packet.payload.dstip), str(packet.payload.srcip))]["count"] += 1
        else:
          mapper[(str(packet.payload.dstip), str(packet.payload.srcip))] = {
            "time": [tock-tick,],
            "count": 1,
            "port": 4
          }

        count = count+1
        if count == totalICMPPackets*3:
            for key, val in mapper.items():
              outFile.write(str(key) + "\n")
              avg = 0
              total_packs = len(val["time"])
              if total_packs > 0:
                for i in range(total_packs):
                  avg += val["time"][i]
                outFile.write("Average time: " + str(avg/total_packs) + "\n")

            count = 0
            temp = self.get_min(mapper)
            outFile.write("Link selected: " + str(temp))
            outFile.write("\n" + "-"*10 + "\n")

            d[self.my_packet.payload.srcip] = temp
            self.Printer(temp)
            self.flow_pusher(self.my_packet.payload.srcip,self.my_packet.payload.dstip,temp,1)
            self.flow_pusher(self.my_packet.payload.dstip,self.my_packet.payload.srcip,self.ips_to_interface[str(self.my_packet.payload.srcip)],2)
            self.send_packet(self.my_packet,temp)
            initializeMapper(mapper)
            

    elif packet.type == pkt.ethernet.IP_TYPE and packet.payload.srcip in d:
        self.flow_pusher(packet.payload.srcip,packet.payload.dstip,self.ips_to_interface[str(packet.payload.dstip)],2)
        self.flow_pusher(packet.payload.dstip,packet.payload.srcip,packet_in.in_port,2)
        self.send_packet(packet,self.ips_to_interface[str(packet.payload.dstip)])
        del d[packet.payload.srcip]

    elif packet.type == pkt.ethernet.IP_TYPE:
      t = 1
      if packet_in.in_port == 1 or packet_in.in_port == 2 or packet_in.in_port == 3:
        t = 4
      self.my_packet = packet
      self.my_packet_in = packet_in
      mapper[("10.0.0.11","10.0.0.12")]["port"] = t
      mapper[("10.0.0.13","10.0.0.14")]["port"] = t+1
      mapper[("10.0.0.15","10.0.0.16")]["port"] = t+2

      k = 0
      while k < totalICMPPackets:
        icmp_packet = self.create_icmp_custom_packet(11,12,pkt.TYPE_ECHO_REQUEST)
        self.send_packet(icmp_packet, t)

        icmp_packet = self.create_icmp_custom_packet(13,14,pkt.TYPE_ECHO_REQUEST)
        self.send_packet(icmp_packet, t+1)

        icmp_packet = self.create_icmp_custom_packet(15,16,pkt.TYPE_ECHO_REQUEST)
        self.send_packet(icmp_packet, t+2)
        k+=1

  # Handles packet in messages from the switch.
  def _handle_PacketIn (self, event):
    packet = event.parsed 
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return
    packet_in = event.ofp 
    self.my_function(packet, packet_in)


def launch ():
  """
  Starts the component

  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    ACN_PART_2C(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
