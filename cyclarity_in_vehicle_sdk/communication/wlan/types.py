from enum import IntEnum
from cyclarity_in_vehicle_sdk.communication.wlan.mac_parsing import RSNCipherSuites

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