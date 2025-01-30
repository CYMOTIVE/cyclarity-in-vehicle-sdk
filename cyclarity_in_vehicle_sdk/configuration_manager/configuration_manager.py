from types import TracebackType
from typing import Any, Optional, Type, Union

from pydantic import Field

from .models import DeviceConfiguration, EthIfFlags, EthInterfaceConfiguration, EthernetInterfaceParams, InterfaceState, IpConfiguration, CanConfiguration, ConfigurationAction
from pyroute2 import NDB, IPRoute
from pyroute2.netlink.rtnl.ifinfmsg.plugins.can import CAN_CTRLMODE_NAMES
# **26/01/2025 lib pyroute2 was approved by Eugene with license Apache 2.0**
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel

ACTION_TYPES = Union[ConfigurationAction.get_subclasses()]

class ConfigurationManager(ParsableModel):
    actions: Optional[list[ACTION_TYPES]] = Field(default=None)

    _snapshots: dict[str, Any] = {}
    _ndb = None

    def __enter__(self):
        self.setup()
        return self
    
    def __exit__(self, 
                 exception_type: Optional[Type[BaseException]], 
                 exception_value: Optional[BaseException], 
                 traceback: Optional[TracebackType]) -> bool:
        self.teardown()
        return False
        
    def teardown(self):
        self._ndb.close()

    def setup(self):
        self._ndb = NDB()
        self.collect_snapshots()
        if self.actions:
            for action in self.actions:
                if type(action) is IpConfiguration:
                    self.configure_ip(action)
                if type(action) is CanConfiguration:
                    self.configure_can(action)
                if type(action) is EthInterfaceConfiguration:
                    self.configure_eth_interface(action)

    def get_device_configuration(self) -> DeviceConfiguration:
        config = DeviceConfiguration()
        self._get_eth_configuration(config)

        return config

    def _get_eth_configuration(self, config: DeviceConfiguration):
        interfaces = self._ndb.interfaces.dump()
        eth_interfaces = [iface for iface in interfaces if iface['ifi_type'] == 1]  
        for iface in eth_interfaces:
            eth_config = EthInterfaceConfiguration(
                interface=iface.ifname,
                mtu=iface.mtu,
                state=InterfaceState.state_from_string(iface.state),
                flags=EthIfFlags.get_flags_from_int(iface.flags)
            )
            ip_params = []
            with self._ndb.interfaces[iface.ifname] as interface:
                for address_obj in interface.ipaddr:
                    ip_params.append(IpConfiguration(interface=iface.ifname,
                                                     ip=address_obj['address'],
                                                     suffix=address_obj['prefixlen'],
                    ))

            config.eth_interfaces.append(
                EthernetInterfaceParams(
                    if_params=eth_config,
                    ip_params=ip_params)
                    )

    def rollback_all(self):
        for interface in self._snapshots.keys():
            self.rollback_interface(interface)

    def rollback_interface(self, if_name: str):
        if snapshot:= self._snapshots.get(if_name, None):
            with self._ndb.interfaces[if_name] as interface:
                interface.rollback(snapshot)

    def configure_ip(self, ip_config: IpConfiguration):
        if not self._is_interface_exists(ip_config.interface):
            self.logger.error(f"Ethernet interface: {ip_config.interface}, does not exists, cannot configure IP")
            return
        
        if str(ip_config.ip) in self.list_ips(ip_config.interface):
            self.logger.error(f"IP {str(ip_config.ip)} is already configured")
            return
        
        self.logger.debug(f"Configuring: {str(ip_config)}")
        with self._ndb.interfaces[ip_config.interface] as interface:
            interface.add_ip(address=str(ip_config.ip), prefixlen=ip_config.suffix)
            if ip_config.route:
                if ip_config.route.gateway:
                    self._ndb.routes.create(
                        dst=ip_config.cidr_notation,
                        gateway=ip_config.route.gateway
                    )
                else:
                    self._ndb.routes.create(
                        dst=ip_config.cidr_notation,
                        oif=interface['index']
                    )

    def remove_ip(self, ip_config: IpConfiguration):
        if not self._is_interface_exists(ip_config.interface):
            self.logger.error(f"Ethernet interface: {ip_config.interface}, does not exists, cannot remove IP")
            return
        
        if str(ip_config.ip) not in self.list_ips(ip_config.interface):
            self.logger.error(f"IP {str(ip_config.ip)} is not configured, cannot remove")
            return
        
        self.logger.debug(f"Removing: {str(ip_config)}")
        with self._ndb.interfaces[ip_config.interface] as interface:
            interface.del_ip(address=str(ip_config.ip), prefixlen=ip_config.suffix)

    def list_interfaces(self) -> list[str]:
        interfaces = []
        for interface in self._ndb.interfaces.dump():
            interfaces.append(interface.ifname)
            
        return interfaces
    
    def list_ips(self, if_name: str) -> list[str]:
        if not self._is_interface_exists(if_name):
            self.logger.error(f"Ethernet interface: {if_name}, does not exists")
            return []
        
        ret_addresses = []
        with self._ndb.interfaces[if_name] as interface:
            for address_obj in interface.ipaddr:
                ret_addresses.append(address_obj['address'])
        
        return ret_addresses


    def configure_can(self, can_config: CanConfiguration):
        if not self._is_interface_exists(can_config.channel):
            self.logger.error(f"CAN interface: {can_config.channel}, does not exists, cannot configure")
            return
        
        with IPRoute() as ip_route:
            idx = ip_route.link_lookup(ifname=can_config.channel)[0]
            link = ip_route.link('get', index=idx)
            if 'state' in link[0] and link[0]['state'] == 'up':
                ip_route.link('set', index=idx, state='down')
            
            ip_route.link(
                'set',
                index=idx,
                kind='can',
                can_bittiming={
                    'bitrate': can_config.bitrate,
                    'sample_point': can_config.sample_point
                    },
                can_ctrlmode=({'flags': CAN_CTRLMODE_NAMES["CAN_CTRLMODE_CC_LEN8_DLC"]}) if can_config.cc_len8_dlc else {}
            )
            ip_route.link('set', index=idx, state='up')

    def _is_interface_exists(self, ifname: str) -> bool:
        return ifname in self.list_interfaces()
    
    def collect_snapshots(self):
        interfaces = self.list_interfaces()
        for interface in interfaces:
            self._snapshots[interface] = self._ndb.interfaces[interface].snapshot()
    
    def configure_eth_interface(self, eth_config: EthInterfaceConfiguration):
        if not self._is_interface_exists(eth_config.interface):
            self.logger.error(f"Ethernet interface: {eth_config.interface}, does not exists, cannot configure")
            return
        
        with self._ndb.interfaces[eth_config.interface] as interface:
            if eth_config.flags:
                interface['flags'] |= sum(eth_config.flags, EthIfFlags(0))
            if eth_config.mtu:
                interface['mtu'] = eth_config.mtu

    # bluetooth,  FirewallTester, arp