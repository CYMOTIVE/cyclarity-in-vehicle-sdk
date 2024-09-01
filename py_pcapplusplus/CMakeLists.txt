cmake_minimum_required(VERSION 3.15...3.27)
project(py_pcapplusplus)

set(CMAKE_CXX_STANDARD 14)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(PcapPlusPlus REQUIRED)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

# Detect the installed nanobind package and import it into CMake
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE NB_DIR)
list(APPEND CMAKE_PREFIX_PATH "${NB_DIR}")

find_package(nanobind CONFIG REQUIRED)

set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)

nanobind_add_module(py_pcapplusplus_ext src/py_pcapplusplus_ext.cpp src/wrapperClasses.cpp)

set_property(TARGET py_pcapplusplus_ext PROPERTY POSITION_INDEPENDENT_CODE ON)

target_link_libraries(py_pcapplusplus_ext PUBLIC PcapPlusPlus::Pcap++ PcapPlusPlus::Packet++ PcapPlusPlus::Common++)

nanobind_add_stub(
    py_pcapplusplus_ext_stub
    MODULE py_pcapplusplus_ext
    OUTPUT py_pcapplusplus_ext.pyi
    PYTHON_PATH $<TARGET_FILE_DIR:py_pcapplusplus_ext>
    DEPENDS py_pcapplusplus_ext
    MARKER_FILE py.typed
)

install(TARGETS py_pcapplusplus_ext LIBRARY DESTINATION py_pcapplusplus)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/py.typed ${CMAKE_CURRENT_BINARY_DIR}/py_pcapplusplus_ext.pyi DESTINATION py_pcapplusplus)