from typing import Optional
from pydantic import BaseModel, IPvAnyAddress


class IpAddressParams(BaseModel):
    ip: IPvAnyAddress
    vlan_id: Optional[int] = None

    class Config:  
        frozen = True

    def __hash__(self):
        return hash((self.ip, self.vlan_id))

    def __str__(self):
        vlan_str = f"Vlan ID: {str(self.vlan_id)}" if self.vlan_id else ""
        return f"IP: {str(self.ip)} {vlan_str}"
