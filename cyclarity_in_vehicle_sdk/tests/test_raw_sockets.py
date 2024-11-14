import pytest
from cyclarity_in_vehicle_sdk.communication.ip.raw.raw_socket import Layer2RawSocket, Layer3RawSocket, IpVersion

def test_layer2_raw_socket():
    layer2_sock = Layer2RawSocket(if_name="eth0")
    layer2_sock.open()
    packet = layer2_sock.receive()
    layer2_sock.close()
    print(packet)

def test_layer3_raw_socket_ipv4():
    layer3_sock = Layer3RawSocket(if_name="eth0", ip_version=IpVersion.IPv4)
    layer3_sock.open()
    packet = layer3_sock.receive()
    layer3_sock.close()
    print(packet)

def test_layer3_raw_socket_ipv6():
    layer3_sock = Layer3RawSocket(if_name="eth0", ip_version=IpVersion.IPv6)
    layer3_sock.open()
    packet = layer3_sock.receive()
    layer3_sock.close()
    print(packet)

