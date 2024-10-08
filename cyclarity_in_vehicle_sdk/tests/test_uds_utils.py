from unittest import TestCase
from cyclarity_in_vehicle_sdk.communication.ip.tcp.tcp import TcpCommunicator
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils
from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import SECURITY_ALGORITHM_XOR
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, ECUResetType, UdsResponseCode, UdsSid
from cyclarity_in_vehicle_sdk.communication.doip.doip_communicator import DoipCommunicator
from cyclarity_in_vehicle_sdk.communication.isotp.impl.isotp_communicator import IsoTpCommunicator
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import CanCommunicatorSocketCan
import pytest

# uds-server is GPL3 cannot be used here
@pytest.mark.skip
@pytest.mark.usefixtures("setup_uds_server")
class IntegrationTestIsoTpBased(TestCase):
    def setUp(self):
        self.uds_utils = UdsUtils(data_link_layer=IsoTpCommunicator(can_communicator=CanCommunicatorSocketCan(channel="vcan0", support_fd=True), txid=0x7df, rxid=0x7e8))
        self.uds_utils.setup()
        
    def test_tester_present(
        self
    ):
        self.assertTrue(self.uds_utils.tester_present())

    def test_session_default_session(
        self
    ):
        res = self.uds_utils.session(session=1, standard_version=2006)
        self.assertEqual(res.session_echo, 1)

    def test_read_did_single(
         self
    ):
        ret = self.uds_utils.read_did(didlist=0xf187)
        self.assertTrue(len(ret) == 1)
        self.assertTrue(0xf187 in ret)

    def test_read_did_multiple(
         self
    ):
        ret = self.uds_utils.read_did(didlist=[0xf187, 0xf189, 0x719e])
        self.assertTrue(len(ret) == 3)
        self.assertTrue(all(item in ret for item in [0xf187, 0xf189, 0x719e]))
    
    def test_read_did_single_not_exists(
         self
    ):
        with self.assertRaises(NegativeResponse) as cm:
            self.uds_utils.read_did(didlist=0xdd)

        ex = cm.exception
        print(ex.code_name)
        self.assertEqual(ex.code, 31)

# This test group expects a DoIP server running in the background, specifically ssas-public NetApp with DoIP over loopback
# see https://cymotive.atlassian.net/wiki/spaces/CLAR/pages/1537048577/DoIP+Server+Setup+Guide
@pytest.mark.skip
class IntegrationTestDoipBased(TestCase):
    def setUp(self):
        self.uds_utils = UdsUtils(data_link_layer=DoipCommunicator(tcp_communicator=TcpCommunicator(destination_ip="127.0.0.1",
                                                                                                           source_ip="127.0.0.1",
                                                                                                           sport=0,
                                                                                                           dport=13400),
                                                                            client_logical_address=0xe80,
                                                                            target_logical_address=0xdead,
                                                                            routing_activation_needed=True))
        self.assertTrue(self.uds_utils.setup())
    
    def test_tester_present(
        self
    ):
        self.assertTrue(self.uds_utils.tester_present())

    def test_session_default_session(
        self
    ):
        res = self.uds_utils.session(session=1)
        self.assertEqual(res.session_echo, 1)

    def test_read_did_single(
        self
    ):
        ret = self.uds_utils.read_did(didlist=0xF15B)
        self.assertTrue(len(ret) == 1)
        self.assertTrue(0xF15B in ret)

    def test_read_did_multiple(
        self
    ):
        ret = self.uds_utils.read_did(didlist=[0xF15B, 0xAB01, 0xAB02])
        self.assertTrue(len(ret) == 3)
        self.assertTrue(all(item in ret for item in [0xF15B, 0xAB01, 0xAB02]))
    
    def test_read_did_single_not_exists(
        self
    ):
        with self.assertRaises(NegativeResponse) as cm:
            self.uds_utils.read_did(didlist=0xdd)

        ex = cm.exception
        self.assertEqual(ex.code, UdsResponseCode.RequestOutOfRange)

    def test_read_did_multi_not_exists(
        self
    ):
        with self.assertRaises(NegativeResponse) as cm:
            self.uds_utils.read_did(didlist=[0xAB02, 0xdd])

        ex = cm.exception
        self.assertEqual(ex.code, UdsResponseCode.RequestOutOfRange)

    def test_security_access(
        self
    ):
        session_change = self.uds_utils.session(session=3)
        self.assertEqual(session_change.session_echo, 3)
        
        security_access_res = self.uds_utils.security_access(security_algorithm=SECURITY_ALGORITHM_XOR(seed_subfunction=1, key_subfunction=2, xor_val=0x78934673))
        self.assertTrue(security_access_res)


    def test_security_access_from_default_session_fail(
        self
    ):       
        session_change = self.uds_utils.session(session=1)
        self.assertEqual(session_change.session_echo, 1)
        with self.assertRaises(NegativeResponse) as cm:
            self.uds_utils.security_access(security_algorithm=SECURITY_ALGORITHM_XOR(seed_subfunction=1, key_subfunction=2, xor_val=0x78934673))
        ex = cm.exception
        self.assertEqual(ex.code, UdsResponseCode.SubFunctionNotSupportedInActiveSession)

    def test_security_access_invalid_key(
        self
    ):      
        session_change = self.uds_utils.session(session=3)
        self.assertEqual(session_change.session_echo, 3) 
        with self.assertRaises(NegativeResponse) as cm:
            self.uds_utils.security_access(security_algorithm=SECURITY_ALGORITHM_XOR(seed_subfunction=1, key_subfunction=2, xor_val=0x321))
        ex = cm.exception
        self.assertEqual(ex.code, UdsResponseCode.InvalidKey)

    def test_ecu_reset(
        self
    ):
        session_change = self.uds_utils.session(session=3)
        self.assertEqual(session_change.session_echo, 3)
        
        security_access_res = self.uds_utils.security_access(security_algorithm=SECURITY_ALGORITHM_XOR(seed_subfunction=1, key_subfunction=2, xor_val=0x78934673))
        self.assertTrue(security_access_res)

        ecu_reset_res = self.uds_utils.ecu_reset(reset_type=ECUResetType.hardReset)
        self.assertTrue(ecu_reset_res)

    def test_ecu_reset_without_security_access_fail(
        self
    ):
        session_change = self.uds_utils.session(session=3)
        self.assertEqual(session_change.session_echo, 3)

        with self.assertRaises(NegativeResponse) as cm:
            self.uds_utils.ecu_reset(reset_type=ECUResetType.hardReset)

        ex = cm.exception
        self.assertEqual(ex.code, UdsResponseCode.SecurityAccessDenied)

    def test_ecu_reset_from_default_session_fail(
        self
    ):
        session_change = self.uds_utils.session(session=1)
        self.assertEqual(session_change.session_echo, 1)
        with self.assertRaises(NegativeResponse) as cm:
            self.uds_utils.ecu_reset(reset_type=ECUResetType.hardReset)

        ex = cm.exception
        self.assertEqual(ex.code, UdsResponseCode.ServiceNotSupportedInActiveSession)

    def test_raw_uds(self):
        # session_change = self.uds_utils.session(session=3)
        # self.assertEqual(session_change.session_echo, 3)
        # security_access_res = self.uds_utils.security_access(security_algorithm=SECURITY_ALGORITHM_XOR(seed_subfunction=1, key_subfunction=2, xor_val=0x78934673))
        # self.assertTrue(security_access_res)
        resp = self.uds_utils.raw_uds_service(sid=UdsSid.TesterPresent, sub_function=0)
        resp