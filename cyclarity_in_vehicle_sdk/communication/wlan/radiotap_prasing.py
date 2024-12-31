import cyclarity_in_vehicle_sdk.external.python_radiotap.radiotap as radiotap

def convert_channel_to_freq(channel):
    if 1 <= channel <= 14:
        return 2407 + (channel * 5)
    else:
        raise ValueError(
            "Channel number is out of range for channels 1-14 in the 2.4 GHz band")


def convert_freq_to_channel(center_freq_mhz):
    if 2407 <= center_freq_mhz <= 2484:  # Valid range for 2.4 GHz Wi-Fi channels 1-14
        return (center_freq_mhz - 2407) // 5
    else:
        raise ValueError(
            "Frequency is out of range for channels 1-14 in the 2.4 GHz band")

# Define a function to parse the Radiotap header


def parse_radiotap(raw_packet):
    # Parse the packet using the defined structure
    header_length, parsed_header = radiotap.radiotap_parse(raw_packet)
    chan_freq = parsed_header.get("chan_freq")
    chan_flags = parsed_header.get("chan_flags")
    if chan_flags is not None and chan_freq is not None:
        parsed_header["channel"] = convert_freq_to_channel(chan_freq)
    # The actual packet data starts after the Radiotap header
    packet_data = raw_packet[header_length:]

    return parsed_header, packet_data
