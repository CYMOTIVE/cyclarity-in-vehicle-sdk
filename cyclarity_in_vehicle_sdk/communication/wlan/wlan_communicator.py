import struct
import fcntl
import time
import asyncio
from abc import abstractmethod
from typing import Sequence, Callable
import socket
import subprocess
from pydantic import Field
import construct

from py_pcapplusplus import Packet, PayloadLayer
from cyclarity_in_vehicle_sdk.communication.ip.base.raw_socket_base import RawSocketCommunicatorBase
from .mac_parsing import wifi_frame_header, FrameType, DataSubtype
from .radiotap_prasing import parse_radiotap, convert_channel_to_freq

ETH_P_ALL = 0x0003

IW_MODE_MONITOR = 6

# Define necessary constants
SIOCSIFFLAGS = 0x8914
IFF_UP = 0x1
IFF_BROADCAST = 0x2
IFF_PROMISC = 0x100
IFF_ALLMULTI = 0x200
ETH_P_ALL = 0x0003
SIOCGIWMODE = 0x8B07
SIOCSIWMODE = 0x8B06  # Command to set the mode of a wireless interface
SIOCGIFFLAGS = 0x8913  # Get the active flag word of the device.
SIOCSIFFLAGS = 0x8914  # Set the active flag word of the device.


class WiFiPacket():

    def __init__(self, data: bytes):
        self.data = data
        self.radiotap_header, self.packet_data = parse_radiotap(data)
        self.parsed_data = wifi_frame_header.parse(self.packet_data)

    def get_payload(self) -> Packet | None:
        if self.parsed_data.type == FrameType.DATA and self.parsed_data.subtype in [
            DataSubtype.DATA,
            # DataSubtype.DATA_CF_ACK,
            # DataSubtype.DATA_CF_POLL,
            # DataSubtype.DATA_CF_ACK_CF_POLL,
            # DataSubtype.NULL_FUNCTION,
            # DataSubtype.CF_ACK,
            # DataSubtype.CF_POLL,
            # DataSubtype.CF_ACK_CF_POLL,
            DataSubtype.QOS_DATA,
            # DataSubtype.QOS_DATA_CF_ACK,
            # DataSubtype.QOS_DATA_CF_POLL,
            # DataSubtype.QOS_DATA_CF_ACK_CF_POLL,
            # DataSubtype.QOS_NULL,
            # DataSubtype.RESERVED_13,
            # DataSubtype.QOS_CF_POLL_NO_DATA,
            # DataSubtype.QOS_CF_ACK_CF_POLL_NO_DATA,
        ]:

            packet = Packet()
            payload_layer = PayloadLayer(data=self.parsed_data.frame_body)
            packet.add_layer(payload_layer)
            return packet
        return None


class RawWiFiSocketCommunicatorBase(RawSocketCommunicatorBase):
    @abstractmethod
    def send_packet(self, packet: WiFiPacket) -> bool:
        raise NotImplementedError

    def send_packets(self, packets: Sequence[WiFiPacket]) -> bool:
        for i, packet in enumerate(packets):
            if not self.send_packet(packet):
                self.logger.error(
                    f"Could not send packet {i} of of {len(packets)}")
                return False
        return True

    def send(self, packet: WiFiPacket | Sequence[WiFiPacket]) -> bool:
        if self.is_open():
            if isinstance(packet, Sequence):
                return self.send_packets(packet)
            else:
                return self.send_packet(packet)
        else:
            self.logger.error(
                "Attempting to send packets without openning the socket.")
            return False

    def send_receive_packet(self, packet: WiFiPacket | Sequence[WiFiPacket] | None, is_answer: Callable[[WiFiPacket], bool], timeout: float) -> Packet | None:
        found_packets = self.send_receive_packets(packet, is_answer, timeout)
        if found_packets:
            return found_packets[0]  # Get first valid answer
        else:
            return None

    @abstractmethod
    def send_receive_packets(self, packet: WiFiPacket | Sequence[WiFiPacket] | None, is_answer: Callable[[WiFiPacket], bool], timeout: float) -> list[WiFiPacket]:
        raise NotImplementedError

    @abstractmethod
    def receive(self, timeout: float) -> WiFiPacket | None:
        raise NotImplementedError

    def receive_answer(self, is_answer: Callable[[WiFiPacket], bool], timeout: float) -> WiFiPacket | None:
        return self.send_receive_packet(None, is_answer, timeout)

    def receive_answers(self, is_answer: Callable[[WiFiPacket], bool], timeout: float) -> WiFiPacket | None:
        return self.send_receive_packets(None, is_answer, timeout)


class WiFiRawSocket(RawWiFiSocketCommunicatorBase):
    if_name: str = Field(
        description="Name of wlan interface to work with. (e.g. wlan0, wlan1 etc...)")
    _raw_socket: socket.socket | None = None

    def open(self) -> bool:
        ETH_P_ALL = 0x0003
        self._raw_socket = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))

        self._raw_socket.bind((self.if_name, ETH_P_ALL))

    def close(self) -> bool:
        self._raw_socket.close()
        self._raw_socket = None
        return True

    def is_open(self) -> bool:
        return self._raw_socket is not None

    def send_packet(self, packet: WiFiPacket) -> bool:
        if self._raw_socket:
            return self._raw_socket.send(WiFiPacket.data)
        else:
            self.logger.error(
                "Attempting to send a packet without openning the socket.")
            return False

    def send_receive_packet(self, packet: WiFiPacket | Sequence[WiFiPacket] | None, is_answer: Callable[[WiFiPacket], bool], timeout: float = 2) -> WiFiPacket | None:
        found_packets = self._send_receive_packets(
            packet, is_answer, timeout, max_answers=1)
        if found_packets:
            return found_packets[0]  # Get first valid answer
        else:
            return None

    def send_receive_packets(self, packet: WiFiPacket | Sequence[WiFiPacket] | None, is_answer: Callable[[WiFiPacket], bool], timeout: float = 2) -> list[WiFiPacket]:
        return self._send_receive_packets(packet, is_answer, timeout)

    def _send_receive_packets(self, packet: WiFiPacket | Sequence[WiFiPacket] | None, is_answer: Callable[[WiFiPacket], bool], timeout: float, max_answers=0) -> list[WiFiPacket]:
        if self._raw_socket:
            found_packets: list[WiFiPacket] = []

            async def find_packet(in_socket: socket.socket, timeout: int):
                nonlocal found_packets
                nonlocal is_answer
                time_spent = 0
                start_time = time.time()
                while time_spent < timeout:
                    received_data, received_from = in_socket.recvfrom(
                        65565, timeout=timeout-time_spent)
                    if not received_data:
                        break
                    recived_packet = WiFiPacket(received_data)
                    if is_answer():
                        found_packets.append(recived_packet)
                        if max_answers and max_answers <= len(found_packets):
                            break
                    time_spent = time.time()-start_time

            loop = asyncio.new_event_loop()
            find_packet_task = loop.create_task(
                find_packet(self._raw_socket, timeout))
            if packet:
                self.send(packet)
            loop.run_until_complete(find_packet_task)
            return found_packets
        else:
            self.logger.error(
                "Attempting to send packets without openning the socket.")
            raise Exception(
                "Attempt transmitting over a closed wlan interface.")

    def switch_channel(self, channel: int) -> bool:
        import subprocess
        try:
            subprocess.run(
                ["iwconfig", self.if_name, "channel", str(channel)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to change channel: {e}")
            return False

        return True

    def receive(self, timeout: float = 2) -> WiFiPacket | None:
        if self._raw_socket:
            data, recived_from = self._raw_socket.recvfrom(65565)
            try:
                return WiFiPacket(data)
            except construct.core.StreamError as e:
                try:
                    header, inner_data = parse_radiotap(data)
                except construct.core.StreamError:
                    header = None
                    inner_data = None
                self.logger.error(f"could not parse packet: {e}")
                self.logger.debug(f"unparsable data: {data}")
                self.logger.debug(f"unparsable data: {header}")
                self.logger.debug(f"unparsable data: {inner_data}")
                return None
        else:
            self.logger.error(
                "Attempting to receive packets without openning the socket.")
            raise Exception(
                "Attempt transmitting over a closed wlan interface.")

    def receive_answer(self, is_answer: Callable[[WiFiPacket], bool], timeout: float = 2) -> WiFiPacket | None:
        return self.send_receive_packet(None, is_answer, timeout)

    def receive_answers(self, is_answer: Callable[[WiFiPacket], bool], timeout: float = 2) -> list[WiFiPacket]:
        return self.send_receive_packets(None, is_answer, timeout)

    def _get_if_flags(self) -> None | int:
        ifreq = struct.pack('16sH', self.if_name.encode('utf-8'), 0)
        try:
            _, flags = struct.unpack('16sH', fcntl.ioctl(
                self._raw_socket, SIOCGIFFLAGS, ifreq))
        except OSError as e:
            self.logger.error(f"Could not get socket flags: {str(e)}")
            return None
        return flags

    def _set_if_flags(self, flags):
        ifreq = struct.pack('16sH', self.if_name.encode('utf-8'), flags)
        try:
            fcntl.ioctl(self._raw_socket, SIOCSIFFLAGS, ifreq)
        except OSError as e:
            self.logger.error(f"Could not set the socket flags: {str(e)}")
            return False
        return True

    def _update_if_flags(self, original_flags, set_flags=0, clear_flags=0):
        # Get the current flags
        new_flags = (original_flags | set_flags) & 0xffff
        new_flags = (original_flags & ~clear_flags) & 0xffff
        return self._set_if_flags(new_flags)

    def _set_mode(self, mode):
        ifreq = struct.pack('16sH14s', self.if_name.encode(
            'utf-8'), mode, b'\x00'*14)

        # Set the interface mode to monitor mode
        try:
            fcntl.ioctl(self._raw_socket.fileno(), SIOCSIWMODE, ifreq)
        except OSError as e:
            self.logger.error("Could not set the wireless mode:", str(e))
            return False
        else:
            self.logger.debug(
                f"Successfully set {self.if_name} to monitor mode.")
            return True

    def _get_mode(self):
        ifreq = struct.pack("16s16s", self.if_name.encode('utf-8'), b'\x00'*16)

        # Set the interface mode to monitor mode
        try:
            ioctl_response = fcntl.ioctl(
                self._raw_socket.fileno(), SIOCGIWMODE, ifreq)
        except OSError as e:
            self.logger.error("Could not set the wireless mode:", e)
            return None
        else:
            _, mode, _ = struct.unpack("16sH14s", ioctl_response)
            return mode

    def _set_dev_state(self, state):
        try:
            subprocess.run(["ip", "link", "set", "dev",
                           self.if_name, state], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Could not set device {state}: {str(e)}")
            return False
        return True

    def _verify_interface(self, verify_flags):
        flags = self._get_if_flags()
        if not flags & verify_flags:
            self.logger.error("Could not setup interface properly")
            self.logger.debug(f"flags: {flags}")
            return False

        mode = self._get_mode()
        if not mode == IW_MODE_MONITOR:
            self.logger.error(
                f"Could not set device to monitor mode. current mode is {mode}")
            return False

        return True


class WiFiRawMonitorSocket(WiFiRawSocket):
    def open(self) -> bool:
        self._raw_socket = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))

        flags = self._get_if_flags()
        if flags is None:
            return False

        self._original_flags = flags

        if not self._set_dev_state("down"):
            return False

        self._original_mode = self._get_mode()

        if self._original_mode is None:
            return False

        if not self._set_mode(IW_MODE_MONITOR):
            return False

        if not self._update_if_flags(flags, set_flags=IFF_BROADCAST | IFF_PROMISC | IFF_ALLMULTI):
            return False

        if not self._set_dev_state("up"):
            return False

        if not self._verify_interface(IFF_UP | IFF_BROADCAST | IFF_PROMISC | IFF_ALLMULTI):
            return False

        self._raw_socket.bind((self.if_name, ETH_P_ALL))

        return True

    def close(self) -> bool:
        if self._raw_socket:
            orig_mode = getattr(self, "_original_mode", None)
            orig_flags = getattr(self, "_original_flags", None)
            if orig_flags is not None or orig_mode is not None:
                self._set_dev_state("down")
                if orig_mode is not None:
                    self._set_mode(orig_mode)
                if orig_flags is not None:
                    self._set_if_flags(orig_flags)
                    if orig_flags & IFF_UP:
                        self._set_dev_state("up")

            self._raw_socket.close()
            self._raw_socket = None
        return True
