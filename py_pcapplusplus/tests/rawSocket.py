import py_pcapplusplus
from doipclient import constants, messages, DoIPClient
from doipclient.client import Parser


def vehicle_identification_req() -> messages.VehicleIdentificationRequest:
    message = messages.VehicleIdentificationRequest()
    return create_doip_message(message)


def req_entity_status() -> messages.EntityStatusResponse:
    message = messages.DoipEntityStatusRequest()
    return create_doip_message(message)

def create_doip_message(message: messages.DoIPMessage, ecu_ip_address="127.0.0.1", protocol_version: int = 0x02):
        payload_data = message.pack()
        payload_type = messages.payload_message_to_type[type(message)]
        data_bytes = DoIPClient._pack_doip(protocol_version, payload_type, payload_data)
        return data_bytes

packet = py_pcapplusplus.Packet()
eth_layer = py_pcapplusplus.EthLayer(src_mac_addr="00:15:5d:61:20:87", dst_mac_addr="00:15:5d:0c:e3:fc") 
packet.add_layer(eth_layer)
ip_layer = py_pcapplusplus.IPv4Layer(src_addr="172.17.86.199", dst_addr="169.254.117.238") 
packet.add_layer(ip_layer)
udp_layer = py_pcapplusplus.UdpLayer(src_port=13400, dst_port=13400) 
packet.add_layer(udp_layer)
doip_layer = py_pcapplusplus.PayloadLayer(vehicle_identification_req()) 
# doip_layer = py_pcapplusplus.PayloadLayer(bytes.fromhex("02fd000100000000"))
packet.add_layer(doip_layer)

print(packet)

raw_socket = py_pcapplusplus.RawSocket(if_name="lo")
sniffed_packets = raw_socket.sniff(3)

for packet in sniffed_packets[:3]:
     print(packet)