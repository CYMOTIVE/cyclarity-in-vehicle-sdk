from typing import Optional
from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorBase, CommunicatorType
from cyclarity_in_vehicle_sdk.communication.ip.tcp.tcp import TcpCommunicator
from cyclarity_in_vehicle_sdk.protocol.doip.impl.doip_utils import DoipUtils, RoutingActivationResponse

class DoipCommunicator(CommunicatorBase):
    tcp_communicator: TcpCommunicator
    client_logical_address: int
    target_logical_address: int
    routing_activation_needed: bool

    def send(self, data: bytes, timeout: Optional[float] = 1) -> int:
        reconnected = self._reconnect_tcp_if_needed()
        if reconnected:
            if not self._initiate_routing_activation_if_needed(timeout=timeout):
                return 0
         
        sent_bytes = DoipUtils.send_uds_request(communicator=self.tcp_communicator, 
                                   payload=data,
                                   client_logical_address=self.client_logical_address, 
                                   target_logical_address=self.target_logical_address,
                                   timeout=timeout)

        return sent_bytes
    
    def recv(self, recv_timeout: float) -> bytes:
        reconnected = self._reconnect_tcp_if_needed()
        if reconnected:
            if not self._initiate_routing_activation_if_needed(timeout=recv_timeout):
                return bytes()

        received_data = DoipUtils.read_uds_response(communicator=self.tcp_communicator, timeout=recv_timeout)
        return bytes(received_data) if received_data else bytes()

    def open(self) -> bool:
        self.tcp_communicator.open()
        self.tcp_communicator.connect()
        
        return self._initiate_routing_activation_if_needed()
    
    def close(self) -> bool:
        self.tcp_communicator.close()

        return True
    
    def get_type(self) -> CommunicatorType:
        return CommunicatorType.DOIP
    
    def _initiate_routing_activation_if_needed(self, timeout: float = 2) -> bool:
        if self.routing_activation_needed:
            resp = DoipUtils.initiate_routing_activation_req_bound(communicator=self.tcp_communicator,
                                                            client_logical_address=self.client_logical_address,
                                                            timeout=timeout)
            if not resp:
                self.logger.warning("No response received for initiate routing activation request")
                return False
            elif resp.response_code != RoutingActivationResponse.ResponseCode.Success:
                self.logger.warning(f"Failed to initiate routing activation, error code: {hex(resp.response_code)}")
                return False
            
        return True
    
    def _reconnect_tcp_if_needed(self) -> bool:
        if not self.tcp_communicator.is_open():
            self.tcp_communicator.close()
            self.tcp_communicator.open()
            self.tcp_communicator.connect()
            return True
        return False