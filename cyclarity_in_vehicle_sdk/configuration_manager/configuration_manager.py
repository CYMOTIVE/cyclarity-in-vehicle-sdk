from typing import Union

from pydantic import IPvAnyAddress
from .models import IpConfiguration, CanConfiguration, IpRoute
from pyroute2 import NDB, IPRoute
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel

class ConfigurationManager(ParsableModel):
    actions: list[Union[IpConfiguration, CanConfiguration]]

    def setup(self):
        for action in self.actions:
            if type(action) is IpConfiguration:
                self.configure_ip(action)
            if type(action) is CanConfiguration:
                self.configure_can(action)

    def teardown(self):
        # restores
        pass

    def configure_ip(self, ip_config: IpConfiguration):
        if not self._is_eth_interface_exists(ip_config.interface):
            self.logger.error(f"Ethernet interface: {ip_config.interface}, does not exists, cannot configure IP")
            return
        
        if str(ip_config.ip) in self.list_ips(ip_config.interface):
            self.logger.error(f"IP {str(ip_config.ip)} is already configured")
            return
        
        self.logger.debug(f"Configuring: {str(ip_config)}")
        with NDB() as ndb:
            with ndb.interfaces[ip_config.interface] as interface:
                interface.add_ip(address=str(ip_config.ip), prefixlen=ip_config.suffix)
                if ip_config.route:
                    if ip_config.route.gateway:
                        ndb.routes.create(
                            dst=ip_config.cidr_notation,
                            gateway=ip_config.route.gateway
                        )
                    else:
                        ndb.routes.create(
                            dst=ip_config.cidr_notation,
                            oif=interface['index']
                        )

    def remove_ip(self, ip_config: IpConfiguration):
        if not self._is_eth_interface_exists(ip_config.interface):
            self.logger.error(f"Ethernet interface: {ip_config.interface}, does not exists, cannot remove IP")
            return
        
        if str(ip_config.ip) not in self.list_ips(ip_config.interface):
            self.logger.error(f"IP {str(ip_config.ip)} is not configured, cannot remove")
            return
        
        self.logger.debug(f"Removing: {str(ip_config)}")
        with NDB() as ndb:
            with ndb.interfaces[ip_config.interface] as interface:
                interface.del_ip(address=str(ip_config.ip), prefixlen=ip_config.suffix)

    def list_interfaces(self) -> list[str]:
        ip_route = IPRoute()
        interfaces = []
        for link in ip_route.get_links():
            interfaces.append(link.get_attr('IFLA_IFNAME'))
        
        return interfaces
    
    def list_ips(self, if_name: str) -> list[str]:
        if not self._is_eth_interface_exists(if_name):
            self.logger.error(f"Ethernet interface: {if_name}, does not exists")
            return []
        
        ret_addresses = []
        with NDB() as ndb:
            with ndb.interfaces[if_name] as interface:
                for address_obj in interface.ipaddr:
                    ret_addresses.append(address_obj['address'])
        
        return ret_addresses


    def configure_can(self, can_config: CanConfiguration):
        pass

    def _is_eth_interface_exists(self, ifname: str) -> bool:
        return ifname in self.list_interfaces()