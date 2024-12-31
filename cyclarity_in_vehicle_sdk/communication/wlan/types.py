from enum import IntEnum
from typing import Optional
from pydantic import BaseModel
from cyclarity_in_vehicle_sdk.utils.custom_types.hexbytes import HexBytes
from cyclarity_in_vehicle_sdk.communication.wlan.mac_parsing import RSNCipherSuites
from cyclarity_in_vehicle_sdk.utils.custom_types.enum_by_name import pydantic_enum_by_name
from cyclarity_in_vehicle_sdk.communication.wlan.wlan_communicator import WiFiSecurity

class BeaconInfo(BaseModel):
    ssid: str
    mac: str
    security: Optional[list[WiFiSecurity]] = None
    # Use raw representation to not limit additional parsing on the elements for future implementations.
    raw_information_elements: HexBytes
    def __str__(self):
        return ("Beacon info:\n"
                f"SSID: {self.ssid}, MAC: {self.mac}, securities: {', '.join(str(sec) for sec in self.security)}"
                "\n"
                )

class ProbeInfo(BaseModel):
    ssid: str
    src_mac: str

@pydantic_enum_by_name
class RSNCipherSuiteType(IntEnum):
    IEEE_WEP40 = RSNCipherSuites.IEEE_WEP40
    IEEE_TKIP = RSNCipherSuites.IEEE_TKIP
    IEEE_CCMP = RSNCipherSuites.IEEE_CCMP
    IEEE_WEP104 = RSNCipherSuites.IEEE_WEP104
    IEEE_BIP_CMAC_128 = RSNCipherSuites.IEEE_BIP_CMAC_128
    IEEE_GCMP_128 = RSNCipherSuites.IEEE_GCMP_128
    IEEE_GCMP_256 = RSNCipherSuites.IEEE_GCMP_256
    IEEE_CCMP_256 = RSNCipherSuites.IEEE_CCMP_256
    IEEE_BIP_GMAC_128 = RSNCipherSuites.IEEE_BIP_GMAC_128
    IEEE_BIP_GMAC_256 = RSNCipherSuites.IEEE_BIP_GMAC_256
    IEEE_BIP_CMAC_256 = RSNCipherSuites.IEEE_BIP_CMAC_256