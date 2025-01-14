import select
import socket
from typing import Optional
from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpConnectionlessCommunicatorBase, IpVersion
from pydantic import Field, IPvAnyAddress

SOCK_DATA_RECV_AMOUNT = 4096

class UdpCommunicator(IpConnectionlessCommunicatorBase):
    _socket: socket.socket = None
        
    def open(self) -> bool:
        if self.source_ip.version == 6:
            self._socket = socket.socket(
                socket.AF_INET6,
                socket.SOCK_DGRAM,
            )
        else:
            self._socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

        self._socket.bind((self.source_ip.exploded, self.sport))
        self._socket.setblocking(0)

    def close(self) -> bool:
        self._socket.close()

    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        self._socket.sendto(
            data,
            (self.destination_ip.exploded, self.dport),
        )

    def send_to(self, target_ip: IPvAnyAddress, data: bytes) -> int:
        self._socket.sendto(
            data,
            (target_ip.exploded, self.dport),
        )

    def recv(self, recv_timeout: float = 0, size: int = SOCK_DATA_RECV_AMOUNT) -> bytes:
        recv_data = None
        ready = select.select([self._socket], [], [], recv_timeout)
        if ready[0]:
            recv_data = self._socket.recv(size)
        return recv_data
    
    def receive_from(self, size: int = SOCK_DATA_RECV_AMOUNT, recv_timeout: int = 0) -> tuple[bytes, IPvAnyAddress]:
        recv_tuple: tuple[bytes, IPvAnyAddress] = (None, None)
        if recv_timeout > 0:
            select.select([self.socket], [], [], recv_timeout)
        try:
            recv_tuple = self._socket.recvfrom(size)
        except BlockingIOError:
            pass
        return recv_tuple

    def get_type(self) -> CommunicatorType:
        return CommunicatorType.UDP
