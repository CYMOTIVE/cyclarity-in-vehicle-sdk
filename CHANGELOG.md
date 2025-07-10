# Changelog  

## [1.1.3] – 10/07/2025

### Added
- **Enhanced Multicast Communication**
  - Added separate socket management for sending and receiving in `MulticastCommunicator`
  - Implemented proper IPv6 multicast support with interface binding
  - Added model validation for multicast address configuration
  - Enhanced error handling with specific exception types

- **UDS Utils Enhancements**
  - Added `request_download()` method for initiating UDS download sessions
  - Added `transfer_data()` method for transferring data blocks during upload/download sessions
  - Added `transfer_exit()` method for completing transfer sessions
  - Enhanced UDS service support with comprehensive error handling and timeout management

### Changed
- **Raw Socket Communication**
  - Replaced async/await pattern with threading in `Layer3RawSocket.send_and_receive()` for better stability
  - Improved packet sniffing mechanism using dedicated threads instead of event loops

- **TCP Communication**
  - Enhanced error handling in `TcpCommunicator.is_open()` method
  - Added `TimeoutError` exception handling in `TcpCommunicator.recv()` method
  - Removed redundant error logging to reduce noise

- **Multicast Communication Architecture**
  - Refactored `MulticastCommunicator` to use separate input and output sockets
  - Improved socket lifecycle management with proper cleanup methods
  - Enhanced IPv6 multicast support with proper interface indexing
  - Added comprehensive validation for multicast address configuration

### Fixed
- **Socket Management**
  - Fixed socket reuse issues in multicast communication
  - Improved socket cleanup and resource management
  - Enhanced error handling for socket operations

- **IPv6 Support**
  - Fixed IPv6 multicast binding and sending logic
  - Improved interface handling for IPv6 multicast operations
  - Enhanced address validation and error reporting

- **Threading and Concurrency**
  - Fixed potential blocking issues in raw socket communication
  - Improved thread safety in packet sniffing operations

### Removed
- Removed unused configuration manager example files
- Removed outdated package configuration files

---

## [1.1.2] – 15/06/2025

### Fixed  
- py-pcapplusplus dependency to ^1.0.6

## [1.1.1] – 12/06/2025
  
### Added  
- **New Functionalities to UdsUtils**
  - UDS Read DTC Information service (0x19) Service
  - Clear Diagnostic Information service (0x14)
  
### Changed  
  
- Update dependency of py-pcapplusplus to version 1.0.5 - now supports macos platform

---  

## [1.1.0] – 11/05/2025
  
### Added  
  
- **Documentation Improvements**  
  - Added and revised docstrings throughout modules (`doip_utils`, `ConfigurationManager`, and more).  
  - Included usage examples in `README.md`.  
  - Added Sphinx configuration and files for generating HTML and PDF documentation.  
  - Provided instructions for documentation generation.  
  - Added generated PDF documentation to the repository.  
  - Documented data models and plugins in Sphinx docs.  
  
- **VLAN Interface Support**  
  - Introduced `CreateVlanAction` and implemented `_create_vlan_interface`.  
  - Utility for IP configuration building, with associated unit tests.  
  - Added explicit `action_type` literal for all relevant actions.  
  - Set up VLAN interface automatically after creation.  
  - Moved `IpAddressParams` definition to SDK.  
  
- **UDS Authentication Service**  
  - Added initial support for UDS authentication via certificate exchange.  
  - Added the `cryptography` dependency.  
  - Created `CryptoUtils` with signing operations and a dedicated `models.py` for crypto models.  
  - Refactored authentication logic, including param models for different authentication scenarios.  
  - Enhanced the `udsutils.authentication()` method to accept models based on `AuthenticationParamsBase`.  
  
- **Utilities**  
  - Added `str` operator implementations to UDS utils and DoIP/ISOTP communicators for easier object representation.  
  
### Changed  
  
- Reorganized documentation, including reversion and alignment of init files for shell devices and updates to RST files.  
- Enhanced organization and extensibility of Sphinx documentation (using `autosummary`, data models, plugins).  
- Updated usage of CyclarityFile alternative to use `HexBytes` instead of `bytes`.  
  
### Fixed  
  
- Improved IPv6 address handling in communication modules.  
- Resolved property name clashing with variable name.  
- Binding and sending logic fixed for IPv6 and socket reuse.  
- Fixed VLAN interface creation logic to skip already existing interfaces.  
- Improved raw socket and out-socket handling for better stability.  
  
### Removed  
  
- Deleted unused Doxygen configuration file.  
- Removed outdated scripts, Poetry lock file, and unnecessary parameters.  
  
---  
  