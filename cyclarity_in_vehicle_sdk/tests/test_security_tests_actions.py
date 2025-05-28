import unittest
from unittest.mock import MagicMock, patch, create_autospec
from cyclarity_in_vehicle_sdk.security_testing.uds_actions import (
    ReadDidAction, ReadDidOutputExact, ReadDidOutputError, ReadDidOutputMaskMatch, ReadDidOutputUnique,
    SessionControlAction, SessionControlOutputSuccess, SessionControlOutputError,
    ECUResetAction, ECUResetOutputSuccess, ECUResetOutputError,
    WriteDidAction, WriteDidOutputSuccess, WriteDidOutputError,
    RoutineControlAction, RoutineControlOutputSuccess, RoutineControlOutputError,
    CanSniffer, CanSnifferOutput
)
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import (
    NegativeResponse, RdidDataTuple, UdsResponseCode
)
from cyclarity_in_vehicle_sdk.utils.custom_types.hexbytes import HexBytes
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import CanCommunicatorSocketCan

class TestReadDidAction(unittest.TestCase):
    def setUp(self):
        self.uds_utils = create_autospec(UdsUtils)

    def test_read_did_exact_success(self):
        expected_data = [RdidDataTuple(did=0x123, data="ABCD")]
        self.uds_utils.read_did.return_value = expected_data
        action = ReadDidAction(dids=0x123, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = ReadDidOutputExact(dids_data=expected_data)
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

    def test_read_did_error(self):
        self.uds_utils.read_did.side_effect = NegativeResponse(
            code=UdsResponseCode.RequestOutOfRange,
            code_name="RequestOutOfRange"
        )
        action = ReadDidAction(dids=0x123, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = ReadDidOutputError(error_code=UdsResponseCode.RequestOutOfRange)
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

    def test_read_did_mask_match(self):
        # Data: 0xABCD & 0xFFCD == 0xABCD
        expected_data = [RdidDataTuple(did=0x123, data="ABCD")]
        self.uds_utils.read_did.return_value = expected_data
        action = ReadDidAction(dids=0x123, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = ReadDidOutputMaskMatch(mask="FFCD", dids_data=expected_data)
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

    def test_read_did_unique(self):
        # Simulate two outputs with different data for uniqueness
        expected_data1 = [RdidDataTuple(did=0x123, data="ABCD")]
        expected_data2 = [RdidDataTuple(did=0x123, data="BCDE")]
        self.uds_utils.read_did.return_value = expected_data2
        action = ReadDidAction(dids=0x123, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = ReadDidOutputUnique(dids_data=expected_data2)
        # prev_outputs is a list of previous outputs
        prev_outputs = [ReadDidOutputUnique(dids_data=expected_data1)]
        result = expected_output.validate(actual_output, prev_outputs=prev_outputs)
        self.assertTrue(result.success, result.fail_reason)

class TestSessionControlAction(unittest.TestCase):
    def setUp(self):
        self.uds_utils = create_autospec(UdsUtils)

    def test_session_control_success(self):
        action = SessionControlAction(session_id=1, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = SessionControlOutputSuccess()
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

    def test_session_control_error(self):
        self.uds_utils.session.side_effect = NegativeResponse(
            code=UdsResponseCode.ServiceNotSupportedInActiveSession,
            code_name="ServiceNotSupportedInActiveSession"
        )
        action = SessionControlAction(session_id=1, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = SessionControlOutputError(error_code=UdsResponseCode.ServiceNotSupportedInActiveSession)
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

class TestECUResetAction(unittest.TestCase):
    def setUp(self):
        self.uds_utils = create_autospec(UdsUtils)

    def test_ecu_reset_success(self):
        action = ECUResetAction(reset_type=1, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = ECUResetOutputSuccess()
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

    def test_ecu_reset_error(self):
        self.uds_utils.ecu_reset.side_effect = NegativeResponse(
            code=UdsResponseCode.SecurityAccessDenied,
            code_name="SecurityAccessDenied"
        )
        action = ECUResetAction(reset_type=1, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = ECUResetOutputError(error_code=UdsResponseCode.SecurityAccessDenied)
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

class TestWriteDidAction(unittest.TestCase):
    def setUp(self):
        self.uds_utils = create_autospec(UdsUtils)

    def test_write_did_success(self):
        action = WriteDidAction(did=0x123, value="ABCD", uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = WriteDidOutputSuccess()
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

    def test_write_did_error(self):
        self.uds_utils.write_did.side_effect = NegativeResponse(
            code=UdsResponseCode.RequestOutOfRange,
            code_name="RequestOutOfRange"
        )
        action = WriteDidAction(did=0x123, value="ABCD", uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = WriteDidOutputError(error_code=UdsResponseCode.RequestOutOfRange)
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

class TestRoutineControlAction(unittest.TestCase):
    def setUp(self):
        self.uds_utils = create_autospec(UdsUtils)

    def test_routine_control_success(self):
        mock_response = MagicMock()
        mock_response.data = b'\x01\x02\x03'
        self.uds_utils.routine_control.return_value = mock_response
        action = RoutineControlAction(routine_id=0x123, control_type=1, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = RoutineControlOutputSuccess(response_data=b'\x01\x02\x03')
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

    def test_routine_control_error(self):
        self.uds_utils.routine_control.side_effect = NegativeResponse(
            code=UdsResponseCode.SubFunctionNotSupported,
            code_name="SubFunctionNotSupported"
        )
        action = RoutineControlAction(routine_id=0x123, control_type=1, uds_utils=self.uds_utils)
        actual_output = action.execute()
        expected_output = RoutineControlOutputError(error_code=UdsResponseCode.SubFunctionNotSupported)
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)

class TestCanSniffer(unittest.TestCase):
    def setUp(self):
        self.can_communicator = create_autospec(CanCommunicatorSocketCan)

    def test_can_sniffer_success(self):
        mock_can_msg = MagicMock()
        mock_can_msg.arbitration_id = 0x123
        self.can_communicator.sniff.return_value = [mock_can_msg]
        action = CanSniffer(can_communicator=self.can_communicator, sniff_time=1.0)
        actual_output = action.execute()
        expected_output = CanSnifferOutput(can_ids=[0x123])
        result = expected_output.validate(actual_output)
        self.assertTrue(result.success, result.fail_reason)
        self.can_communicator.__enter__.assert_called_once()
        self.can_communicator.__exit__.assert_called_once()

if __name__ == '__main__':
    unittest.main() 