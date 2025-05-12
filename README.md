# In-Vehicle SDK Package  

[![pypi](https://img.shields.io/pypi/v/cyclarity-in-vehicle-sdk)](https://pypi.org/project/cyclarity-in-vehicle-sdk/)
[![downloads](https://static.pepy.tech/badge/cyclarity-in-vehicle-sdk)](https://pepy.tech/projects/cyclarity-in-vehicle-sdk)
[![downloads_monthly](https://static.pepy.tech/badge/cyclarity-in-vehicle-sdk/month)](https://pepy.tech/projects/cyclarity-in-vehicle-sdk)
[![Tests](https://github.com/CYMOTIVE/cyclarity-in-vehicle-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/CYMOTIVE/cyclarity-in-vehicle-sdk/actions/workflows/ci.yml)

This package provides the In-Vehicle SDK, offering a range of functionalities to support communication and operations with in-vehicle systems.  
  
## Features  
  
The In-Vehicle SDK package includes the following interfaces and implementations:  

1. **Communication**
    1. **CommunicatorBase**: Provides the capability to send and receive byte data over various protocols. The following implementations are available:  
        * `TcpCommunicator`  
        * `UdpCommunicator`
        * `MulticastCommunicator`  
        * `IsoTpCommunicator`  
        * `DoipCommunicator`  
    
    2. **RawSocketCommunicatorBase**: Offers send, receive, and srp (send and receive answer) operations for `py_pcapplusplus.Packet` types. The following implementations are available:  
        * `Layer2RawSocket`  
        * `Layer3RawSocket`  
        * `WiFiRawSocket`
    
    3. **CanCommunicatorBase**: Exposes the python-can functionality, offering operations like send, receive, sniff, and more. The following implementation is available:  
        * `CanCommunicatorSocketCan` - A specific implementation for the socketcan driver  
  
2. **DoipUtils**: A utility library for performing Diagnostic over IP (DoIP) operations, such as vehicle identity requests, routing activation, and more.  
  
3. **UdsUtilsBase**: Used for performing Unified Diagnostic Services (UDS) operations, such as ECU reset, read DIDs, session change, and more. The following implementation is available:  
    * `UdsUtils` - Can be initialized to work over DoIP/ISO-TP  
  
4. **IDeviceShell**: Allows for the execution of shell commands. The following implementations are available:  
    * `AdbDeviceShell`  
    * `SerialDeviceShell`  
    * `SshDeviceShell`  

5. **SomeipUtils**: A utility library for SOME/IP operations, allowing the receive and parse services, and in these services invoke methods and subscribe to eventgroups

6. **Plugins**:
    * `SessionChangeCrashDetector`: a plugin that detects ECU crash based on UDS session change
    * `UnrespondedTesterPresentCrashDetector`: a plugin that detects ECU crash based on UDS TP that is not being responded
    * `UdsEcuRecoverPlugin`: a plugin responsible of recovering the ECU back to predefined UDS state - session and elevation
    * `RelayResetPlugin`: a plugin that resets a device via relay
    * `UdsBasedEcuResetPlugin`: a plugin that resets a device via UDS ECU Reset

7. **ConfigurationManager**: An API allowing to perform configuration of the IOT Device.
    * configure_actions(action/s) - can perform the following configuration actions on the device:
        1. `IpAddAction` - add an IP to an Ethernet interface, and optionally configure a route for this IP.
        2. `IpRemoveAction` - remove an existing IP from an Ethernet interface.
        3. `CanConfigurationAction` - configure CAN interface parameters. e.g. bitrate, sample-point, cc-len8-dlc flag and state.
        4. `EthInterfaceConfigurationAction` - configure the Ethernet interface: mtu, state and flags.
        5. `WifiConnectAction` - connect to a WiFi access point
        6. `CreateVlanAction` - creating a VLAN interface
    * get_device_configuration() - retrieves the current device configurations:
        1. Ethernet interface configuration: state, IPs, flags and MTU.
        2. CAN interface configurations: state, bitrate, sample-point and cc-len8-dlc flag.
        3. The available WiFi access points. 

The complete user manual can be found in [here](docs/cyclarity-in-vehicle-sdk.pdf)

## Installation  
  
You can install the In-Vehicle SDK package using pip:  
`pip install cyclarity-in-vehicle-sdk`

## Usage

Example for importing and using `CanCommunicatorSocketCan` for sending a Message
```
from cyclarity_in_vehicle_sdk.communication.can.base.can_communicator_base import CanMessage
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import CanCommunicatorSocketCan

canmsg = CanMessage(
            arbitration_id=0x123,
            is_extended_id = False,
            is_rx=False,
            data=b"\x00" * 8,
            is_fd=False,
            bitrate_switch=False,
        )

socket = CanCommunicatorSocketCan(channel="vcan0", support_fd=True)
with socket:
    socket.send(can_msg=canmsg)
```