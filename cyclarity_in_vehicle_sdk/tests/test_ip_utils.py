

from ipaddress import IPv4Address, IPv6Address, ip_address
from unittest import TestCase

from cyclarity_in_vehicle_sdk.utils.ip.ip_utils import build_ip


class TestBuildIp(TestCase):  
  
    def test_ipv4_valid(self):  
        base_ip = ip_address('192.168.1.1')  
        result = build_ip(base_ip, 24, 5)  
        self.assertEqual(result, IPv4Address('192.168.1.5'))  
  
    def test_ipv4_random_host(self):  
        base_ip = ip_address('192.168.1.1')  
        result = build_ip(base_ip, 24)  
        self.assertTrue(isinstance(result, IPv4Address))  
  
    def test_ipv4_invalid_prefix(self):  
        base_ip = ip_address('192.168.1.1')  
        result = build_ip(base_ip, 33)  
        self.assertIsNone(result)  
  
    def test_ipv4_invalid_host_part(self):  
        base_ip = ip_address('192.168.1.1')  
        result = build_ip(base_ip, 24, 256)  
        self.assertIsNone(result)  
  
    def test_ipv6_valid(self):  
        base_ip = ip_address('fabc:787:565:1::A')  
        result = build_ip(base_ip, 64, 0xcafe)  
        self.assertEqual(result, IPv6Address('fabc:787:565:1::CAFE'))  

    def test_ipv6_random_host(self):  
        base_ip = ip_address('2001:db8::1')  
        result = build_ip(base_ip, 64)  
        self.assertTrue(isinstance(result, IPv6Address))

    def test_ipv6_invalid_prefix(self):  
        base_ip = ip_address('2001:db8::1')  
        result = build_ip(base_ip, 129)  
        self.assertIsNone(result)  
  
    def test_ipv6_invalid_host_part(self):  
        base_ip = ip_address('2001:db8::1')  
        result = build_ip(base_ip, 64, 2**64)  
        self.assertIsNone(result)  
  
    def test_ipv4_prefix_0(self):  
        base_ip = ip_address('192.168.1.1')  
        result = build_ip(base_ip, 0, 1)  
        self.assertEqual(result, IPv4Address('0.0.0.1'))  
  
    def test_ipv6_prefix_0(self):  
        base_ip = ip_address('2001:db8::1')  
        result = build_ip(base_ip, 0, 1)  
        self.assertEqual(result, IPv6Address('::1'))  
  
    def test_ipv4_prefix_32(self):  
        base_ip = ip_address('192.168.1.1')  
        result = build_ip(base_ip, 32)  
        self.assertIsNone(result)  
  
    def test_ipv6_prefix_128(self):  
        base_ip = ip_address('2001:db8::1')  
        result = build_ip(base_ip, 128)  
        self.assertIsNone(result)  
  
    def test_invalid_ip_type(self):  
        base_ip = "invalid_ip"  
        result = build_ip(base_ip, 24, 1)  
        self.assertIsNone(result)  