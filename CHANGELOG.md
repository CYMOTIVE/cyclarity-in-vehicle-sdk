# Changelog  

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
  