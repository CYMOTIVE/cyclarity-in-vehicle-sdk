import struct
import construct as cs
import binascii
from Crypto.Cipher import AES

from .mac_parsing import wifi_frame_header

CCMP = cs.BitStruct(
    "PN0" / cs.Octet,
    "PN1" / cs.Octet,
    "res0" / cs.Octet,
    "key_id" / cs.BitsInteger(2),
    "ext_iv" / cs.BitsInteger(1),
    "res1" / cs.BitsInteger(5),
    "PN2" / cs.Octet,
    "PN3" / cs.Octet,
    "PN4" / cs.Octet,
    "PN5" / cs.Octet,
    "data" / cs.Bytewise(cs.GreedyBytes),
)


class WifiEncAlgorithmBase():
    def __init__(self, mac_header, payload):
        pass


class CCMPWifiEncAlgorithm(WifiEncAlgorithmBase):
    def __init__(self, mac_header, payload):
        self.ccmp_payload = CCMP.parse(payload)
        self.pn = self._get_pn()
        self.key_id = self.ccmp_payload.key_id
        self.nonce = self._create_nonce(mac_header, self.pn)
        self.aad = self._create_aad(mac_header)

    def _get_pn(self):
        pn = self.ccmp_payload.PN5
        pn = (pn << 8) | self.ccmp_payload.PN4
        pn = (pn << 8) | self.ccmp_payload.PN3
        pn = (pn << 8) | self.ccmp_payload.PN2
        pn = (pn << 8) | self.ccmp_payload.PN1
        pn = (pn << 8) | self.ccmp_payload.PN0
        return pn

    def _addr2bin(self, addr):
        return binascii.a2b_hex(addr.replace(':', ''))

    def _pn2bin(self, pn):
        return struct.pack(">Q", pn)[2:]

    def _create_nonce(self, mac_header, pn):
        priority = mac_header.frame_body.header.qos_control.tid
        addr = mac_header.address2

        return struct.pack("B", priority) + self._addr2bin(addr) + self._pn2bin(pn)

    def _create_aad(self, mac_header, amsdu_spp=False):
        mac_headers_raw = wifi_frame_header.build(mac_header)
        # FC field with masked values
        fc = mac_headers_raw[:2]
        fc = struct.pack("<BB", fc[0] & 0x8f, fc[1] & 0xc7)

        # Sequence number is masked, but fragment number is included
        sc = struct.pack(
            "<H", mac_header.sequence_control.fragment_number & 0xf)

        addr1 = self._addr2bin(mac_header.address1)
        addr2 = self._addr2bin(mac_header.address2)
        addr3 = self._addr2bin(mac_header.address3)
        tid = struct.pack("<H", mac_header.frame_body.header.qos_control.tid)
        aad = fc + addr1 + addr2 + addr3 + sc + tid

        return aad

    def decrypt(self, tk, verify=True):
        payload = self.ccmp_payload.data

        # Decrypt using AES in CCM Mode.
        cipher = AES.new(tk, AES.MODE_CCM, self.nonce, mac_len=8)
        cipher.update(self.aad)
        plaintext = cipher.decrypt(payload[:-8])

        try:
            if verify:
                cipher.verify(payload[-8:])
        except ValueError:
            return None

        return plaintext
