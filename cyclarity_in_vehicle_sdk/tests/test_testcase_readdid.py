import unittest
from cyclarity_in_vehicle_sdk.security_testing.test_case import CyclarityTestCase, TestStepTuple
from cyclarity_in_vehicle_sdk.security_testing.uds_actions import (
    ReadDidAction, ReadDidOutputExact, ReadDidOutputMaskMatch, ReadDidOutputUnique, RdidDataTuple
)
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils
from cyclarity_in_vehicle_sdk.communication.isotp.impl.isotp_communicator import IsoTpCommunicator
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import CanCommunicatorSocketCan

class DummyCanCommunicator(CanCommunicatorSocketCan):
    def __init__(self):
        super().__init__(channel="vcan0", support_fd=False)

class DummyIsoTpCommunicator(IsoTpCommunicator):
    def __init__(self):
        super().__init__(can_communicator=DummyCanCommunicator(), rxid=0x123, txid=0x456)

class MockUdsUtils(UdsUtils):
    def __init__(self):
        super().__init__(data_link_layer=DummyIsoTpCommunicator())
    def read_did(self, didlist):
        return [RdidDataTuple(did=0x1234, data='ABCD')]

class TestCyclarityTestCase(unittest.TestCase):
    def make_action_and_output(self, output_cls, **output_kwargs):
        uds_utils = MockUdsUtils()
        action = ReadDidAction(dids=0x1234, uds_utils=uds_utils)
        expected_output = output_cls(dids_data=[RdidDataTuple(did=0x1234, data='ABCD')], **output_kwargs)
        return action, expected_output

    def test_testcase_with_readdid_outputs(self):
        # Exact match
        action1, expected_output1 = self.make_action_and_output(ReadDidOutputExact)
        # Mask match (mask set to match 'ABCD' as int)
        action2, expected_output2 = self.make_action_and_output(ReadDidOutputMaskMatch, mask=0xAFCF)
        # Unique (simulate previous output)
        action3, expected_output3 = self.make_action_and_output(ReadDidOutputUnique)

        testcase = CyclarityTestCase(
            name="ReadDID TestCase",
            test_items=[
                TestStepTuple(action=action3, expected_output=expected_output3),
                TestStepTuple(action=action1, expected_output=expected_output1),
                TestStepTuple(action=action2, expected_output=expected_output2),
            ]
        )

        self.assertTrue(testcase.run())

if __name__ == "__main__":
    unittest.main() 