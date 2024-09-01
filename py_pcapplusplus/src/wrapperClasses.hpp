#include <Packet.h>
#include <PcapFileDevice.h>
#include <EthLayer.h>
#include <TcpLayer.h>
#include <UdpLayer.h>
#include <IPv4Layer.h>
#include <IPv6Layer.h>
#include <SomeIpLayer.h>
#include <SomeIpSdLayer.h>
#include <PayloadLayer.h>
#include <MacAddress.h>
#include <IpAddress.h>
#include <RawSocketDevice.h>
#include "SystemUtils.h"

#include <nanobind/nanobind.h>

enum class LayerType : uint8_t
{
    kTcpLayer = pcpp::TCP,
    kUdpLayer = pcpp::UDP,
    kEthLayer = pcpp::Ethernet,
    kIPv4Layer = pcpp::IPv4,
    kIPv6Layer = pcpp::IPv6,
    kSomeIpLayer = pcpp::SomeIP,
    kSomeIpSdLayer = pcpp::SomeIP,
    kPayloadLayer = pcpp::GenericPayload
};

int 
sendEthPackets(std::string const& ethInterface, std::vector<pcpp::Packet*> const& packets, std::string const& destAddr);

std::vector<pcpp::Packet*>
sniffEth(std::string const& ethInterface, double timeoutSeconds);

bool 
sendPacket(pcpp::RawSocketDevice &rawSocket, pcpp::Packet* packet);

pcpp::Packet*
receivePacket(pcpp::RawSocketDevice &rawSocket, bool blocking, double timeout);

bool 
replaceLinkLayerWithFreshEthLayer(pcpp::Packet* packet, pcpp::MacAddress const& srcMac, pcpp::MacAddress const& dstMac);

int 
sendPackets(pcpp::RawSocketDevice &rawSocket, std::vector<pcpp::Packet*>const& packets);

pcpp::IPAddress
getDefaultGateway(std::string const& ifName);

std::vector<pcpp::Packet*>
sniff(pcpp::RawSocketDevice &rawSocket, double timeoutSeconds);
