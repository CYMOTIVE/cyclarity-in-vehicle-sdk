import select
import socket
import struct
from typing import Optional
from cyclarity_in_vehicle_sdk.communication.ip.base.ip_communicator_base import IpConnectionlessCommunicatorBase
from pydantic import Field, IPvAnyAddress, model_validator

from cyclarity_in_vehicle_sdk.communication.base.communicator_base import CommunicatorType

SOCK_DATA_RECV_AMOUNT = 4096

class MulticastCommunicator(IpConnectionlessCommunicatorBase):
    """A class used for multicast communication over IP networks.
    """
    interface_name: Optional[str] = Field(None, description="Network interface name - needed for IPv6 multicast")
    _in_socket: Optional[socket.socket] = None
    _out_socket: Optional[socket.socket] = None
    _interface_index: Optional[int] = None
    _is_open: bool = False
    
    @model_validator(mode="after")
    def validate_destination_ip(self) -> "MulticastCommunicator":
        if not self.destination_ip.is_multicast:
            raise ValueError(f"Invalid multicast address provided: {str(self.destination_ip)}")
        if self.destination_ip.version != self.source_ip.version:
            raise ValueError(f"Mismatch in IP version between source ({self.source_ip.version}) and destination ({self.destination_ip.version})")
        if self.destination_ip.version == 6 and not self.interface_name:
            raise ValueError("IPv6 multicast requires interface_name to be specified")
        return self

    def open(self) -> bool:
        """Opens the sockets for multicast communication.
        
        Creates separate sockets for receiving (bound to multicast group) 
        and sending (bound to source IP for proper source address).
        
        Returns:
            bool: True if both sockets were successfully opened.
        
        Raises:
            RuntimeError: If the communicator failed to open.
        """
        try:
            is_ipv6 = self.source_ip.version == 6

            if is_ipv6:
                self._interface_index = socket.if_nametoindex(self.interface_name)
                
            self._setup_receive_socket(is_ipv6)
            self._setup_send_socket(is_ipv6)
            self._is_open = True
            return True
            
        except Exception as e:
            self._cleanup_sockets()
            raise RuntimeError(f"Failed to open multicast communicator: {e}")

    def _setup_receive_socket(self, is_ipv6: bool) -> None:
        """Set up the socket for receiving multicast traffic."""
        family = socket.AF_INET6 if is_ipv6 else socket.AF_INET
        self._in_socket = socket.socket(family, socket.SOCK_DGRAM)
        self._in_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        if hasattr(socket, 'SO_REUSEPORT'):
            self._in_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        if is_ipv6:
            self._in_socket.bind((str(self.destination_ip), self.destination_port))
            
            join_data = struct.pack("16sI", self.destination_ip.packed, self._interface_index)
            self._in_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, join_data)
        else:
            self._in_socket.bind((str(self.destination_ip), self.destination_port))
            
            packed_local_addr = socket.inet_aton(str(self.source_ip))
            packed_multicast_addr = socket.inet_aton(str(self.destination_ip))
            mreq = struct.pack('4s4s', packed_multicast_addr, packed_local_addr)
            self._in_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self._in_socket.setblocking(False)

    def _setup_send_socket(self, is_ipv6: bool) -> None:
        """Set up the socket for sending traffic with proper source binding."""
        family = socket.AF_INET6 if is_ipv6 else socket.AF_INET
        self._out_socket = socket.socket(family, socket.SOCK_DGRAM)
        
        self._out_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if is_ipv6:
            self._out_socket.bind((str(self.source_ip), self.source_port))
            self._out_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, self._interface_index)
            self._out_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
        else:
            self._out_socket.bind((str(self.source_ip), self.source_port))
            self._out_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, 
                                      socket.inet_aton(str(self.source_ip)))
            self._out_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)

        self._out_socket.setblocking(False)

    def _cleanup_sockets(self) -> None:
        """Clean up both sockets safely."""
        if self._in_socket:
            try:
                self._in_socket.close()
            except Exception:
                pass
            finally:
                self._in_socket = None
                
        if self._out_socket:
            try:
                self._out_socket.close()
            except Exception:
                pass
            finally:
                self._out_socket = None
                
        self._is_open = False

    def close(self) -> bool:
        """Closes both sockets.

        Returns:
            bool: True if sockets were successfully closed.
        """
        self._cleanup_sockets()
        return True

    def is_open(self) -> bool:
        """Check if the communicator is open and ready.
        
        Returns:
            bool: True if both sockets are open and ready.
        """
        return self._is_open and self._in_socket is not None and self._out_socket is not None

    def send(self, data: bytes, timeout: Optional[float] = None) -> int:
        """Sends data to the multicast group.

        Args:
            data (bytes): The data to be sent.
            timeout (Optional[float], optional): The timeout for the send operation.

        Returns:
            int: The number of bytes sent.
            
        Raises:
            RuntimeError: If the communicator is not open.
        """
        if not self.is_open():
            raise RuntimeError("Communicator is not open")
            
        try:
            if self.destination_ip.version == 6:
                return self._out_socket.sendto(
                    data, 
                    (str(self.destination_ip), self.destination_port, 0, self._interface_index)
                )
            else:
                return self._out_socket.sendto(
                    data, 
                    (str(self.destination_ip), self.destination_port)
                )
        except Exception as e:
            raise RuntimeError(f"Failed to send data: {e}")

    def recv(self, recv_timeout: float = 0, size: int = SOCK_DATA_RECV_AMOUNT) -> Optional[bytes]:
        """Receives data from the multicast group.

        Args:
            recv_timeout (float, optional): The timeout for the receive operation.
            size (int, optional): The size of the data to be received.

        Returns:
            Optional[bytes]: The data received, or None if no data or timeout.
            
        Raises:
            RuntimeError: If the communicator is not open.
        """
        if not self.is_open():
            raise RuntimeError("Communicator is not open")
            
        try:
            if recv_timeout > 0:
                ready = select.select([self._in_socket], [], [], recv_timeout)
                if not ready[0]:
                    return None
                    
            return self._in_socket.recv(size)
        except BlockingIOError:
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to receive data: {e}")

    def send_to(self, target_ip: IPvAnyAddress, data: bytes) -> int:
        """Sends data to a specific IP address using the destination port.

        Args:
            target_ip (IPvAnyAddress): The target IP address.
            data (bytes): The data to be sent.

        Returns:
            int: The number of bytes sent.
            
        Raises:
            RuntimeError: If the communicator is not open.
        """
        if not self.is_open():
            raise RuntimeError("Communicator is not open")
            
        try:
            if target_ip.version == 6:
                return self._out_socket.sendto(
                    data, 
                    (str(target_ip), self.destination_port, 0, self._interface_index)
                )
            else:
                return self._out_socket.sendto(data, (str(target_ip), self.destination_port))
        except Exception as e:
            raise RuntimeError(f"Failed to send data to {target_ip}:{self.destination_port}: {e}")

    def receive_from(self, size: int, recv_timeout: int = 0) -> tuple[bytes, IPvAnyAddress]:
        """Receives data from any source and returns sender information.

        Args:
            size (int): The size of the data to be received.
            recv_timeout (int, optional): The timeout for the receive operation.

        Returns:
            tuple[bytes, IPvAnyAddress]: The data received and the sender's IP address.
            
        Raises:
            RuntimeError: If the communicator is not open.
            TimeoutError: If timeout occurs and no data is received.
        """
        if not self.is_open():
            raise RuntimeError("Communicator is not open")
            
        try:
            if recv_timeout > 0:
                ready = select.select([self._in_socket], [], [], recv_timeout)
                if not ready[0]:
                    raise TimeoutError("Receive operation timed out")
                    
            data, addr = self._in_socket.recvfrom(size)
            # Extract IP address from the address tuple
            sender_ip = IPvAnyAddress(addr[0])
            return (data, sender_ip)
        except BlockingIOError:
            raise TimeoutError("No data available (non-blocking)")
        except Exception as e:
            raise RuntimeError(f"Failed to receive data: {e}")

    def get_type(self) -> CommunicatorType:
        return CommunicatorType.MULTICAST
