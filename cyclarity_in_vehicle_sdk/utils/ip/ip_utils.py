from ipaddress import IPv4Address, IPv6Address, ip_network
import random
from pydantic import IPvAnyAddress

IPV4_LEN_BITS = 32
IPV6_LEN_BITS = 128

def build_ip(base: IPvAnyAddress, network_prefix: int = 0, host_part: int = None) -> IPvAnyAddress | None:
    """Generate IP address within the host of the base IP, using provided host part or generating randomly if not provided

    Args:
        base (IPvAnyAddress): Base IP address
        network_prefix (int, optional): network part length of the base IP
        host_part (int, optional): Host part of the IP address  

    Returns:
        IPvAnyAddress | None: Generated IP address, None if conditions were not valid
    """
    if isinstance(base, IPv4Address):  
        if not (0 <= network_prefix < IPV4_LEN_BITS):  
            return None  
        network = ip_network((base, network_prefix), strict=False)  

        num_host_bits = IPV4_LEN_BITS - network_prefix  
        max_host_value = 2**num_host_bits - 1  
        if host_part is None:  
            host_part = random.randint(1, max_host_value - 1)  # Exclude network and broadcast  
        if not (0 <= host_part <= max_host_value):  
            return None  

        return IPv4Address(int(network.network_address) + host_part)  

    elif isinstance(base, IPv6Address):
        if not (0 <= network_prefix < IPV6_LEN_BITS):  
            return None  
        network = ip_network((base, network_prefix), strict=False)

        num_host_bits = IPV6_LEN_BITS - network_prefix  
        max_host_value = 2**num_host_bits - 1  
        if host_part is None:  
            host_part = random.randint(1, max_host_value - 1)  # Exclude network and broadcast equivalent  
        if not (0 <= host_part <= max_host_value):  
            return None  

        return IPv6Address(int(network.network_address) + host_part)  
    else:
        return None