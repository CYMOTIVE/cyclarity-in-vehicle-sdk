from construct import (
    this,
    Const,
    Adapter,
    Enum as ConEnum,
    Array,
    Struct,
    Int64ul,
    Int32ub,
    Int32ul,
    Int16ub,
    Int16ul,
    BytesInteger,
    Byte,
    Bytes,
    GreedyBytes,
    GreedyRange,
    BitsSwapped,
    BitStruct,
    BitsInteger,
    Flag,
    If,
    IfThenElse,
    Switch,
    Computed,
    ConstructError,
)


class SwapBitsAdapter(Adapter):
    def _flip_bits(self, value: int, num_bits) -> int:
        # Reverse the bit order (swap bits)
        return int(f'{value:0{num_bits}b}'[::-1], 2)

    def _decode(self, obj, context, path):
        return self._flip_bits(obj, self.subcon.sizeof())

    def _encode(self, obj, context, path):
        return self._flip_bits(obj, self.subcon.sizeof())


class MacAddressAdapter(Adapter):
    def _decode(self, obj, context, path):
        # Format the sequence of bytes as a MAC address string
        return ':'.join(format(b, '02x') for b in obj)

    def _encode(self, obj, context, path):
        # Convert the MAC address string back into bytes
        return bytes(int(b, 16) for b in obj.split(':'))


# Use the MacAddressAdapter with an array of 6 bytes to represent the MAC address
AddressField = MacAddressAdapter(Array(6, Byte))


class RateAdapter(Adapter):
    def _decode(self, obj, context, path):
        # Clear the MSB to get the rate and then divide by 2 to get the Mbps value
        rate_mbps = (obj & 0x7F) / 2.0
        # Check if the MSB is set to identify if it's a basic rate
        is_basic_rate = bool(obj & 0x80)
        return (rate_mbps, is_basic_rate)

    def _encode(self, obj, context, path):
        # Combine the Mbps rate value with the basic rate flag
        rate_raw = int(obj[0] * 2)
        if obj[1]:  # If it's a basic rate, set the MSB
            rate_raw |= 0x80
        return rate_raw

class FallbackStringAdapter(Adapter):  
    def __init__(self, length, encodings=["utf-8", "utf-16-le", "utf-16-be"], allow_bytestring=True):  
        super().__init__(Bytes(length))  
        self.length = length
        self.encodings = encodings
  
    def _decode(self, obj, context, path):  
        for encoding in self.encodings:
            try:  
                return obj.decode(encoding)
            except UnicodeDecodeError:  
                pass

        if self.allow_bytestring:
            return obj
        
        raise ConstructError(f"Object cannot be decoded with any of {self.encodings}")  
  
    def _encode(self, obj, context, path):  
        if isinstance(obj, bytes):
            return obj
        
        length = self.length(context) if callable(self.length) else self.length

        for encoding in self.encodings:
            try:  
                s = obj.encode(encoding)  
                if len(s) == length:
                    return s
            except UnicodeEncodeError:  
                pass

        raise ConstructError(f"Object cannot be encoded with any of {self.encodings}")  

    #def _build(self, obj, stream, context, path):
    #    obj2 = self._encode(obj, context, path)
    #    buildret = self.subcon._build(obj2, stream, context, path)
    #    return buildret

FrameType = ConEnum(
    SwapBitsAdapter(BitsInteger(2)),
    MANAGEMENT=0,
    CONTROL=1,
    DATA=2,
    EXTENSION=3,
)

# Define Enums for subtypes of management, control, and data frames
ManagementSubtype = ConEnum(
    SwapBitsAdapter(BitsInteger(4)),
    ASSOCIATION_REQUEST=0,
    ASSOCIATION_RESPONSE=1,
    REASSOCIATION_REQUEST=2,
    REASSOCIATION_RESPONSE=3,
    PROBE_REQUEST=4,
    PROBE_RESPONSE=5,
    TIMING_ADVERTISEMENT=6,
    RESERVED1=7,
    BEACON=8,
    ATIM=9,
    DISASSOCIATION=10,
    AUTHENTICATION=11,
    DEAUTHENTICATION=12,
    ACTION=13,
    ACTION_NO_ACK=14,
    RESERVED2=15,
)

# Placeholder for control subtypes (control frames are not expanded in this example)
ControlSubtype = ConEnum(
    SwapBitsAdapter(BitsInteger(4)),
    RESERVED0=0,
    RESERVED1=1,
    TRIGGER=2,
    TACK=3,
    BEAMFORMING_REPORT_POLL=4,
    VHT_NDP_ANNOUNCEMENT=5,
    CONTROL_FRAME_EXTENSION=6,
    CONTROL_WRAPPER=7,
    BLOCK_ACK_REQUEST=8,
    BLOCK_ACK=9,
    PS_POLL=10,
    RTS=11,
    CTS=12,
    ACK=13,
    CF_END=14,
    CF_END_CF_ACK=15,
)

# Placeholder for data subtypes (data frames are not expanded in this example)
DataSubtype = ConEnum(
    SwapBitsAdapter(BitsInteger(4)),
    DATA=0,
    DATA_CF_ACK=1,
    DATA_CF_POLL=2,
    DATA_CF_ACK_CF_POLL=3,
    NULL_FUNCTION=4,
    CF_ACK=5,
    CF_POLL=6,
    CF_ACK_CF_POLL=7,
    QOS_DATA=8,
    QOS_DATA_CF_ACK=9,
    QOS_DATA_CF_POLL=10,
    QOS_DATA_CF_ACK_CF_POLL=11,
    QOS_NULL=12,
    RESERVED_13=13,
    QOS_CF_POLL_NO_DATA=14,
    QOS_CF_ACK_CF_POLL_NO_DATA=15,
)

ExtensionSubtype = ConEnum(
    SwapBitsAdapter(BitsInteger(4)),
    DMG_BEACON=0,
    S1G_BEACON=1,
    RESERVED_2=2,
    RESERVED_3=3,
    RESERVED_4=4,
    RESERVED_5=5,
    RESERVED_6=6,
    RESERVED_7=7,
    RESERVED_8=8,
    RESERVED_9=9,
    RESERVED_10=10,
    RESERVED_11=11,
    RESERVED_12=12,
    RESERVED_13=13,
    RESERVED_14=14,
    RESERVED_15=15,
)

VendorOui = ConEnum(
    BytesInteger(3),
    IEEE=0x000FAC,
    MICROSOFT_CORP=0x0050f2,
    __default__=lambda v: v,
)

# Define the Capability Information structure
CapabilityInfo = BitsSwapped(BitStruct(
    "ess" / Flag,
    "ibss" / Flag,
    "cf_pollable" / Flag,
    "cf_poll_request" / Flag,
    "privacy" / Flag,
    "short_preamble" / Flag,
    "pbcc" / Flag,
    "channel_agility" / Flag,
    "spectrum_management" / Flag,
    "qos" / Flag,
    "short_slot_time" / Flag,
    "apsd" / Flag,
    "radio_measurement" / Flag,
    "dsss_ofdm" / Flag,
    "delayed_block_ack" / Flag,
    "immediate_block_ack" / Flag,
))

IEType = ConEnum(
    Byte,
    SSID=0,
    SUPPORTED_RATES=1,
    FH_PARAMETER_SET=2,
    DS_PARAMETER_SET=3,
    CF_PARAMETER_SET=4,
    TIM=5,
    IBSS_PARAMETER_SET=6,
    COUNTRY=7,
    REQUEST=10,
    BSS_LOAD=11,
    EDCA_PARAMETER_SET=12,
    TSPEC=13,
    TCLAS=14,
    SCHEDULE=15,
    CHALLENGE_TEXT=16,
    POWER_CONSTRAINT=32,
    POWER_CAPABILITY=33,
    TPC_REQUEST=34,
    TPC_REPORT=35,
    SUPPORTED_CHANNELS=36,
    CHANNEL_SWITCH_ANNOUNCEMENT=37,
    MEASUREMENT_REQUEST=38,
    MEASUREMENT_REPORT=39,
    QUIET=40,
    IBSS_DFS=41,
    ERP_INFO=42,
    TS_DELAY=43,
    TCLAS_PROCESSING=44,
    HT_CAPABILITIES=45,
    QOS_CAPABILITY=46,
    RESURVED_47=47,
    RSN=48,
    # ...
    EXTENDED_SUPPORTED_RATES=50,
    # ...
    RSNI=65,
    # ...
    SSID_LIST=84,
    # ...
    INTERNETWORKING=107,
    # ...
    EXTENDED_CAPABILITIES=127,
    # ...
    VENDOR_SPECIFIC=221,
    # ...
    RSN_EXTENSION=244,
    # ... add other IE types as needed
    # Refer to the 802.11 standard for a complete list of IE types
    EXTENDED_ID=255,
)
repeating_element_types = [
    IEType.VENDOR_SPECIFIC, 
    IEType.EXTENDED_ID, 
    IEType.INTERNETWORKING,
    IEType.EXTENDED_CAPABILITIES,
]

# Define parsers for different types of Information Elements
ssid_element = Struct(
    "ssid" / FallbackStringAdapter(this._.len)
)

supported_rates_element = Struct(
    "rates" / Array(this._.len, RateAdapter(Byte))
)

# ...

SsidElement = Struct(
    "id" / Const(IEType.SSID, IEType),
    "len" / Byte,
    "ssid" / FallbackStringAdapter(this.len),
)

ssid_list_element = Struct(
    "ssid_list" / GreedyRange(SsidElement)
)

# ...

fh_parameter_set_element = Struct(
    "dwell_time" / Int16ub,
    "hop_set" / Byte,
    "hop_pattern" / Byte,
    "hop_index" / Byte,
)

ds_parameter_set_element = Struct(
    "current_channel" / Byte,
)

cf_parameter_set_element = Struct(
    "cfp_count" / Byte,
    "cfp_period" / Byte,
    "cfp_max_duration" / Int16ub,
    "cfp_dur_remaining" / Int16ub,
)

ibss_parameter_set_element = Struct(
    "atim_window" / Int16ub,
)

country_element = Struct(
    "country_string" / Bytes(3),
    "country_info" / Array((this._.len-3)//3, Struct(
        "first_channel_number" / Byte,
        "number_of_channels" / Byte,
        "max_transmit_power_level" / Byte,
    )),
)

request_element = Struct(
    "requested_info_elems" / Array(this.len, Byte)
)

bss_load_element = Struct(
    "station_count" / Int16ub,
    "channel_utilization" / Byte,
    "available_admission_capacity" / Int16ub
)

AKMSuites = ConEnum(
    Int32ub,
    IEEE_RESERVED=0x000FAC_00,
    IEEE_8021X=0x000FAC_01,  # WPA/WPA2 Enterprise, requires RADIUS authentication
    IEEE_PSK=0x000FAC_02,  # WPA/WPA2 Personal, uses a pre-shared key
    IEEE_FT_8021X=0x000FAC_03,  # Fast BSS Transition (802.11r) using 802.1X
    IEEE_FT_PSK=0x000FAC_04,  # Fast BSS Transition using Pre-Shared Key
    IEEE_8021X_SHA256=0x000FAC_05,  # 802.1X using SHA-256
    IEEE_PSK_SHA256=0x000FAC_06,  # Pre-Shared Key using SHA-256
    IEEE_TDLS=0x000FAC_07,  # Tunneled Direct Link Setup
    IEEE_SAE=0x000FAC_08,  # Simultaneous Authentication of Equals
    IEEE_FT_SAE=0x000FAC_09,  # Fast BSS Transition with SAE
    IEEE_AP_PEER_KEY=0x000FAC_0A,  # AP Peer Key
    IEEE_8021X_SUITE_B=0x000FAC_0B,  # 802.1X Suite B
    IEEE_8021X_SUITE_B_192=0x000FAC_0C,  # 802.1X Suite B (192-bit)
    IEEE_FILS_SHA256=0x000FAC_0D,  # Fast Initial Link Setup with SHA-256
    IEEE_FILS_SHA384=0x000FAC_0E,  # Fast Initial Link Setup with SHA-384
    IEEE_FT_FILS_SHA256=0x000FAC_0F,  # Fast BSS Transition with FILS SHA-256
    IEEE_FT_FILS_SHA384=0x000FAC_10,  # Fast BSS Transition with FILS SHA-384
    IEEE_OWE=0x000FAC_11,  # Opportunistic Wireless Encryption
    __default__=lambda v: v
)

RSNCipherSuites = ConEnum(
    Int32ub,
    IEEE_WEP40=0x000FAC_01,
    IEEE_TKIP=0x000FAC_02,
    IEEE_CCMP=0x000FAC_04,
    IEEE_WEP104=0x000FAC_05,
    IEEE_BIP_CMAC_128=0x000FAC_06,
    IEEE_GCMP_128=0x000FAC_08,
    IEEE_GCMP_256=0x000FAC_09,
    IEEE_CCMP_256=0x000FAC_0A,
    IEEE_BIP_GMAC_128=0x000FAC_0B,
    IEEE_BIP_GMAC_256=0x000FAC_0C,
    IEEE_BIP_CMAC_256=0x000FAC_0D,
    __default__=lambda v: f"UNKNOWN_CIPHER_{v>>8:06X}:{v&0xff}"
)

rsn_capabilities = BitStruct(
    "PreAuthentication" / Flag,
    "NoPairwise" / Flag,
    "PTKSAReplayCounter" / BitsInteger(2),
    "GTKSAReplayCounter" / BitsInteger(2),
    "ManagementFrameProtectionRequired" / Flag,
    "ManagementFrameProtectionCapable" / Flag,
    "JointMultiBandRSNA" / Flag,
    "PeerKeyEnabled" / Flag,
    "SPPAMSDUCapable" / Flag,
    "SPPAMSDURequired" / Flag,
    "PBAC" / Flag,
    "ExtendedKeyIDForUnicast" / Flag,
    "OCVC" / Flag,
    "Resurved" / Flag,
)

rsn_element = Struct(
    "Version" / Int16ul,
    "GroupCipherSuite" / RSNCipherSuites,
    "PairwiseCipherSuiteCount" /
    IfThenElse(this._.len >= 8, Int16ul, Computed(0)),
    "PairwiseCipherSuites" /
    Array(this.PairwiseCipherSuiteCount, RSNCipherSuites),
    "AKMSuiteCount" / IfThenElse(this._.len >= 10 +
                                 this.PairwiseCipherSuiteCount * 4, Int16ul, Computed(0)),
    "AKMSuites" / Array(this.AKMSuiteCount, AKMSuites),
    "RSNCapabilities" / If(this._.len >= 12 + this.PairwiseCipherSuiteCount * 4 + this.AKMSuiteCount * 4,
                           rsn_capabilities),
    "PMKIDCount" / IfThenElse(this._.len >= 14 + this.PairwiseCipherSuiteCount *
                              4 + this.AKMSuiteCount * 4, Int16ul, Computed(0)),
    "PMKIDs" / Array(this.PMKIDCount, Bytes(16)),
    "GroupManagmentCipherSuite" / If(this._.len >= 18 + this.PairwiseCipherSuiteCount *
                                     4 + this.AKMSuiteCount * 4 + this.PMKIDCount * 16, RSNCipherSuites),
)

# ...

rsni_element = Struct(
    "rsni" / Byte,
)

# ...

# Define the HT Capabilities Info sub-structure
ht_capabilities_info = BitStruct(
    "ldpc_coding_capability" / Flag,
    "supported_channel_width_set" / Flag,
    "sm_power_save" / BitsInteger(2),
    "ht_greenfield" / Flag,
    "short_gi_for_20mhz" / Flag,
    "short_gi_for_40mhz" / Flag,
    "tx_stbc" / Flag,
    "rx_stbc" / BitsInteger(2),
    "ht_delayed_block_ack" / Flag,
    "max_amsdu_length" / Flag,
    "dsss_cck_mode_40mhz" / Flag,
    "psmp_support" / Flag,
    "forty_mhz_intolerant" / Flag,
    "lsig_txop_protection" / Flag,
)

# Define the A-MPDU Parameters sub-structure
a_mpdu_parameters = Struct(
    "max_ampdu_length_exponent" / BitsInteger(2),
    "min_mpdu_start_spacing" / BitsInteger(3),
    "resurved" / BitsInteger(3),
)

# Define the HT Capabilities IE parser
ht_capabilities_element = Struct(
    "ht_capabilities_info" / ht_capabilities_info,
    "a_mpdu_parameters" / a_mpdu_parameters,
    "supported_mcs_set" / Array(16, Byte),  # 128 bits represented as 16 bytes
    # Other fields would be added here based on the 802.11 specification
)

# ...

rsn_extension_element = Struct(
    "rsn_extended_capabilities" / BitStruct(
        "len" / BitsInteger(4),
        "protected_twt_operation_support" / Flag,
        "sae_hash_to_element" / Flag,
        "resurved_6" / Flag,
        "resurved_7" / Flag,
        "resurved_8" / Array(this._.len-1, Byte),
    ),
)

# ...

MicrosoftSpecificElementType = ConEnum(
    Byte,
    WPA=1,
    __default__=lambda v: v
)

vendor_specific_content = {
    VendorOui.MICROSOFT_CORP: Struct(
        "type" / MicrosoftSpecificElementType,
        "other_fields" / Bytes(this._._.len - 4),
    )
}

vendor_specific_element = Struct(
    # Typically the first 3 bytes are the Organizationally Unique Identifier (OUI)
    "oui" / VendorOui,
    # The rest is vendor-specific content
    "vendor_specific_content" / \
    Switch(this.oui, vendor_specific_content, Bytes(this._.len - 3))
)

# ... add other parsers

# Update the ie_elements dictionary with the additional parsers
ie_elements = {
    IEType.SSID: ssid_element,
    IEType.SUPPORTED_RATES: supported_rates_element,
    IEType.FH_PARAMETER_SET: fh_parameter_set_element,
    IEType.DS_PARAMETER_SET: ds_parameter_set_element,
    IEType.CF_PARAMETER_SET: cf_parameter_set_element,
    IEType.IBSS_PARAMETER_SET: ibss_parameter_set_element,
    IEType.COUNTRY: country_element,
    IEType.REQUEST: request_element,
    IEType.BSS_LOAD: bss_load_element,
    IEType.RSN: rsn_element,
    # ... add other cases for different IE types based on their IDs
    # IEType.HT_CAPABILITIES: ht_capabilities_element,
    # ...
    IEType.RSNI: rsni_element,
    # ... add other cases for different IE types based on their IDs
    IEType.EXTENDED_SUPPORTED_RATES: supported_rates_element,
    # ... add other cases for different IE types based on their IDs
    # IEType.SSID_LIST: ssid_list_element,
    # ...
    IEType.RSN_EXTENSION: rsn_extension_element,
    # ... add other cases for different IE types based on their IDs
    IEType.VENDOR_SPECIFIC: vendor_specific_element,
    # ... add other cases for different IE types based on their IDs
}

# Add more specific IE parsers as needed...

# Define the Information Element (IE) parser with a Switch
InformationElement = Struct(
    "id" / IEType,
    "len" / Byte,
    "id_extension" / If(this.id == IEType.EXTENDED_ID, Byte),
    "info" / If(this.len > 0, IfThenElse(this.id == IEType.EXTENDED_ID,
                                         Bytes(this.len-1),
                                         Switch(this.id, ie_elements,
                                         default=Bytes(this.len))
                                         ),  # Use a default case for unknown or unhandled IEs
                ),
)

VendorSpecificElement = Struct(
    "id" / Byte,
    "len" / Byte,
    "content" / Bytes(this.len),
)

# Define a generic structure to parse multiple IEs
InformationElements = GreedyRange(InformationElement)

QoSControl = BitStruct(
    "tid" / BitsInteger(4),  # Traffic Identifier
    "eos" / Flag,            # End of Service Period
    "ack_policy" / BitsInteger(2),
    "amsdu_present" / Flag,
    "txop_dur_req" / BitsInteger(8),
)

DataFrameHeader = Struct(
    "address4" / If(this._._.frame_control.to_ds &
                    this._._.frame_control.from_ds, AddressField),
    "qos_control" / If(this._._.frame_control.subtype >=
                       DataSubtype.QOS_DATA, QoSControl),
    # Assuming 32-bit HT Control field
    "ht_control" / If(this._._.frame_control.subtype >=
                      DataSubtype.QOS_DATA and this._._.frame_control.order_or_pHTC, Int32ul),
)

# Define parsers for each management frame subtype
management_subtype_parsers = {
    ManagementSubtype.ASSOCIATION_REQUEST: Struct(
        "capability_info" / CapabilityInfo,
        "listen_interval" / Int16ul,
        "information_elements" / InformationElements,
    ),
    ManagementSubtype.ASSOCIATION_RESPONSE: Struct(
        "capability_info" / CapabilityInfo,
        "status_code" / Int16ul,
        "association_id" / Int16ul,
        "information_elements" / InformationElements,
    ),
    ManagementSubtype.REASSOCIATION_REQUEST: Struct(
        "capability_info" / CapabilityInfo,
        "listen_interval" / Int16ul,
        "current_ap_address" / AddressField,
        "information_elements" / InformationElements,
    ),
    ManagementSubtype.REASSOCIATION_RESPONSE: Struct(
        "capability_info" / CapabilityInfo,
        "status_code" / Int16ul,
        "association_id" / Int16ul,
        "information_elements" / InformationElements,
    ),
    ManagementSubtype.PROBE_REQUEST: Struct(
        "information_elements" / InformationElements,
    ),
    ManagementSubtype.PROBE_RESPONSE: Struct(
        "timestamp" / Int64ul,
        "beacon_interval" / Int16ul,
        "capability_info" / CapabilityInfo,
        "information_elements" / InformationElements,
    ),
    ManagementSubtype.BEACON: Struct(
        "timestamp" / Int64ul,
        "beacon_interval" / Int16ul,
        "capability_info" / CapabilityInfo,
        "information_elements" / InformationElements,
        "MME" / GreedyBytes,
    ),
    ManagementSubtype.DISASSOCIATION: Struct(
        "reason_code" / Int16ul,
        "vendor_specific_elements" / GreedyRange(VendorSpecificElement),
        "MME" / GreedyBytes,
    ),
    ManagementSubtype.AUTHENTICATION: Struct(
        "auth_algorithm_number" / Int16ul,
        "auth_transaction_sequence_number" / Int16ul,
        "status_code" / Int16ul,
        "challenge_text" / GreedyBytes,
    ),
    ManagementSubtype.DEAUTHENTICATION: Struct(
        "reason_code" / Int16ul,
        "vendor_specific_elements" / GreedyRange(VendorSpecificElement),
        "MME" / GreedyBytes,
    ),
    ManagementSubtype.ACTION: Struct(
        "category" / Byte,
        "action_details" / GreedyBytes,
    ),
    ManagementSubtype.ACTION_NO_ACK: Struct(
        "category" / Byte,
        "action_details" / GreedyBytes,
    ),
    # Additional subtypes, if defined, would go here.
}

# Data frame structure that includes a data body
DataFrameWithBody = Struct(
    "header" / DataFrameHeader,
    "data" / GreedyBytes,
)

# Data frame structure that does not include a data body (e.g., for null or control frames)
DataFrameWithoutBody = Struct(
    "header" / DataFrameHeader,
)

# Now map the subtypes to the appropriate structures using the refactored structures
data_subtype_parsers = {
    DataSubtype.DATA: DataFrameWithBody,
    DataSubtype.DATA_CF_ACK: DataFrameWithBody,
    DataSubtype.DATA_CF_POLL: DataFrameWithBody,
    DataSubtype.DATA_CF_ACK_CF_POLL: DataFrameWithBody,
    DataSubtype.NULL_FUNCTION: DataFrameWithoutBody,
    DataSubtype.CF_ACK: DataFrameWithoutBody,
    DataSubtype.CF_POLL: DataFrameWithoutBody,
    DataSubtype.CF_ACK_CF_POLL: DataFrameWithoutBody,
    DataSubtype.QOS_DATA: DataFrameWithBody,
    DataSubtype.QOS_DATA_CF_ACK: DataFrameWithBody,
    DataSubtype.QOS_DATA_CF_POLL: DataFrameWithBody,
    DataSubtype.QOS_DATA_CF_ACK_CF_POLL: DataFrameWithBody,
    DataSubtype.QOS_NULL: DataFrameWithoutBody,
    DataSubtype.RESERVED_13: GreedyBytes,  # Reserved subtype, no specific structure
    DataSubtype.QOS_CF_POLL_NO_DATA: DataFrameWithoutBody,
    DataSubtype.QOS_CF_ACK_CF_POLL_NO_DATA: DataFrameWithoutBody,
}

frame_type_parsers = {
    # Management frame types (subtype-specific parsing would go here)
    FrameType.MANAGEMENT: Switch(
        this.frame_control.subtype,  # Based on subtype
        management_subtype_parsers,
        default=GreedyBytes,  # Default case if subtype is not found
    ),
    # Control frame types (simplified)
    FrameType.CONTROL: Struct(
        "control_frame" / GreedyBytes,  # Simplified control frame structure
    ),
    # Data frame types (simplified)
    FrameType.DATA: Switch(
        this.frame_control.subtype,  # Based on subtype
        data_subtype_parsers,
        default=GreedyBytes,  # Default case if subtype is not found
    ),
}

FrameControl = BitsSwapped(BitStruct(
    "protocol_version" / SwapBitsAdapter(BitsInteger(2)),
    "type" / FrameType,
    "subtype" / Switch(this.type, {
        FrameType.MANAGEMENT: ManagementSubtype,
        FrameType.CONTROL: ControlSubtype,
        FrameType.DATA: DataSubtype,
        FrameType.EXTENSION: ExtensionSubtype,
    }),
    "to_ds" / Flag,
    "from_ds" / Flag,
    "more_fragments" / Flag,
    "retry" / Flag,
    "power_management" / Flag,
    "more_data" / Flag,
    "protected_frame" / Flag,
    "order_or_pHTC" / Flag,
))

# Define the structure of a common 802.11 frame header
wifi_frame_header = Struct(
    "frame_control" / FrameControl,
    "duration_id" / Int16ul,
    "address1" / AddressField,
    "address2" / If(this.frame_control.type !=
                    FrameType.CONTROL, AddressField),
    "address3" / If(this.frame_control.type !=
                    FrameType.CONTROL, AddressField),
    "control_data" / If(this.frame_control.type ==
                        FrameType.CONTROL, GreedyBytes),
    "sequence_control" / If(this.frame_control.type != FrameType.CONTROL, BitsSwapped(BitStruct(
        "fragment_number" / SwapBitsAdapter(BitsInteger(4)),
        "sequence_number" / SwapBitsAdapter(BitsInteger(12)),
    ))),
    "frame_body" / If(this.frame_control.type != FrameType.CONTROL, Switch(
        this.frame_control.type,
        frame_type_parsers,
        default=GreedyBytes,
    )),
)
