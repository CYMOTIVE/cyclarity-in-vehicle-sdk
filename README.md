# In-Vehicle SDK Package  
  
This package provides the In-Vehicle SDK, offering a range of functionalities to support communication and operations with in-vehicle systems.  
  
## Features  
  
The In-Vehicle SDK package includes the following interfaces and implementations:  
  
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
  
4. **DoipUtils**: A utility library for performing Diagnostic over IP (DoIP) operations, such as vehicle identity requests, routing activation, and more.  
  
5. **UdsUtilsBase**: Used for performing Unified Diagnostic Services (UDS) operations, such as ECU reset, read DIDs, session change, and more. The following implementation is available:  
    * `UdsUtils` - Can be initialized to work over DoIP/ISO-TP  
  
6. **IDeviceShell**: Allows for the execution of shell commands. The following implementations are available:  
    * `AdbDeviceShell`  
    * `SerialDeviceShell`  
    * `SshDeviceShell`  

7. **SomeipUtils**: A utility library for SOME/IP operations, allowing the receive and parse services, and in these services invoke methods and subscribe to eventgroups

8. **Plugins**:
    * `SessionChangeCrashDetector`: a plugin that detects ECU crash based on UDS session change
    * `UnrespondedTesterPresentCrashDetector`: a plugin that detects ECU crash based on UDS TP that is not being responded
    * `UdsEcuRecoverPlugin`: a plugin responsible of recovering the ECU back to predefined UDS state - session and elevation
    * `RelayResetPlugin`: a plugin that resets a device via relay
    * `UdsBasedEcuResetPlugin`: a plugin that resets a device via UDS ECU Reset

## Installation  
  
You can install the In-Vehicle SDK package using pip:  
`pip install cyclarity-in-vehicle-sdk`
