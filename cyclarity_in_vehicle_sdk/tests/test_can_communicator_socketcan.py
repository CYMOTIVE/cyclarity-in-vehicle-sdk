import shlex
import subprocess
from unittest import mock, TestCase

import pytest
from cyclarity_in_vehicle_sdk.communication.can.base.can_communicator_base import CanMessage
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import CanCommunicatorSocketCan

test_m1 = CanMessage(
        arbitration_id=0x401,
        data=[0x44, 0x44, 0x44, 0x44, 0x44, 0x44],
        is_extended_id=False,
)  

test_m2 = CanMessage(
    arbitration_id=0x404,
    data=[0x55, 0x55, 0x55, 0x55, 0x55, 0x55],
    is_extended_id=True,
)

@pytest.fixture(scope="session", autouse=True)
def setup_vcan0():
    print("setup_vcan0")
    try:  
        output = subprocess.check_output('ip link show ' + "vcan0", shell=True)  
        if output:  
            print("Interface exists.")  
    except subprocess.CalledProcessError:  
        print("Interface does not exist.")  
        # Setup VCAN0
        subprocess.run(shlex.split("ip link add dev vcan0 type vcan"))
        subprocess.run(shlex.split("ip link set vcan0 mtu 16"))
        subprocess.run(shlex.split("ip link set up vcan0"))
    return

@pytest.fixture(scope="class")
def send_periodic_messages(setup_vcan0):
    print("send_periodic_messages")
    with CanCommunicatorSocketCan(channel="vcan0", support_fd=True) as can_comm:
        can_comm.send_periodically(test_m1, 0.1, 4)
        can_comm.send_periodically(test_m2, 0.1, 4)
        yield

@pytest.mark.skip
@pytest.mark.usefixtures("send_periodic_messages")
class TestCanCommunicatorSocketCan(TestCase):
    def setUp(self) -> None:
        self.can_comm = CanCommunicatorSocketCan(channel="vcan0", support_fd=True)
        self.can_comm.open()

    def tearDown(self) -> None:
        self.can_comm.close()
    
    def test_read_can_msg(
        self
    ):  
        read_msg = self.can_comm.receive()
        self.assertIsNotNone(read_msg)
        self.assertEqual(read_msg.arbitration_id, test_m1.arbitration_id or test_m2.arbitration_id)
        self.assertEqual(read_msg.data, test_m1.data or test_m2.data)
    
    def test_sniff_can_msgs(
        self
    ):  
        msgs = self.can_comm.sniff(sniff_time=0.5)
        self.assertIsNotNone(msgs)
        sniffed_ids = set()
        {sniffed_ids.add(msg.arbitration_id) for msg in msgs}
        self.assertEqual(len(sniffed_ids), 2)
        self.assertIn(test_m1.arbitration_id, sniffed_ids)
        self.assertIn(test_m2.arbitration_id, sniffed_ids)

    def test_sniff_can_msgs_blacklisted(
        self
    ):  
        self.can_comm.add_to_blacklist(canids=[test_m1.arbitration_id])
        msgs = self.can_comm.sniff(sniff_time=0.5)
        self.assertIsNotNone(msgs)
        sniffed_ids = set()
        {sniffed_ids.add(msg.arbitration_id) for msg in msgs}
        self.assertEqual(len(sniffed_ids), 1)
        self.assertNotIn(test_m1.arbitration_id, sniffed_ids)
        self.assertIn(test_m2.arbitration_id, sniffed_ids)