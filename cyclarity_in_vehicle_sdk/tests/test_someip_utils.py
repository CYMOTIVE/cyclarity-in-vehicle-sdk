from ipaddress import IPv4Address
from unittest import TestCase
from unittest.mock import Mock, PropertyMock
from cyclarity_in_vehicle_sdk.communication.ip.udp.udp import UdpCommunicator
from cyclarity_in_vehicle_sdk.protocol.someip.impl.someip_utils import SomeipUtils
from cyclarity_in_vehicle_sdk.protocol.someip.models.someip_models import SOMEIP_EVTGROUP_INFO, SOMEIP_METHOD_INFO, SOMEIP_SERVICE_INFO, SOMEIP_ENDPOINT_OPTION, Layer4ProtocolType


class SomeipUtilsUTs(TestCase):
    def setUp(self):
        self.someip_utils = SomeipUtils()

    def test_find_service_success(self):
        test_sd_packet = 'ffff8100000000300000000101010200c00000000000001001000010b0a7000101000003000000000000000c000904007f00000100110457'
        expected_service_id = 0xb0a7
        expected_service_info = SOMEIP_SERVICE_INFO(
            service_id=expected_service_id,
            instance_id=1,
            major_ver=1,
            minor_ver=0,
            ttl=3,
            endpoints=[
                SOMEIP_ENDPOINT_OPTION(
                    endpoint_addr='127.0.0.1',
                    port=1111,
                    port_type=Layer4ProtocolType.UDP)
            ]
        )

        mocked_socket = Mock(spec=UdpCommunicator)
        mocked_socket.recv.return_value = bytes.fromhex(test_sd_packet)

        result = self.someip_utils.find_service(mocked_socket,
                                       expected_service_id)
        
        mocked_socket.send.assert_called_once()
        mocked_socket.recv.assert_called_once()

        self.assertEqual(len(result), 1)
        self.assertEqual(expected_service_info, result[0])

    def test_find_service_invalid_packet(self):
        test_sd_packet = 'ffff810000000003000000000000000c000904f0000010010457'
        service_id = 0xb0a7

        mocked_socket = Mock(spec=UdpCommunicator)
        mocked_socket.recv.return_value = bytes.fromhex(test_sd_packet)

        result = self.someip_utils.find_service(mocked_socket,
                                       service_id)
        
        mocked_socket.send.assert_called_once()
        mocked_socket.recv.assert_called_once()

        self.assertEqual(len(result), 0)

    def test_find_service_not_received(self):
        service_id = 0xb0a7

        mocked_socket = Mock(spec=UdpCommunicator)
        mocked_socket.recv.return_value = None

        result = self.someip_utils.find_service(mocked_socket,
                                       service_id)
        
        mocked_socket.send.assert_called_once()
        mocked_socket.recv.assert_called_once()

        self.assertEqual(len(result), 0)

    def test_invoke_method_success(self):
        test_packet = 'b0a70001000000220000000101018000323032352d30312d32325431343a33393a32382e303931323538'
        test_service_id = 0xb0a7
        test_service_info = SOMEIP_SERVICE_INFO(
            service_id=test_service_id,
            instance_id=1,
            major_ver=1,
            minor_ver=0,
            ttl=3,
            endpoints=[
                SOMEIP_ENDPOINT_OPTION(
                    endpoint_addr='127.0.0.1',
                    port=1111,
                    port_type=Layer4ProtocolType.UDP)
            ]
        )
        test_method_id = 1
        expected_method_info = SOMEIP_METHOD_INFO(method_id=test_method_id, payload=b'2025-01-22T14:39:28.091258')

        mocked_socket = Mock(spec=UdpCommunicator)
        mocked_socket.recv.return_value = bytes.fromhex(test_packet)

        result = self.someip_utils.method_invoke(mocked_socket,
                                       test_service_info,
                                       test_method_id
                                       )
        
        mocked_socket.send.assert_called_once()
        mocked_socket.recv.assert_called_once()

        self.assertEqual(expected_method_info, result)

    def test_subscribe_eventgroup_success(self):
        test_packet = 'ffff8100000000240000000201010200c00000000000001007000000b0a70001010000030000000100000000'
        test_eventgroup_payload = 'b0a78001000000220000000101010200323032352d30312d32325431343a34353a35352e363530313536'
        test_service_id = 0xb0a7
        test_service_info = SOMEIP_SERVICE_INFO(
            service_id=test_service_id,
            instance_id=1,
            major_ver=1,
            minor_ver=0,
            ttl=3,
            endpoints=[
                SOMEIP_ENDPOINT_OPTION(
                    endpoint_addr='127.0.0.1',
                    port=1111,
                    port_type=Layer4ProtocolType.UDP)
            ]
        )
        test_eventgroup_id = 1
        expected_eventgroup_info = SOMEIP_EVTGROUP_INFO(eventgroup_id=1, initial_data=b'\xb0\xa7\x80\x01\x00\x00\x00"\x00\x00\x00\x01\x01\x01\x02\x002025-01-22T14:45:55.650156')

        mocked_sd_socket = Mock(spec=UdpCommunicator)
        mocked_sd_socket.recv.return_value = bytes.fromhex(test_packet)

        mocked_ep_socket = Mock(spec=UdpCommunicator)
        mocked_ep_socket.recv.return_value = bytes.fromhex(test_eventgroup_payload)
        type(mocked_ep_socket).source_ip = PropertyMock(return_value=IPv4Address('127.0.0.1'))  
        type(mocked_ep_socket).source_port = PropertyMock(return_value=0)  

        result = self.someip_utils.subscribe_evtgrp(mocked_sd_socket,
                                                    mocked_ep_socket,
                                       test_service_info,
                                       test_eventgroup_id,
                                       transport_protocol=Layer4ProtocolType.UDP
                                       )
        
        mocked_sd_socket.send.assert_called_once()
        mocked_sd_socket.recv.assert_called_once()
        mocked_ep_socket.recv.assert_called_once()

        self.assertEqual(expected_eventgroup_info, result)