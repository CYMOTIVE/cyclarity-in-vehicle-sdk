from enum import IntEnum
from functools import partial
import logging
import time
from typing import Optional, Type, TypeAlias
from doipclient import constants, messages, DoIPClient
from doipclient.client import Parser
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel
from pydantic import IPvAnyAddress

from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorBase
from cyclarity_in_vehicle_sdk.communication.ip.raw.raw_socket import Layer3RawSocket
from cyclarity_in_vehicle_sdk.communication.ip.tcp.tcp import TcpCommunicator

from py_pcapplusplus import IPv4Layer, IPv6Layer, PayloadLayer, Packet, TcpLayer, UdpLayer, LayerType

DOIP_PORT = 13400

class DoipProtocolVersion(IntEnum):
    DoIP_13400_2010 = 0x01
    DoIP_13400_2012 = 0x02
    DoIP_13400_2019 = 0x03

# type aliases
VehicleIdentificationResponse: TypeAlias = messages.VehicleIdentificationResponse
RoutingActivationResponse: TypeAlias = messages.RoutingActivationResponse
EntityStatusResponse: TypeAlias = messages.EntityStatusResponse
ActivationType: TypeAlias = messages.RoutingActivationRequest.ActivationType
DoIPMessage: TypeAlias = messages.DoIPMessage

class DoipUtils(ParsableModel):
    raw_socket: Layer3RawSocket
    _tcp_communicators_cache: dict[str, TcpCommunicator] = {}

    def setup(self) -> bool:
        """Opens the socket for communicating with the target

        Returns:
            bool: True if succeeded False otherwise
        """
        if not self.raw_socket.open():
            self.logger.error("Failed opening raw socket")
            return False
        
        return True

    def teardown(self) -> bool:
        """Closes communications with the target

        Returns:
            bool: True if succeeded False otherwise
        """
        self.raw_socket.close()
        for tcp_con in self._tcp_communicators_cache.values():
            tcp_con.close()
        return True
    
    def initiate_vehicle_identity_req(self, 
                                      source_address: IPvAnyAddress, 
                                      source_port: int, 
                                      target_address: IPvAnyAddress, 
                                      protocol_version: DoipProtocolVersion = DoipProtocolVersion.DoIP_13400_2012, 
                                      eid: bytes = None, 
                                      vin: str = None) -> VehicleIdentificationResponse:
        """Initiate Vehicle identification request

        Args:
            source_address (IPvAnyAddress): source IP address for the request
            source_port (int): source port for the request
            target_address (IPvAnyAddress): target IP address
            protocol_version (DoipProtocolVersion, optional): the Doip Protocol Version. Defaults to DoipProtocolVersion.DoIP_13400_2012.
            eid (bytes, optional): eid. Defaults to None.
            vin (str, optional): vin. Defaults to None.

        Returns:
            VehicleIdentificationResponse: if got a response, None otherwise
        """
        if eid:
            message = messages.VehicleIdentificationRequestWithEID(eid)
        elif vin:
            message = messages.VehicleIdentificationRequestWithVIN(vin)
        else:
            message = messages.VehicleIdentificationRequest()

        is_answer_cb = partial(DoipUtils._is_answer, 
                               expected_source_port=source_port, 
                               l4_type=LayerType.UdpLayer, 
                               expected_resp_type=messages.VehicleIdentificationResponse)

        doip_layer_data = self._pack_doip_message(message, protocol_version)
        packet = Packet()
        if source_address.version == 4:
            ip_layer = IPv4Layer(src_addr=str(source_address), dst_addr=str(target_address))
        else:
            ip_layer = IPv6Layer(src_addr=str(source_address), dst_addr=str(target_address))
        packet.add_layer(ip_layer)
        udp_layer = UdpLayer(src_port=source_port, dst_port=DOIP_PORT)
        packet.add_layer(udp_layer)
        doip_layer = PayloadLayer(doip_layer_data)
        packet.add_layer(doip_layer)
        resp_packet = self.raw_socket.send_receive_packet(packet, is_answer_cb, constants.A_PROCESSING_TIME)
        if resp_packet:
            parser = Parser()
            parser.reset()
            result = parser.read_message(bytes(resp_packet.get_layer(LayerType.PayloadLayer)))
            if type(result) is messages.VehicleIdentificationResponse:
                return result
            elif result:
                self.logger.warning(
                    f"Received unexpected DoIP message type {type(result)}. Ignoring"
                )
        return None

    def initiate_routing_activation_req(self, 
                                        source_address: IPvAnyAddress,
                                        target_address: IPvAnyAddress,
                                        client_logical_address: int,
                                        timeout: float = constants.A_PROCESSING_TIME,
                                        activation_type: ActivationType = ActivationType.Default,
                                        protocol_version: DoipProtocolVersion = DoipProtocolVersion.DoIP_13400_2012,
                                        vm_specific: int = None) -> Optional[RoutingActivationResponse]:
        """Initiate Routing activation request

        Args:
            source_address (IPvAnyAddress): source IP address
            target_address (IPvAnyAddress): target IP address
            client_logical_address (int): client's logical address
            timeout (float, optional): timeout in seconds for the operation
            activation_type (ActivationType, optional): The activation type. Defaults to ActivationType.Default.
            protocol_version (DoipProtocolVersion, optional): the Doip Protocol Version. Defaults to DoipProtocolVersion.DoIP_13400_2012.
            vm_specific (int, optional): optional vm specific argument. Defaults to None.

        Returns:
            Optional[RoutingActivationResponse]: RoutingActivationResponse if got a response, None otherwise
        """
        
        
        _, tcp_communicator = self._get_tcp_communicator(source_address=source_address, target_address=target_address)

        return self.initiate_routing_activation_req_bound(communicator=tcp_communicator,
                                                          client_logical_address=client_logical_address,
                                                          timeout=timeout,
                                                          activation_type=activation_type,
                                                          protocol_version=protocol_version,
                                                          vm_specific=vm_specific)
    
    @staticmethod
    def initiate_routing_activation_req_bound(communicator: Type[CommunicatorBase],
                                              client_logical_address: int,
                                              timeout: float = constants.A_PROCESSING_TIME,
                                              activation_type: ActivationType = ActivationType.Default,
                                              protocol_version: DoipProtocolVersion = DoipProtocolVersion.DoIP_13400_2012,
                                              vm_specific: int = None) -> Optional[RoutingActivationResponse]:
        """Initiate Routing activation request via the provided communicator 

        Args:
            communicator (Type[CommunicatorBase]): communicator to perform the request over
            client_logical_address (int): client's logical address
            timeout (float, optional): timeout in seconds for the operation
            activation_type (ActivationType, optional): The activation type. Defaults to ActivationType.Default.
            protocol_version (DoipProtocolVersion, optional): the Doip Protocol Version. Defaults to DoipProtocolVersion.DoIP_13400_2012.
            vm_specific (int, optional): optional vm specific argument. Defaults to None.

        Returns:
            Optional[RoutingActivationResponse]: RoutingActivationResponse if got a response, None otherwise
        """
        
        message = messages.RoutingActivationRequest(
            client_logical_address, activation_type, vm_specific=vm_specific
        )
        data = DoipUtils._pack_doip_message(message, protocol_version)
        bytes_sent = communicator.send(data=data, timeout=timeout)
        if not bytes_sent:
            communicator.close()
            return None
        response = DoipUtils._read_doip(communicator, timeout=timeout)
        if type(response) is messages.RoutingActivationResponse:
            return response
        return None

    def req_entity_status(self, 
                          source_address: IPvAnyAddress, 
                          source_port: int, 
                          target_address: IPvAnyAddress, 
                          protocol_version: DoipProtocolVersion = DoipProtocolVersion.DoIP_13400_2012) -> EntityStatusResponse:
        """Initiate Entity status request

        Args:
            source_address (IPvAnyAddress): source IP address
            source_port (int): source port
            target_address (IPvAnyAddress): target IP address
            protocol_version (DoipProtocolVersion, optional): the Doip Protocol Version. Defaults to DoipProtocolVersion.DoIP_13400_2012.

        Returns:
            EntityStatusResponse: if got a response, None otherwise
        """
        is_answer_cb = partial(DoipUtils._is_answer, 
                               expected_source_port=source_port, 
                               l4_type=LayerType.UdpLayer, 
                               expected_resp_type=messages.EntityStatusResponse)

        message = messages.DoipEntityStatusRequest()
        doip_layer_data = self._pack_doip_message(message, protocol_version)
        packet = Packet()
        if source_address.version == 4:
            ip_layer = IPv4Layer(src_addr=str(source_address), dst_addr=str(target_address))
        else:
            ip_layer = IPv6Layer(src_addr=str(source_address), dst_addr=str(target_address))
        packet.add_layer(ip_layer)
        udp_layer = UdpLayer(src_port=source_port, dst_port=DOIP_PORT)
        packet.add_layer(udp_layer)
        doip_layer = PayloadLayer(doip_layer_data)
        packet.add_layer(doip_layer)
        resp_packet = self.raw_socket.send_receive_packet(packet, is_answer_cb, constants.A_PROCESSING_TIME)
        if resp_packet:
            parser = Parser()
            parser.reset()
            result = parser.read_message(bytes(resp_packet.get_layer(LayerType.PayloadLayer)))
            if type(result) is messages.EntityStatusResponse:
                return result
            elif result:
                self.logger.warning(
                    f"Received unexpected DoIP message type {type(result)}. Ignoring"
                )
        return None
    
    @staticmethod
    def send_uds_request(
        logger: logging.Logger,
        communicator: Type[CommunicatorBase],
        payload: bytes,
        client_logical_address: int,
        target_logical_address: int,
        timeout: float) -> int:
        """Sends a UDS request

        Args:
            communicator (Type[CommunicatorBase]): communicator to perform the request over
            payload (bytes): the UDS request payload
            client_logical_address (int): client's logical address
            target_logical_address (int): target's logical address
            timeout (float): timeout in seconds for the operation

        Returns:
            int: number of bytes actually sent
        """
        message = messages.DiagnosticMessage(
            source_address=client_logical_address,
            target_address=target_logical_address,
            user_data=payload
            )
        data = DoipUtils._pack_doip_message(message=message)
        sent_bytes = communicator.send(data=data, timeout=timeout)
        response = DoipUtils._read_doip(communicator, timeout=timeout)
        if type(response) is not messages.DiagnosticMessagePositiveAcknowledgement:
            logger.warning("Did not received DiagnosticMessagePositiveAcknowledgement")
        return sent_bytes        

    @staticmethod
    def read_uds_response(communicator: Type[CommunicatorBase], timeout: float) -> Optional[bytes]:
        """Reads a UDS response

        Args:
            communicator (Type[CommunicatorBase]): communicator to read the response over
            timeout (float): timeout in seconds for the operation

        Returns:
            Optional[bytes]: UDS response in bytes if received a valid response, False otherwise
        """
        response = DoipUtils._read_doip(communicator, timeout=timeout)

        if type(response) is messages.DiagnosticMessage:
            return bytes(response.user_data)
        return None

    @staticmethod
    def _pack_doip_message(message: messages.DoIPMessage, protocol_version: DoipProtocolVersion = DoipProtocolVersion.DoIP_13400_2012,) -> bytes:
        payload_data = message.pack()
        payload_type = messages.payload_message_to_type[type(message)]

        return DoIPClient._pack_doip(protocol_version, payload_type, payload_data)
    
    def _get_tcp_communicator(self, source_address: IPvAnyAddress, target_address: IPvAnyAddress) -> tuple[bool, TcpCommunicator]:
        """Fetch TCP communicator from cache if available and still open, create new one otherwise

        Returns:
            tuple[bool, TcpCommunicator]: True + communicator if fetched from cache, False + communicator otherwise
        """
        tcp_communicator = self._tcp_communicators_cache.get(f"{str(source_address)}_{str(target_address)}", None)

        if tcp_communicator and tcp_communicator.is_open():
            return (True, tcp_communicator)
        elif tcp_communicator and not tcp_communicator.is_open():
            tcp_communicator.close()
        
        tcp_communicator = TcpCommunicator(destination_ip=str(target_address),
                            source_ip=str(source_address),
                            dport=DOIP_PORT,
                            sport=0)
        tcp_communicator.open()
        tcp_communicator.connect()
        self._tcp_communicators_cache[f"{str(source_address)}_{str(target_address)}"] = tcp_communicator
        return (False, tcp_communicator)

    @staticmethod
    def _is_answer(other: Packet, expected_source_port: int, l4_type: LayerType, expected_resp_type: Type[messages.DoIPMessage]):
        payload_layer = other.get_layer(LayerType.PayloadLayer)
        received_dst_port = None
        if l4_type == LayerType.TcpLayer:
            tcp_layer: TcpLayer = other.get_layer(LayerType.TcpLayer)
            if tcp_layer:
                received_dst_port = tcp_layer.dst_port
        elif l4_type == LayerType.UdpLayer:
            udp_layer: UdpLayer = other.get_layer(LayerType.UdpLayer)
            if udp_layer:
                received_dst_port = udp_layer.dst_port
        else:
            raise RuntimeError(f"Unsupported layer 4 type received: {l4_type}, expected TCP/UDP")
        
        if received_dst_port and received_dst_port == expected_source_port and payload_layer:
            parser = Parser()
            result = parser.read_message(bytes(payload_layer))
            return True if type(result) is expected_resp_type else False
        return False

    @staticmethod
    def _read_doip(communicator: Type[CommunicatorBase], timeout: float = constants.A_PROCESSING_TIME) -> messages.DoIPMessage:
        parser = Parser()
        start_time = time.time()
        data = bytearray()
        response = None
        while (time.time() - start_time) <= timeout:
            if data:
                response = parser.read_message(data)
            data = bytearray()
            if type(response) is messages.GenericDoIPNegativeAcknowledge:
                break
            elif response and type(response) is not messages.DoIPMessage:
                # We got a response that might actually be interesting to the caller,
                # so return it.
                return response
            else:
                # There were no responses in the parser, so we need to read off the network
                # and feed that to the parser until we find another DoIP message
                data = communicator.recv(recv_timeout=timeout)
                if len(data) == 0:
                    break
        return None
