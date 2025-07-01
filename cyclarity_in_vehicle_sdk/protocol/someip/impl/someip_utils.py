import itertools
from typing import Union
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpVersion
from cyclarity_in_vehicle_sdk.communication.ip.tcp.tcp import TcpCommunicator
from cyclarity_in_vehicle_sdk.communication.ip.udp.multicast import MulticastCommunicator
from cyclarity_in_vehicle_sdk.communication.ip.udp.udp import UdpCommunicator
from cyclarity_in_vehicle_sdk.protocol.someip.models.someip_models import (
    SOMEIP_ENDPOINT_OPTION,
    SOMEIP_EVTGROUP_INFO,
    SOMEIP_METHOD_INFO,
    SOMEIP_SERVICE_INFO,
    Layer4ProtocolType,
    SomeIpSdOptionFlags,
    SomeIpReturnCode,
    )
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
import py_pcapplusplus
from pydantic import IPvAnyAddress


class SomeipUtils(ParsableModel):
    def find_service(
        self,
        socket: UdpCommunicator | MulticastCommunicator,
        service_id: int,
        recv_retry: int = 1,
        recv_timeout: float = 0.01,
    ) -> list[SOMEIP_SERVICE_INFO]:
        """	SOME/IP Find Service

        Args:
            socket (UdpCommunicator | MulticastCommunicator): 
                A SOME/IP SD socket (UDP) for sending FindService queries
                A SOME/IP SD socket for receiving offered services response (UDP) from broadcast (Multicast)
            service_id (int): The Service ID to try query
            recv_retry (int): Retries for receiving data from the SD socket. defaults to 1.
            recv_timeout (float): Timeout in seconds for the read operation. defaults to 0.01

        Returns:
            list[SOMEIP_SERVICE_INFO] list of found services
        """
        found_services: list[SOMEIP_SERVICE_INFO] = []
        if isinstance(socket, UdpCommunicator):
            someip_sd_layer = py_pcapplusplus.SomeIpSdLayer(flags=SomeIpSdOptionFlags.Unicast, 
                                                            msg_type=py_pcapplusplus.SomeIpMsgType.REQUEST)

            find_service_entry = py_pcapplusplus.SomeIpSdEntry(
                                                    entry_type=py_pcapplusplus.SomeIpSdEntryType.FindService,
                                                    service_id=service_id,
                                                    instance_id=0xFFFF,
                                                    major_version=0xFF,
                                                    ttl=0xFFFFFF,
                                                    minor_version=0xFFFFFFFF)
            someip_sd_layer.add_entry(find_service_entry)

            socket.send(bytes(someip_sd_layer))

        # Read received data and convert it to SOME/IP packet
        for _ in range(recv_retry):
            recv_data = socket.recv(recv_timeout)

            if recv_data is not None:
                self._parse_find_service_response(recv_data, found_services)

        return found_services

    def _parse_find_service_response(
        self, 
        recv_data: bytes,
        found_services: list[SOMEIP_SERVICE_INFO]
    ):
        """Helper internal method for parsing SOME/IP SD layer into offered services

        Args:
            recv_data (bytes): Raw data for the SOME/IP SD layer
            found_services (list[SOMEIP_SERVICE_INFO]): list of services to append into the parsed info
        """
        some_ip_sd_layer = py_pcapplusplus.SomeIpSdLayer.from_bytes(recv_data)  # Convert packet to SOME/IP SD
        if (some_ip_sd_layer
            and not some_ip_sd_layer.message_type == py_pcapplusplus.SomeIpMsgType.ERRORS
            and not some_ip_sd_layer.return_code == SomeIpReturnCode.E_UNKNOWN_SERVICE
        ):
            entries = some_ip_sd_layer.get_entries()
            options = some_ip_sd_layer.get_options()
            if len(entries) > 0 and len(options) > 0:
                for entry in entries:
                    if entry.type != py_pcapplusplus.SomeIpSdEntryType.OfferService:  
                        # if not offer_service (this is what we are looking for.) continue.
                        continue

                    self.logger.info(f"Found service ID: {hex(entry.service_id)}")

                    service_info = SOMEIP_SERVICE_INFO(
                        service_id=entry.service_id,
                        instance_id=entry.instance_id,
                        major_ver=entry.major_version,
                        minor_ver=entry.minor_version,
                        ttl=entry.ttl,
                    )

                    self._parse_options_for_offer_service(entry, options, service_info)

                    found_services.append(service_info)
            else:
                self.logger.error(
                    "Found service ID, but response message is a bit weird. check"
                    " debug log for more info. continuing to next service."
                )
                self.logger.debug(f"error in parsing the response: [{recv_data.hex()}]")
    
    def _parse_options_for_offer_service(
        self, 
        sd_entry: py_pcapplusplus.SomeIpSdEntry, 
        sd_options: list[py_pcapplusplus.SomeIpSdOption],
        service_info: SOMEIP_SERVICE_INFO
    ):
        """	Helper internal method for parsing options for endpoints information

        Args:
            sd_entry (py_pcapplusplus.SomeIpSdEntry): the parsed SOME/IP SD entry
            sd_options (list[py_pcapplusplus.SomeIpSdOption]): the entire options from the SOME/IP SD layer
            service_info (SOMEIP_SERVICE_INFO): service info object to append the discovered endpoints into 
            
        """
        combined_sorted_options_idx = sorted(
            itertools.chain(range(sd_entry.index_1, sd_entry.index_1 + sd_entry.n_opt_1),
                            range(sd_entry.index_2, sd_entry.index_2 + sd_entry.n_opt_2))
        )

        for opt_idx in combined_sorted_options_idx:
            
            if opt_idx > len(sd_options):
                self.logger.warning("SD entry pointing to a nonexisting option(s)")
                break
            
            if sd_options[opt_idx].type in [py_pcapplusplus.SomeIpSdOptionType.IPv4Endpoint,
                                            py_pcapplusplus.SomeIpSdOptionType.IPv6Endpoint]:
                service_info.endpoints.append(
                    SOMEIP_ENDPOINT_OPTION(
                        endpoint_addr = sd_options[opt_idx].addr,
                        port = sd_options[opt_idx].port,
                        port_type = (Layer4ProtocolType.TCP 
                                     if sd_options[opt_idx].protocol_type == py_pcapplusplus.SomeIpSdProtocolType.SD_TCP 
                                     else Layer4ProtocolType.UDP
                                     )

                ))

    def subscribe_evtgrp(
        self,
        sd_socket: UdpCommunicator,
        ep_socket: Union[UdpCommunicator, TcpCommunicator],
        service_info: SOMEIP_SERVICE_INFO,
        evtgrpid: int,
        transport_protocol: Layer4ProtocolType,
        recv_timeout: int = 0.01,
    ) -> SOMEIP_EVTGROUP_INFO | None:
        """	Subscribing to an eventgroup and fetch dome initial data

        Args:
            sd_socket (UdpCommunicator): A SOME/IP SD socket (UDP) for sending FindService queries
            ep_socket (Union[UdpCommunicator, TcpCommunicator]): the end point communicator for receiving the eventgroup data
            service_info (SOMEIP_SERVICE_INFO): information regarding the service in which the event group is located
            evtgrpid (int): the event group ID
            transport_protocol (Layer4ProtocolType): the layer 4 protocol type UDP/TCP
            recv_timeout (float): Timeout in seconds for the read operation. defaults to 0.01

        Returns:
            SOMEIP_EVTGROUP_INFO if found. None otherwise
        """
        found_evtgrpid = None
        someip_sd_layer = self._build_evtgrp_layer(
            service_info,
            evtgrpid,
            transport_protocol,
            ep_socket.source_port,
            ep_socket.source_ip,
            )

        # send evtgrp subscribe
        sd_socket.send(bytes(someip_sd_layer))

        # Read received data on sd socket and convert it to SOME/IP packet
        recv_data = sd_socket.recv(recv_timeout)
        if recv_data is not None:
            received_someip_sd_layer = py_pcapplusplus.SomeIpSdLayer.from_bytes(recv_data)  # Convert packet to SOME/IP SD
            if (received_someip_sd_layer 
                and len(received_someip_sd_layer.get_entries()) 
                and received_someip_sd_layer.get_entries()[0].ttl != 0 # if ttl is 0 it means we got a NACK
                ):
                found_evtgrpid = received_someip_sd_layer.get_entries()[0].event_group_id
                self.logger.info(f"Found eventgroup ID: {hex(found_evtgrpid)}")

                # found evtgrp, probably the server also sent
                # some initial data with it - try to receive it.
                initial_data = ep_socket.recv(recv_timeout=recv_timeout)
                found_evtgrpid = SOMEIP_EVTGROUP_INFO(
                    eventgroup_id=found_evtgrpid,
                    initial_data=initial_data,
                )

        return found_evtgrpid

    def _build_evtgrp_layer(
        self,
        service_info: SOMEIP_SERVICE_INFO,
        evtgrpid: int,
        transport_protocol: Layer4ProtocolType,
        source_port: int,
        source_ip: IPvAnyAddress,
    ) -> py_pcapplusplus.SomeIpSdLayer:
        """	Helper internal method for creating the SOME/IP SD subscribe eventgroup layer

        Args:
            service_info (SOMEIP_SERVICE_INFO): information regarding the service in which the event group is located
            evtgrpid (int): the event group ID
            transport_protocol (Layer4ProtocolType): the layer 4 protocol type UDP/TCP
            source_port (int): the source port to configure
            source_ip (IPvAnyAddress): the source IP to configure.

        Returns:
            SessionControlResultData
        """
        # Build base packet.
        someip_sd_layer = py_pcapplusplus.SomeIpSdLayer(
            flags=SomeIpSdOptionFlags.Unicast
            )
        someip_sd_entry = py_pcapplusplus.SomeIpSdEntry(
            entry_type=py_pcapplusplus.SomeIpSdEntryType.SubscribeEventgroup,
            service_id=service_info.service_id,
            instance_id=service_info.instance_id,
            major_version=service_info.major_ver,
            ttl=service_info.ttl,
            counter=0,
            event_group_id=evtgrpid
            )
        index = someip_sd_layer.add_entry(someip_sd_entry)
        protocol_type = (py_pcapplusplus.SomeIpSdProtocolType.SD_UDP
                         if transport_protocol == Layer4ProtocolType.UDP
                         else py_pcapplusplus.SomeIpSdProtocolType.SD_TCP)

        if source_ip.version == 6:
            someip_sd_option = py_pcapplusplus.SomeIpSdIPv6Option(
                option_type=py_pcapplusplus.SomeIpSdIPv6OptionType.IPv6Endpoint,
                ipv6_addr=str(source_ip),
                port=source_port,
                protocol_type=protocol_type
                )
        else:
            someip_sd_option = py_pcapplusplus.SomeIpSdIPv4Option(
                option_type=py_pcapplusplus.SomeIpSdIPv4OptionType.IPv4Endpoint,
                ipv4_addr=str(source_ip),
                port=source_port,
                protocol_type=protocol_type
                )

        someip_sd_layer.add_option_to(index,
                                      someip_sd_option)

        return someip_sd_layer
    
    def method_invoke(
        self,
        socket: Union[TcpCommunicator, UdpCommunicator],
        service_info: SOMEIP_SERVICE_INFO,
        method_id: int,
        recv_timeout: int = 0.01,
    ) -> SOMEIP_METHOD_INFO | None:
        """	Invoke SOME/IP Method

        Args:
            socket (Union[UdpCommunicator, TcpCommunicator]): the end point communicator for method request/response
            service_info (SOMEIP_SERVICE_INFO): information regarding the service in which the method is located
            method_id (int): The Method ID
            recv_timeout (float): Timeout in seconds for the read operation. defaults to 0.01

        Returns:
            SessionControlResultData
        """
        found_method_info = None
        someip_layer = py_pcapplusplus.SomeIpLayer(
            service_id=service_info.service_id,
            method_id=method_id,
            client_id=0x0000,
            session_id=0x0001,
            interface_version=service_info.major_ver,
            msg_type=py_pcapplusplus.SomeIpMsgType.REQUEST
            )

        socket.send(bytes(someip_layer))

        # Read received data and convert it to SOME/IP packet
        recv_data = socket.recv(recv_timeout)
        if recv_data is not None:
            ret_someip_layer = py_pcapplusplus.SomeIpLayer.from_bytes(recv_data)
            if (ret_someip_layer
                and ret_someip_layer.return_code != SomeIpReturnCode.E_UNKNOWN_METHOD
                ):
                self.logger.info(f"Received something in method ID: {hex(method_id)}")

                found_method_info = SOMEIP_METHOD_INFO(
                    method_id=method_id,
                    return_code=ret_someip_layer.return_code,
                    payload=ret_someip_layer.payload
                )

        return found_method_info
