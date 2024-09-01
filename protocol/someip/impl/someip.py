import base64
from binascii import hexlify
from collections import namedtuple
from typing import Optional, Sequence, Union

import jsonargparse
from pydantic import Field, IPvAnyAddress

from clarity.common.models import SCAN_TRACE

from clarity.communicator.communication_layers.tcp.tcp import TCP_ComLayer
from clarity.communicator.communication_layers.udp.udp import (
    UDP_ComLayer,
)
from clarity.communicator.communicator_base import ComLayerBaseNew

from .someip_models import (
    SOMEIP_METHOD_INFO,
    SOMEIP_SERVICE_INFO,
    SOMEIP_TARGET,
    TEMP_LISTEN_PORT,
    SomeIpSdOptionFlags
)
from .someip_option_handling import SOMEIP_OPTION_HANDLING_MAPPING
import py_pcapplusplus as pypcap

# NamedTuples #
EventgrpWithTraceReponse = namedtuple("EventgrpWithTraceReponse", ["evtgrpid", "trace"])

RET_E_UNKNOWN_SERVICE = 0x02
RET_E_UNKNOWN_METHOD = 0x03

class SOMEIP_ComLayer(ComLayerBaseNew):
    hosts_to_skip: Optional[Sequence[IPvAnyAddress]] = Field(
        description="A list of hosts that the scan should skip. "
        "only the host part of the IPv6 address is taken into account."
    )
    prev_layer: Union[UDP_ComLayer, TCP_ComLayer]

    def get_info(self):
        return SOMEIP_TARGET(
            source_ip=self.prev_layer.source_ip,
            target_ip=self.prev_layer.target_ip,
            source_port=self.prev_layer.source_port,
            destination_port=self.prev_layer.destination_port,
        )

    ##### Factory #####
    def from_service_info(
        self,
        service_info: SOMEIP_SERVICE_INFO,
    ):
        """
        create a new someip comm layer instance,
        based on current instance and the found service.
        """
        # because replace_comlayer.. methods return a new instance, a variable
        # is needed in order to keep tabs of the newly created commlayer.
        new_someip_l = self
        new_ip_layer = new_someip_l.prev_layer.prev_layer

        # Check if endpoint address of service is different from current ip,
        # if it is - a new IP layer is also to be created.
        # Make sure to compare IPvAnyAddress types otherwise this will always be false.
        if (
            IPvAnyAddress(service_info.endpoint_addr)
            != new_ip_layer.target_ip
        ):
            # Copy params of current ip layer, but change target_ip
            new_ip_layer = new_ip_layer.model_copy(
                update={"target_ip": IPvAnyAddress(service_info.endpoint_addr)}
            )

            # This creates a new instance from the current one.
            new_someip_l = new_someip_l.replace_comlayer_by_type(new_ip_layer)

        # Transport layer will change for sure. depending on the response the service
        # is either a TCP or a UDP service with a different port.
        if service_info.port_type == pypcap.SomeIpSdProtocolType.SD_TCP:
            new_prev_layer = TCP_ComLayer(
                sport=TEMP_LISTEN_PORT, dport=service_info.port, prev_layer=new_ip_layer
            )
        elif service_info.port_type == pypcap.SomeIpSdProtocolType.SD_UDP:
            new_prev_layer = UDP_ComLayer(
                sport=TEMP_LISTEN_PORT, dport=service_info.port, prev_layer=new_ip_layer
            )
        else:
            raise Exception(
                f"invalid Layer 4 Proto in Someip Service Info: {service_info.port_type}"
            )

        # This creates a new instance from the current one.
        new_someip_l = new_someip_l.replace_comlayer_by_prev_idx(new_prev_layer, 0)

        return new_someip_l

    ##### Find Service Functions #####
    def _parse_options_for_offer_service(
        self, some_ip_sd_layer: pypcap.SomeIpSdLayer, service_idx: int, **kwargs
    ) -> dict[int, SOMEIP_SERVICE_INFO]:
        found_services: dict[int, SOMEIP_SERVICE_INFO] = {}

        entries = some_ip_sd_layer.get_entries()
        # get opt data
        opt_idx_1 = entries[service_idx].index_1
        opt_idx_2 = entries[service_idx].index_2
        opt_len_1 = entries[service_idx].n_opt_1
        opt_len_2 = entries[service_idx].n_opt_2

        option_ranges = [
            range(opt_idx_1, opt_idx_1 + opt_len_1),
            range(opt_idx_2, opt_idx_2 + opt_len_2),
        ]

        for opt_range in option_ranges:
            for i in opt_range:
                if option_handler := SOMEIP_OPTION_HANDLING_MAPPING.get(
                    some_ip_sd_layer.get_options()[i].type
                ):
                    someip_service_info = option_handler(some_ip_sd_layer, service_idx, i)
                    found_services.update(someip_service_info)

        return found_services

    def _parse_find_service_response(
        self, recv_data
    ) -> dict[int, SOMEIP_SERVICE_INFO]:
        found_services = {}

        some_ip_sd_layer: pypcap.SomeIpSdLayer = pypcap.SomeIpSdLayer.from_bytes(recv_data)  # Convert packet to SOME/IP SD
        if (
            not some_ip_sd_layer.message_type == pypcap.SomeIpMsgType.ERRORS
            and not some_ip_sd_layer.return_code == RET_E_UNKNOWN_SERVICE
        ):
            entries: list[pypcap.SomeIpSdEntry] = some_ip_sd_layer.get_entries()
            if len(entries) > 0 and len(some_ip_sd_layer.get_options()) > 0:
                for i, entry in enumerate(entries):
                    if entry.type != pypcap.SomeIpSdEntryType.OfferService:  # if not offer_service
                        # (this is what we are looking for.) continue.
                        continue

                    self.logger.info(f"Found service ID: {hex(entry.service_id)}")

                    found_services.update(self._parse_options_for_offer_service(some_ip_sd_layer, i))
            else:
                self.logger.error(
                    "Found service ID, but response message is a bit weird. check"
                    " debug log for more info. continuing to next service."
                )
                self.logger.debug(f"err in parsing the response: [{hexlify(bytes(some_ip_sd_layer))}]")

        return found_services

    def find_service(
        self,
        srv_id,
        recv_retry=1,
        recv_timeout=0.01,
        **kwargs,
    ) -> dict[int, SOMEIP_SERVICE_INFO]:
        trace = None
        should_trace = kwargs.get("should_trace")

        self.logger.info(f"Testing service ID: {hex(srv_id)}")

        someip_sd_layer = pypcap.SomeIpSdLayer(flags=SomeIpSdOptionFlags.Unicast)

        find_service_entry = pypcap.SomeIpSdEntry(entry_type=pypcap.SomeIpSdEntryType.FindService,
                                                  service_id=srv_id,
                                                  instance_id=0xFFFF,
                                                  major_version=0xFF,
                                                  ttl=0xFFFFFF,
                                                  minor_version=0xFFFFFFFF)
        someip_sd_layer.add_entry(find_service_entry)

        self.send(bytes(someip_sd_layer))

        # Read received data and convert it to SOME/IP packet
        for i in range(recv_retry):
            recv_data = self.recv(recv_timeout)

            if recv_data is not None:
                curr_found_services = self._parse_find_service_response(recv_data)

                # Add trace to found services
                if should_trace:
                    # initialize trace
                    trace = SCAN_TRACE(
                        request=base64.b64encode(bytes(someip_sd_layer)).decode("ascii"),
                        response=base64.b64encode(bytes(recv_data)).decode("ascii"),
                    )

                    for srv in curr_found_services.keys():
                        # every entry is of type SOMEIP_SERVICE_INFO,
                        # it has a "trace" field.
                        curr_found_services[srv].trace = trace

                return curr_found_services

        return {}

    ##### Eventgroup Subscribe Functions #####
    def _build_evtgrp_packet(
        self, service_id: int, service_info: SOMEIP_SERVICE_INFO, evtgrpid: int
    ) -> pypcap.SomeIpSdLayer:
        # Build base packet.
        someip_sd_layer = pypcap.SomeIpSdLayer(flags=SomeIpSdOptionFlags.Unicast)
        someip_sd_entry = pypcap.SomeIpSdEntry(entry_type=pypcap.SomeIpSdEntryType.SubscribeEventgroup,
                                               service_id=service_id,
                                               instance_id=service_info.inst_id,
                                               major_version=service_info.major_ver,
                                               ttl=service_info.ttl,
                                               counter=0,
                                               event_group_id=evtgrpid)
        index = someip_sd_layer.add_entry(someip_sd_entry)

        if self.prev_layer.prev_layer._is_ipv6:
            someip_sd_option = pypcap.SomeIpSdIPv6Option(option_type=pypcap.SomeIpSdIPv6OptionType.IPv6Endpoint,
                                                        ipv6_addr=str(self.prev_layer.prev_layer.source_ip),
                                                        port=TEMP_LISTEN_PORT,
                                                        protocol_type=service_info.port_type)
        else:
            someip_sd_option = pypcap.SomeIpSdIPv4Option(option_type=pypcap.SomeIpSdIPv4OptionType.IPv4Endpoint,
                                                        ipv4_addr=str(self.prev_layer.prev_layer.source_ip),
                                                        port=TEMP_LISTEN_PORT,
                                                        protocol_type=service_info.port_type)

        someip_sd_layer.add_option_to(index,
                                      someip_sd_option)

        return someip_sd_layer

    def subscribe_evtgrp_pre(
        self,
        service_info: SOMEIP_SERVICE_INFO,
        *args,
        **kwargs,
    ) -> "SOMEIP_ComLayer":
        # Create layer from service info.
        return self.from_service_info(service_info)

    def subscribe_evtgrp(
        self,
        service_id: int,
        service_info: SOMEIP_SERVICE_INFO,
        evtgrpid: int,
        recv_timeout: int = 0.01,
        *args,
        **kwargs,
    ) -> Optional[EventgrpWithTraceReponse]:
        """
        NOTE: before calling this function multiple times, one has to call subscribe_evtgrp_pre once,
              and pass along the create someip_l layer created by it,
              after its (someip_l) socket has been created, and 'connect' function was called on it.
        """
        trace = None
        should_trace = kwargs.get("should_trace")

        someip_sd_layer = self._build_evtgrp_packet(service_id, service_info, evtgrpid)

        # send evtgrp subscribe
        self.send(bytes(someip_sd_layer))

        # Read received data on sd socket and convert it to SOME/IP packet
        recv_data = self.recv(recv_timeout)
        if recv_data is not None:
            received_someip_sd_layer = pypcap.SomeIpSdLayer.from_bytes(recv_data)  # Convert packet to SOME/IP SD
            if received_someip_sd_layer and len(received_someip_sd_layer.get_entries()) and received_someip_sd_layer.get_entries()[0].ttl != 0:  # if ttl is 0 it means we got a NACK
                found_evtgrpid = received_someip_sd_layer.get_entries()[0].event_group_id

                # Add trace to found eventgroups if flag defined
                if should_trace:
                    # initialize trace
                    trace = SCAN_TRACE(
                        request=base64.b64encode(bytes(received_someip_sd_layer)).decode("ascii"),
                        response=base64.b64encode(bytes(recv_data)).decode("ascii"),
                    )

                self.logger.info(f"Found eventgroupID: {hex(found_evtgrpid)}")

                found_evtgrpid_with_trace = EventgrpWithTraceReponse(
                    evtgrpid=found_evtgrpid, trace=trace
                )

                return found_evtgrpid_with_trace

        return None

    ##### Method Invoke Functions #####
    def _build_method_packet(self, method_id: int, service_id: int, service_info: SOMEIP_SERVICE_INFO) -> pypcap.SomeIpLayer:
        return pypcap.SomeIpLayer(service_id=service_id,
                                  method_id=method_id,
                                  client_id=0x0000,
                                  session_id=0x0001,
                                  interface_version=service_info.major_ver,
                                  msg_type=pypcap.SomeIpMsgType.REQUEST)

    def method_invoke_pre(
        self,
        service_info: SOMEIP_SERVICE_INFO,
        *args,
        **kwargs,
    ) -> "SOMEIP_ComLayer":
        # Create layer from service info.
        return self.from_service_info(service_info)

    def method_invoke(
        self,
        service_id: int,
        service_info: SOMEIP_SERVICE_INFO,
        method_id: int,
        recv_timeout: int = 0.01,
        *args,
        **kwargs,
    ) -> Optional[dict[int, SOMEIP_METHOD_INFO]]:
        trace = None
        should_trace = kwargs.get("should_trace")

        someip_layer = self._build_method_packet(method_id, service_id, service_info)

        self.logger.debug(f"Testing method ID: {hex(method_id)}")

        self.send(bytes(someip_layer))

        # Read received data and convert it to SOME/IP packet
        recv_data = self.recv(recv_timeout)
        if recv_data is not None:
            ret_someip_layer:pypcap.SomeIpLayer = pypcap.SomeIpLayer.from_bytes(recv_data)
            if not ret_someip_layer:
                self.logger.error("SOME/IP parsing of received message is unclear.")
                return None

            if ret_someip_layer.return_code != RET_E_UNKNOWN_METHOD:
                # Add trace to found eventgroups if flag defined
                if should_trace:
                    # initialize trace
                    trace = SCAN_TRACE(
                        request=base64.b64encode(bytes(someip_layer)).decode("ascii"),
                        response=base64.b64encode(bytes(recv_data)).decode("ascii"),
                    )

                self.logger.info(f"Received something in method ID: {hex(method_id)}")

                found_method_info = SOMEIP_METHOD_INFO(trace=trace)

                return found_method_info

        return None


jsonargparse.typing.register_type(IPvAnyAddress)
