from .someip_models import SOMEIP_SERVICE_INFO
import py_pcapplusplus as pypcap

def _handle_IPv4_IPv6_endpoint_option(
    some_ip_sd_layer: pypcap.SomeIpSdLayer, srvc_idx: int, opt_idx: int, **kwargs
) -> dict[int, SOMEIP_SERVICE_INFO]:
    
    # get data regarding service
    entries = some_ip_sd_layer.get_entries()
    found_srv_id = entries[srvc_idx].service_id
    found_inst_id = entries[srvc_idx].instance_id
    found_major_ver = entries[srvc_idx].major_version
    found_minor_ver = entries[srvc_idx].minor_version
    found_ttl = entries[srvc_idx].ttl

    # get data regarding IPv6 Option
    options = some_ip_sd_layer.get_options()
    if options[opt_idx].type == pypcap.SomeIpSdOptionType.IPv4Endpoint:
        option: pypcap.SomeIpSdIPv4Option = options[opt_idx]
    else:
        option: pypcap.SomeIpSdIPv6Option = options[opt_idx]

    endpoint_addr = option.addr
    found_port = option.port
    found_port_type = option.protocol_type

    return {
        found_srv_id: SOMEIP_SERVICE_INFO(
            inst_id=found_inst_id,
            major_ver=found_major_ver,
            minor_ver=found_minor_ver,
            ttl=found_ttl,
            endpoint_addr=endpoint_addr,
            port=found_port,
            port_type=found_port_type,
        )
    }

SOMEIP_OPTION_HANDLING_MAPPING = {
    pypcap.SomeIpSdOptionType.IPv4Endpoint: _handle_IPv4_IPv6_endpoint_option,
    pypcap.SomeIpSdOptionType.IPv6Endpoint: _handle_IPv4_IPv6_endpoint_option
}
