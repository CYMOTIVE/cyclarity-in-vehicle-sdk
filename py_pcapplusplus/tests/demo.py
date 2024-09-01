import py_pcapplusplus
import itertools
import os

def batched(iterable, n):
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch

reader = py_pcapplusplus.Reader(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'filtered.ipv6dns_packets_1_10000.pcap'))

for count, chunk in enumerate(batched(reader, 1)):
    if count == 1:
        break
    chunk_packets = []
    for p in chunk:
        frame = p.get_layer(py_pcapplusplus.LayerType.IPv4Layer)
        if frame:
            frame.src_ip = "10.0.0.8"
            frame.clear_chksum()
        frame = p.get_layer(py_pcapplusplus.LayerType.TcpLayer)
        if frame:
            frame.clear_chksum()
        chunk_packets.append(p)

    for p in chunk_packets:
        print(p)
    packets_sent = py_pcapplusplus.send_eth_packets('eth0', chunk_packets, "10.0.0.1")
    print(f"Packets sent: {len(chunk_packets)}/{str(packets_sent)}")
