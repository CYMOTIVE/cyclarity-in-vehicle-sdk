#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "PcapPlusPlus::Packet++" for configuration "Release"
set_property(TARGET PcapPlusPlus::Packet++ APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(PcapPlusPlus::Packet++ PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libPacket++.a"
  )

list(APPEND _cmake_import_check_targets PcapPlusPlus::Packet++ )
list(APPEND _cmake_import_check_files_for_PcapPlusPlus::Packet++ "${_IMPORT_PREFIX}/lib/libPacket++.a" )

# Import target "PcapPlusPlus::Pcap++" for configuration "Release"
set_property(TARGET PcapPlusPlus::Pcap++ APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(PcapPlusPlus::Pcap++ PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libPcap++.a"
  )

list(APPEND _cmake_import_check_targets PcapPlusPlus::Pcap++ )
list(APPEND _cmake_import_check_files_for_PcapPlusPlus::Pcap++ "${_IMPORT_PREFIX}/lib/libPcap++.a" )

# Import target "PcapPlusPlus::Common++" for configuration "Release"
set_property(TARGET PcapPlusPlus::Common++ APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(PcapPlusPlus::Common++ PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libCommon++.a"
  )

list(APPEND _cmake_import_check_targets PcapPlusPlus::Common++ )
list(APPEND _cmake_import_check_files_for_PcapPlusPlus::Common++ "${_IMPORT_PREFIX}/lib/libCommon++.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
