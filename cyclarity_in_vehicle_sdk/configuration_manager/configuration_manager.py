from types import TracebackType
from typing import Optional, Type, Union

import nmcli
from pydantic import Field

from cyclarity_in_vehicle_sdk.configuration_manager.models import (
    CanInterfaceConfigurationInfo,
    DeviceConfiguration, 
    EthIfFlags,
    EthInterfaceParams,
    EthernetInterfaceConfigurationInfo,
    InterfaceState, 
    IpConfigurationParams,
    WifiAccessPointConfigurationInfo,
    CanFdOptions
    )
from cyclarity_in_vehicle_sdk.configuration_manager.actions import (
    ConfigurationAction,
    CreateVlanAction,
    IpAddAction,
    IpRemoveAction,
    WifiConnectAction,
    EthInterfaceConfigurationAction,
    CanConfigurationAction,
)
from pyroute2 import NDB, IPRoute
from pyroute2.netlink.exceptions import NetlinkError
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel

ACTION_TYPES = Union[ConfigurationAction.get_subclasses()]

class ConfigurationManager(ParsableModel):
    actions: Optional[list[ACTION_TYPES]] = Field(default=None)
    _ndb = None
    _can_ctrlmode_options: dict[str, str] = {'cc_len8_dlc': 'off', 'fd': 'off'}

    def model_post_init(self, *args, **kwargs):
        super().model_post_init(*args, **kwargs)
        self._ndb = NDB()

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
        """Cleanup internal objects
        """
        self._ndb.close()

    def setup(self):
        """Configures the received actions from the initialization
        """
        if self.actions:
            self.configure_actions(self.actions)

    def configure_actions(self, actions: Union[ConfigurationAction, list[ConfigurationAction]]):
        """Configures the received actions

        Args:
            actions (Union[ConfigurationAction, list[ConfigurationAction]]): list of configuration actions to configure
        """
        if isinstance(actions, ConfigurationAction):
            actions = [actions]

        for action in actions:
            if type(action) is IpAddAction:
                self._configure_ip(action)
            if type(action) is IpRemoveAction:
                self._remove_ip(action)
            if type(action) is CanConfigurationAction:
                self._configure_can(action)
            if type(action) is EthInterfaceConfigurationAction:
                self._configure_eth_interface(action)
            if type(action) is WifiConnectAction:
                self._connect_wifi_device(action)
            if type(action) is CreateVlanAction:
                self._create_vlan_interface(action)

    def get_device_configuration(self) -> DeviceConfiguration:
        """Get the current device configuration

        Returns:
            DeviceConfiguration: the device's current configurations
        """
        config = DeviceConfiguration()
        self._get_eth_configuration(config)
        self._get_can_configuration(config)
        self._get_wifi_devices_info(config)

        return config
    
    def _create_vlan_interface(self, vlan_create_params: CreateVlanAction):
        if self._is_interface_exists(vlan_create_params.if_name):
            self.logger.info(f"Ethernet interface: {vlan_create_params.if_name}, already exists")
            return
        
        with IPRoute() as ip:
            ip.link(
                "add",
                ifname=vlan_create_params.if_name,
                kind="vlan",
                link=ip.link_lookup(ifname=vlan_create_params.if_link)[0],
                vlan_id=vlan_create_params.vlan_id
            )
            ip.link(
                "set",
                index=ip.link_lookup(ifname=vlan_create_params.if_name)[0],
                state="up"
            )

    def _connect_wifi_device(self, wifi_connect_params: WifiConnectAction):
        try:
            nmcli.device.wifi_connect(ssid=wifi_connect_params.ssid,
                                      password=wifi_connect_params.password)
        except nmcli.ConnectionActivateFailedException:
            self.logger.error(f"Failed to connect to: {wifi_connect_params.ssid}")

    def _configure_ip(self, ip_config: IpAddAction):
        if not self._is_interface_exists(ip_config.interface):
            self.logger.error(f"Ethernet interface: {ip_config.interface}, does not exists, cannot configure IP")
            return
        
        if str(ip_config.ip) in self._list_ips(ip_config.interface):
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
                    ).commit()
                else:
                    self._ndb.routes.create(
                        dst=ip_config.cidr_notation,
                        oif=interface['index']
                    ).commit()

    def _remove_ip(self, ip_config: IpRemoveAction):
        if not self._is_interface_exists(ip_config.interface):
            self.logger.error(f"Ethernet interface: {ip_config.interface}, does not exists, cannot remove IP")
            return
        
        if str(ip_config.ip) not in self._list_ips(ip_config.interface):
            self.logger.error(f"IP {str(ip_config.ip)} is not configured, cannot remove")
            return
        
        if ip_config.route:
            route = None
            if ip_config.route.gateway:
                route = self._ndb.routes.get({'dst': ip_config.cidr_notation, 'gateway': ip_config.route.gateway})
            else:
                route = self._ndb.routes.get({'dst': ip_config.cidr_notation})
            if route:  
                route.remove().commit()

        self.logger.debug(f"Removing: {str(ip_config)}")
        with self._ndb.interfaces[ip_config.interface] as interface:
            interface.del_ip(address=str(ip_config.ip), prefixlen=ip_config.suffix)

    def _list_interfaces(self) -> list[str]:
        interfaces = []
        for interface in self._ndb.interfaces.dump():
            interfaces.append(interface.ifname)
            
        return interfaces
    
    def _list_ips(self, if_name: str) -> list[str]:
        if not self._is_interface_exists(if_name):
            self.logger.error(f"Ethernet interface: {if_name}, does not exists")
            return []
        
        ret_addresses = []
        with self._ndb.interfaces[if_name] as interface:
            for address_obj in interface.ipaddr:
                ret_addresses.append(address_obj['address'])
        
        return ret_addresses


    def _configure_can(self, can_config: CanConfigurationAction):
        if not self._is_interface_exists(can_config.channel):
            self.logger.error(f"CAN interface: {can_config.channel}, does not exists, cannot configure")
            return
        with IPRoute() as ip_route:
            idx = ip_route.link_lookup(ifname=can_config.channel)[0]
            link = ip_route.link('get', index=idx)
            if 'state' in link[0] and link[0]['state'] == 'up':
                ip_route.link('set', index=idx, state='down')
            
            if can_config.cc_len8_dlc:
                self._can_ctrlmode_options.update({'cc_len8_dlc': 'on'})
            if can_config.fd:
                self._can_ctrlmode_options.update({'fd': 'on'})
            
            try:
                ip_route.link(
                    'set',
                    index=idx,
                    kind='can',
                    can_bittiming={
                        'bitrate': can_config.bitrate,
                        'sample_point': can_config.sample_point
                        },
                    can_ctrlmode=self._can_ctrlmode_options,
                    can_data_bittiming=({'bitrate': can_config.fd.dbitrate} if can_config.fd else {})
                )
            except NetlinkError as ex:
                self.logger.error(f"Failed to configure CAN interface. what: {ex}")
                
            if can_config.state == InterfaceState.UP:
                ip_route.link('set', index=idx, state='up')

    def _configure_eth_interface(self, eth_config: EthInterfaceConfigurationAction):
        if not self._is_interface_exists(eth_config.interface):
            self.logger.error(f"Ethernet interface: {eth_config.interface}, does not exists, cannot configure")
            return
        
        with self._ndb.interfaces[eth_config.interface] as interface:
            if eth_config.flags:
                interface['flags'] = (0xffffffff & sum(eth_config.flags, EthIfFlags(0)))
            if eth_config.mtu:
                interface['mtu'] = eth_config.mtu
            if eth_config.state:
                interface['state'] = eth_config.state.lower()

    def _is_interface_exists(self, ifname: str) -> bool:
        return ifname in self._list_interfaces()

    def _get_wifi_devices_info(self, config: DeviceConfiguration):
        try:
            wifi_list = nmcli.device.wifi()
            for wifi in wifi_list:
                if wifi.ssid:
                    wifi_dev = next((wifi_dev for wifi_dev in config.configurations_info if (type(wifi_dev) is WifiAccessPointConfigurationInfo 
                                                                                             and wifi_dev.ssid == wifi.ssid)), None)
                    if wifi_dev:
                        wifi_dev.connected = True if wifi.in_use else wifi_dev.connected
                    else:
                        config.configurations_info.append(WifiAccessPointConfigurationInfo(ssid=wifi.ssid,
                                                    security=wifi.security,
                                                    connected=wifi.in_use,
                                                    ))
        except Exception:
            pass

    def _get_eth_configuration(self, config: DeviceConfiguration):
        interfaces = self._ndb.interfaces.dump()
        eth_interfaces = [iface for iface in interfaces if iface['ifi_type'] == 1] # 1 = ARPHRD_ETHER
        for iface in eth_interfaces:
            eth_config = EthInterfaceParams(
                interface=iface.ifname,
                mtu=iface.mtu,
                state=InterfaceState.state_from_string(iface.state),
                flags=EthIfFlags.get_flags_from_int(iface.flags)
            )
            ip_params = []
            with self._ndb.interfaces[iface.ifname] as interface:
                for address_obj in interface.ipaddr:
                    ip_params.append(IpConfigurationParams(interface=iface.ifname,
                                                     ip=address_obj['address'],
                                                     suffix=address_obj['prefixlen'],
                    ))

            config.configurations_info.append(
                EthernetInterfaceConfigurationInfo(
                    if_params=eth_config,
                    ip_params=ip_params)
                    )
            
    def _get_can_configuration(self, config: DeviceConfiguration):
        can_interfaces = self._ndb.interfaces.dump().filter(kind='can')
        with IPRoute() as ip_route:
            for iface in can_interfaces:
                link = ip_route.link('get', index=iface.index)[0]
                attrs = dict(link['attrs'])
                link_info_attrs = dict(attrs['IFLA_LINKINFO']['attrs'])
                info_data_attrs = dict(link_info_attrs['IFLA_INFO_DATA']['attrs'])
                fd_options: CanFdOptions = None
                if info_data_attrs.get('IFLA_CAN_CTRLMODE', {}).get('fd', None) and \
                    info_data_attrs.get('IFLA_CAN_DATA_BITTIMING', None):
                    fd_options = CanFdOptions(dbitrate=info_data_attrs.get('IFLA_CAN_DATA_BITTIMING', None).get('bitrate', 0))

                can_config = CanInterfaceConfigurationInfo(
                    channel=iface.ifname,
                    state=InterfaceState.state_from_string(iface.state),
                    bitrate=int(info_data_attrs.get('IFLA_CAN_BITTIMING', {}).get('bitrate', 0)),
                    sample_point=float(info_data_attrs.get('IFLA_CAN_BITTIMING', {}).get('sample_point', 0) / 1000.0),
                    cc_len8_dlc=info_data_attrs.get('IFLA_CAN_CTRLMODE', {}).get('cc_len8_dlc', False),
                    fd=fd_options
                )
                config.configurations_info.append(can_config)