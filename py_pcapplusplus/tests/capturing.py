import py_pcapplusplus

try:
    packets = py_pcapplusplus.sniff_eth('eth0', 5)
    print(f"received {len(packets)} packets")
    for index, packet in enumerate(packets, start=1):
        print(f"{index} - {packet}")
        b:bytes = bytes(packet)
        print(len(b))

except RuntimeError as ex:
    print(ex)
    
