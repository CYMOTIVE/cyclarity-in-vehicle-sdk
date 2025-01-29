
from typing import Optional
from pydantic import BaseModel, Field, IPvAnyAddress, model_validator
from ipaddress import IPv4Network, IPv6Network

class IpRoute(BaseModel):
    gateway: Optional[str] = None

class IpConfiguration(BaseModel):
    interface: str = Field(description="The network interface for the IP to be configured")
    ip: IPvAnyAddress = Field(description="The IP to configure, IPv4/IPv6")
    suffix: int = Field(description="The subnet notation for this IP address")
    route: Optional[IpRoute] = Field(default=None,
                                     description="Optional parameter for setting a route for the IP")

    @model_validator(mode='after')
    def validate_ip_subnet(self):
        ip_subnet = str(self.ip) + '/' + str(self.suffix)
        if self.ip.version == 6:
            IPv6Network(ip_subnet, False)
        else:
            IPv4Network(ip_subnet, False)
        return self
    
    @property
    def cidr_notation(self) -> str:
        return f"{str(self.ip)}/{str(self.suffix)}"
    
    def __str__(self):
        return f"{self.interface} - {self.cidr_notation}"

class CanConfiguration(BaseModel):
    channel: str
    bitrate: int
    sample_point: float
    cc_len8_dlc: bool
