from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr,EthAddr
from pox.lib.packet.arp import arp,ethernet
import pox.lib.packet as pkt
from pox.lib.packet.ipv4 import ipv4
import random

log = core.getLogger()
d = {}
currentLink_left = 0
currentLink_right = 0


class ACN_PART_2C (object):
  def __init__ (self, connection):
    self.ips_to_interface = {"10.0.0.{}".format(i): i for i in range(1, 7)}
    self.ips = ["10.0.0.{}".format(i) for i in range(1, 7)] 
    self.macs = ["00:00:00:00:00:0{}".format(i) for i in range(1, 7)] 
    self.ips_to_macs = {"10.0.0.{}".format(i): '00:00:00:00:00:0{}'.format(i) for i in range(1, 7)}

    self.connection = connection
    connection.addListeners(self)

  #this function sends a packet to a particular port
  def send_packet (self, packet_in, out_port):
    msg = of.ofp_packet_out()
    msg.data = packet_in
    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)
    # Sending message to switch
    self.connection.send(msg)

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
    
  def flow_pusher(self, s_ip, d_ip, o_port, count):
    fm = of.ofp_flow_mod()
    fm.match.dl_type = 0x800
    fm.match.nw_src = s_ip 
    fm.match.nw_dst = d_ip
    fm.idle_timeout = 1
    fm.hard_timeout = of.OFP_FLOW_PERMANENT
    fm.priority = 1000
    if count == 1:
      fm.match.in_port = self.ips_to_interface[str(s_ip)]
    fm.actions.append(of.ofp_action_output(port = o_port))
    self.connection.send(fm)
    print("flow has been pushed")

  @staticmethod
  def get_min(min_cost):
    min_c = 10**9
    res = None
    for key, val in min_cost.items():
        avg_ = sum(val["time"])/5
        if avg_ < min_c:
            min_c = avg_
            res = val["port"]
    return res


  def my_function (self, packet, packet_in):
    global d
    global currentLink_left
    global currentLink_right


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
              arp_response = self.create_arp_response_packet(
                packet,
                EthAddr(self.ips_to_macs[self.ips[j]]),
                packet.src
              )
              self.send_packet(arp_response, self.ips_to_interface[self.ips[i]])
              break
          j+=1
        i+=1

    elif packet.type == pkt.ethernet.IP_TYPE and packet.payload.srcip in d:
      self.flow_pusher(
        packet.payload.srcip, 
        packet.payload.dstip, 
        self.ips_to_interface[str(packet.payload.dstip)], 
        2
      )
      self.flow_pusher(
        packet.payload.dstip, 
        packet.payload.srcip, 
        packet_in.in_port, 
        1
      )
      self.send_packet(
        packet, 
        self.ips_to_interface[str(packet.payload.dstip)]
      )
      del d[packet.payload.srcip]


    elif packet.type == pkt.ethernet.IP_TYPE:
        if packet_in.in_port == 1 or packet_in.in_port == 2 or packet_in.in_port == 3:
            temp = currentLink_left + 4
            currentLink_left = (currentLink_left + 1) % 3
        else:
            temp = currentLink_right + 1
            currentLink_right = (currentLink_right + 1) % 3
        print("Temp is {}".format(temp))
        self.Printer(temp)

        self.flow_pusher(packet.payload.srcip, packet.payload.dstip, temp, 1)
        self.flow_pusher(packet.payload.dstip, packet.payload.srcip, packet_in.in_port, 2)
        self.send_packet(packet, temp)
        d[packet.payload.srcip] = temp


  # Handles packet in messages from the switch.
  def _handle_PacketIn (self, event):
    packet = event.parsed 
    if not packet.parsed:
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