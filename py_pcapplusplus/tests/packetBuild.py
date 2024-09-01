import py_pcapplusplus

packet = py_pcapplusplus.Packet()
eth_layer = py_pcapplusplus.EthLayer(src_mac_addr="00:15:5d:62:d8:0f", dst_mac_addr="00:15:5d:62:d8:0a") 
packet.add_layer(eth_layer)

ip_layer = py_pcapplusplus.IPv4Layer(src_addr="127.0.0.1", dst_addr="127.0.0.1") 
packet.add_layer(ip_layer)
print(packet)
someip_layer = py_pcapplusplus.SomeIpLayer(1,1,1,1,1,py_pcapplusplus.SomeIpMsgType.REQUEST_ACK, 1)
print(someip_layer)
someip_layer.method_id = 123
print(someip_layer)

someip_layer_bytes = bytes(someip_layer)

someip_layer_new: py_pcapplusplus.SomeIpLayer = py_pcapplusplus.SomeIpLayer.from_bytes(someip_layer_bytes)
if someip_layer_new:
    print(someip_layer_new)
else:
    print("cast from bytes failed")

someip_sd_layer = py_pcapplusplus.SomeIpSdLayer()
print(someip_sd_layer)

entry = py_pcapplusplus.SomeIpSdEntry(py_pcapplusplus.SomeIpSdEntryType.FindService, 1,2,3,4,5)
entry_index = someip_sd_layer.add_entry(entry)
print(someip_sd_layer)
option = py_pcapplusplus.SomeIpSdIPv4Option(py_pcapplusplus.SomeIpSdIPv4OptionType.IPv4Endpoint, "10.0.0.1", 1234, py_pcapplusplus.SomeIpSdProtocolType.SD_TCP)
someip_sd_layer.add_option_to(entry_index, option)
print(someip_sd_layer)

entries = someip_sd_layer.get_entries()
print(len(entries))

someip_sd_layer_bytes = bytes(someip_sd_layer)

someip_sd_layer_new: py_pcapplusplus.SomeIpSdLayer = py_pcapplusplus.SomeIpSdLayer.from_bytes(someip_sd_layer_bytes)
if someip_sd_layer_new:
    print(someip_sd_layer_new)
else:
    print("cast from bytes failed")