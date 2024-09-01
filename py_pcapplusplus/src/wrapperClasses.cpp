#include "wrapperClasses.hpp"

#include <arpa/inet.h>
#include <net/if.h>
#include <ifaddrs.h>
#include <algorithm>
#include <iostream>
#include <RawPacket.h>
#include <PcapLiveDevice.h>
#include <PcapLiveDeviceList.h>
#include <NetworkUtils.h>
#include <nanobind/nanobind.h>

bool 
replaceLinkLayerWithFreshEthLayer(pcpp::Packet* packet, pcpp::MacAddress const& srcMac, pcpp::MacAddress const& dstMac)
{
    // replace first layer with clean Eth layer
    if(!packet->removeFirstLayer()) return false;
    if(!packet->insertLayer(nullptr, new pcpp::EthLayer(srcMac, dstMac, PCPP_ETHERTYPE_IP), true)) return false;

    packet->computeCalculateFields();
    return true;
}

int sendEthPackets(std::string const& ethInterface, std::vector<pcpp::Packet*>const& packets, std::string const& destAddr)
{
    pcpp::PcapLiveDevice* dev = pcpp::PcapLiveDeviceList::getInstance().getPcapLiveDeviceByName(ethInterface);
    if (!dev) {
        return 0;
    }

    if (!dev->open()) {
        return 0;
    }

    pcpp::MacAddress dstMac;
    if (pcpp::IPv4Address::isValidIPv4Address(destAddr)) {
        pcpp::IPv4Address destIp(destAddr);
        // send an ARP request to determine dst MAC address
        double arpResTO = 0;
        dstMac = pcpp::NetworkUtils::getInstance().getMacAddress(destIp, dev, arpResTO);
    }
    auto srcMac = dev->getMacAddress();

    int packetSent = 0;
    for (auto packet : packets) {
        if (replaceLinkLayerWithFreshEthLayer(packet, srcMac, dstMac)) {
            packetSent += dev->sendPacket(packet) ? 1 : 0;
        }
    }

    dev->close();
    return packetSent;
}


std::vector<pcpp::Packet*>
sniffEth(std::string const& ethInterface, double timeoutSeconds)
{
    pcpp::PcapLiveDevice* dev = pcpp::PcapLiveDeviceList::getInstance().getPcapLiveDeviceByName(ethInterface);
    if (!dev) {
        nanobind::raise("Invalid interface provided");
    }

    if (!dev->open()) {
        nanobind::raise("Error opening pcap live device");
    }

    std::vector<pcpp::Packet*> retPackets;
    pcpp::OnPacketArrivesStopBlocking cb = [&retPackets](pcpp::RawPacket* inPacket, pcpp::PcapLiveDevice* device, void*)->bool {
        retPackets.push_back(new pcpp::Packet(inPacket));
        return false;
    };

    if (0 == dev->startCaptureBlockingMode(cb, nullptr, timeoutSeconds)) {
        dev->close();
        nanobind::raise("Error while capturing from device");
    }
    dev->close();
    return retPackets;
}

bool 
sendPacket(pcpp::RawSocketDevice &rawSocket, pcpp::Packet* packet)
{
    return rawSocket.sendPacket(packet->getRawPacket());
}

pcpp::Packet*
receivePacket(pcpp::RawSocketDevice &rawSocket, bool blocking, double timeout)
{
    auto rawPacket = new pcpp::RawPacket();
    auto res = rawSocket.receivePacket(*rawPacket, blocking, timeout);

    if (pcpp::RawSocketDevice::RecvPacketResult::RecvSuccess == res) {
        return new pcpp::Packet(rawPacket, true);
    }
    else if (pcpp::RawSocketDevice::RecvPacketResult::RecvError == res) {
        delete rawPacket;
        nanobind::raise("Error reading from socket");
    }
    else {
        delete rawPacket;
        return nullptr;
    }
}

int sendPackets(pcpp::RawSocketDevice &rawSocket, std::vector<pcpp::Packet*>const& packets)
{
    int packetSent = 0;
    for (auto packet : packets) {
        packetSent += sendPacket(rawSocket, packet) ? 1 : 0;
    }
    return packetSent;
}

pcpp::IPAddress
getDefaultGateway(std::string const& ifName)
{
    // find interface name and index from IP address
	struct ifaddrs* addrs;
	getifaddrs(&addrs);
	for (struct ifaddrs* curAddr = addrs; curAddr != NULL; curAddr = curAddr->ifa_next)
	{
		if (curAddr->ifa_addr && (curAddr->ifa_flags & IFF_UP) && curAddr->ifa_name == ifName)
		{
			if  (curAddr->ifa_addr->sa_family == AF_INET)
			{
				struct sockaddr_in* sockAddr = (struct sockaddr_in*)(curAddr->ifa_addr);
				char addrAsCharArr[32];
				inet_ntop(curAddr->ifa_addr->sa_family, (void *)&(sockAddr->sin_addr), addrAsCharArr, sizeof(addrAsCharArr));
				return pcpp::IPAddress(addrAsCharArr);
			}
			else if (curAddr->ifa_addr->sa_family == AF_INET6)
			{
				struct sockaddr_in6* sockAddr = (struct sockaddr_in6*)(curAddr->ifa_addr);
				char addrAsCharArr[40];
				inet_ntop(curAddr->ifa_addr->sa_family, (void *)&(sockAddr->sin6_addr), addrAsCharArr, sizeof(addrAsCharArr));
				return pcpp::IPAddress(addrAsCharArr);
			}

		}
	}
    nanobind::raise("Failed to find default gateway");
}

std::vector<pcpp::Packet*>
sniff(pcpp::RawSocketDevice &rawSocket, double timeoutSeconds)
{
    pcpp::RawPacketVector rawPackets;
    std::vector<pcpp::Packet*> retPackets;
    int failedReads = 0;
    std::ignore = rawSocket.receivePackets(rawPackets, timeoutSeconds, failedReads);

    auto iter = rawPackets.begin();

    while (iter != rawPackets.end())
	{
        retPackets.push_back(new pcpp::Packet(rawPackets.getAndRemoveFromVector(iter), true));
	}

    return retPackets;
}