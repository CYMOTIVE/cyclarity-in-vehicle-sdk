import secrets
from unittest import TestCase
from cyclarity_in_vehicle_sdk.communication.ip.tcp.tcp import TcpCommunicator
from cyclarity_in_vehicle_sdk.protocol.uds.impl.uds_utils import UdsUtils
from cyclarity_in_vehicle_sdk.protocol.uds.models.uds_models import SECURITY_ALGORITHM_XOR
from cyclarity_in_vehicle_sdk.protocol.uds.base.uds_utils_base import NegativeResponse, ECUResetType, UdsResponseCode, UdsSid, RdidDataTuple, UdsStandardVersion
from cyclarity_in_vehicle_sdk.communication.doip.doip_communicator import DoipCommunicator
from cyclarity_in_vehicle_sdk.communication.isotp.impl.isotp_communicator import IsoTpCommunicator
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import CanCommunicatorSocketCan
import pytest
from mock import MagicMock

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
        res = self.uds_utils.session(session=1, standard_version=UdsStandardVersion.ISO_14229_2006)
        self.assertEqual(res.session_echo, 1)

    def test_read_did_single(
         self
    ):
        ret = self.uds_utils.read_did(didlist=0xf187)
        self.assertTrue(len(ret) == 1)
        self.assertTrue(0xf187 in [did_tuple.did for did_tuple in ret])

    def test_read_did_multiple(
         self
    ):
        ret = self.uds_utils.read_did(didlist=[0xf187, 0xf189, 0x719e])
        self.assertTrue(len(ret) == 3)
        ret_dids = [did_tuple.did for did_tuple in ret]
        self.assertTrue(all(item in ret_dids for item in [0xf187, 0xf189, 0x719e]))

    def test_read_did_multiple_same(
         self
    ):
        ret = self.uds_utils.read_did(didlist=[0xf187, 0xf187, 0xf187])
        self.assertTrue(len(ret) == 3)
        ret_dids = [did_tuple.did for did_tuple in ret]
        self.assertTrue(all(item in ret_dids for item in [0xf187]))
    
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
        self.assertTrue(0xF15B in [did_tuple.did for did_tuple in ret])

    def test_read_did_multiple(
        self
    ):
        ret = self.uds_utils.read_did(didlist=[0xF15B, 0xAB01, 0xAB02])
        self.assertTrue(len(ret) == 3)
        ret_dids = [did_tuple.did for did_tuple in ret]
        self.assertTrue(all(item in ret_dids for item in [0xF15B, 0xAB01, 0xAB02]))

    def test_read_did_multiple_same(
        self
    ):
        ret = self.uds_utils.read_did(didlist=[0xF15B, 0xF15B, 0xF15B])
        self.assertTrue(len(ret) == 3)
        ret_dids = [did_tuple.did for did_tuple in ret]
        self.assertTrue(all(item in ret_dids for item in [0xF15B]))
    
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

class UdsUtilsUTs(TestCase):
    def setUp(self):
        self.uds_utils = UdsUtils(data_link_layer=DoipCommunicator(tcp_communicator=TcpCommunicator(destination_ip="127.0.0.1",
                                                                                                           source_ip="127.0.0.1",
                                                                                                           sport=0,
                                                                                                           dport=13400),
                                                                            client_logical_address=0xe80,
                                                                            target_logical_address=0xdead,
                                                                            routing_activation_needed=True))
        self.uds_utils.data_link_layer = MagicMock()
    def test_split_dids_single(self):  
        did1 = 0x123  
        data_len = 15  
        did1_data = secrets.token_bytes(data_len)  
        dids = [did1]  
        input_data = did1.to_bytes(length=2, byteorder='big') + did1_data  
        expected_res = [RdidDataTuple(did=did1, data=did1_data.hex())]  
        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)  
        self.assertEqual(res, expected_res)  

    def test_split_dids_multiple_same_did(self):
        did1 = 0x123
        did1_number = 3
        data_len = 15
        did1_data = secrets.token_bytes(data_len) 
        dids = [did1] * did1_number
        input_data = (did1.to_bytes(length=2, byteorder='big') + did1_data) * did1_number
        expected_res = [RdidDataTuple(did=did1, data=did1_data.hex())] * did1_number 

        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)

        self.assertEqual(res, expected_res)

    def test_split_dids_multiple(self):  
        did1 = 0x123  
        did2 = 0x456  
        data_len = 15  
        did1_data = secrets.token_bytes(data_len)  
        did2_data = secrets.token_bytes(data_len)  
        dids = [did1, did2]  
        input_data = did1.to_bytes(length=2, byteorder='big') + did1_data + did2.to_bytes(length=2, byteorder='big') + did2_data  
        expected_res = [  
            RdidDataTuple(did=did1, data=did1_data.hex()),  
            RdidDataTuple(did=did2, data=did2_data.hex())  
        ]  
        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)  
        self.assertEqual(res, expected_res)  

    def test_split_dids_not_found(self):  
        did1 = 0x123  
        data_len = 15  
        did1_data = secrets.token_bytes(data_len)  
        dids = [0x999]  # DID not present in the data  
        input_data = did1.to_bytes(length=2, byteorder='big') + did1_data  
        expected_res = []  
        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)  
        self.assertEqual(res, expected_res)  

    def test_split_dids_partly_not_found_first(self):  
        did1 = 0x123  
        data_len = 15  
        did1_data = secrets.token_bytes(data_len)  
        dids = [0x999, did1]  # DID not present in the data  
        input_data = did1.to_bytes(length=2, byteorder='big') + did1_data  
        expected_res = [
            RdidDataTuple(did=did1, data=did1_data.hex())
        ]  
        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)  
        self.assertEqual(res, expected_res)  

    def test_split_dids_partly_not_found_second(self):  
        did1 = 0x123  
        data_len = 15  
        did1_data = secrets.token_bytes(data_len)  
        dids = [did1, 0x999]  # DID not present in the data  
        input_data = did1.to_bytes(length=2, byteorder='big') + did1_data  
        expected_res = [
            RdidDataTuple(did=did1, data=did1_data.hex())
        ]  
        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)  
        self.assertEqual(res, expected_res)  

    def test_split_dids_empty_list(self):  
        dids = []  
        input_data = ""  
        expected_res = []  
        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)  
        self.assertEqual(res, expected_res)  

    def test_split_dids_empty_data(self):  
        dids = [0x123]  
        input_data = b''  
        expected_res = []  
        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)  
        self.assertEqual(res, expected_res)  

    def test_split_dids_overlapping(self):  
        did1 = 0x123  
        did2 = 0x1234  
        data_len = 15    
        did1_data = secrets.token_bytes(data_len)  
        did2_data = secrets.token_bytes(data_len)  
        dids = [did1, did2]  
        input_data = did1.to_bytes(length=2, byteorder='big') + did1_data + did2.to_bytes(length=2, byteorder='big') + did2_data  
        expected_res = [  
            RdidDataTuple(did=did1, data=did1_data.hex()),  
            RdidDataTuple(did=did2, data=did2_data.hex())  
        ]  
        res = self.uds_utils._split_dids(didlist=dids, data_bytes=input_data)  
        self.assertEqual(res, expected_res)  