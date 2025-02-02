from scapy.all import *
from scapy.layers.inet6 import IP6Field
import ctypes
import collections
from .SOMEIP import SOMEIP


class _SDPacketBase(Packet):
    """ base class to be used among all SD Packet definitions."""
    # use this dictionary to set default values for desired fields (mostly on subclasses
    # where not all fields are defined locally)
    # - key : field_name, value : desired value
    # - it will be used from 'init_fields' function, upon packet initialization
    #
    # example : _defaults = {'field_1_name':field_1_value,'field_2_name':field_2_value}
    _defaults = {}

    def _set_defaults(self):
        """ goes through '_defaults' dict setting field default values (for those that have been defined)."""
        for key in self._defaults.keys():
            try:
                self.get_field(key)
            except KeyError:
                pass
            else:
                self.setfieldval(key, self._defaults[key])

    def init_fields(self):
        """ perform initialization of packet fields with desired values.
            NOTE : this funtion will only be called *once* upon class (or subclass) construction
        """
        Packet.init_fields(self)
        self._set_defaults()


# SD ENTRY
#  - Service
#  - EventGroup
class _SDEntry(_SDPacketBase):
    """ Base class for SDEntry_* packages."""
    TYPE_FMT = ">B"
    TYPE_PAYLOAD_I = 0
    # ENTRY TYPES : SERVICE
    TYPE_SRV_FINDSERVICE = 0x00
    TYPE_SRV_OFFERSERVICE = 0x01
    TYPE_SRV = (TYPE_SRV_FINDSERVICE, TYPE_SRV_OFFERSERVICE)
    # ENTRY TYPES : EVENGROUP
    TYPE_EVTGRP_SUBSCRIBE = 0x06
    TYPE_EVTGRP_SUBSCRIBE_ACK = 0x07
    TYPE_EVTGRP = (TYPE_EVTGRP_SUBSCRIBE, TYPE_EVTGRP_SUBSCRIBE_ACK)
    # overall len (UT usage)
    OVERALL_LEN = 16

    # fields_desc = [
    #     ByteField("type", 0),       # Type Field[8bit]                  用于表明Entry Type
    #     ByteField("index_1", 0),    # Index First Option Run[8bit]      在option array中运行的第一个选项的index
    #     ByteField("index_2", 0),    # Index Second Option Run[8bit]     在option array中运行的第二个选项的index
    #     BitField("n_opt_1", 0, 4),  # Number of Options 1[4bit]         第一个option array的数量
    #     BitField("n_opt_2", 0, 4),  # Number of Options 2[4bit]         第二个option array的数量
    #     ShortField("srv_id", 0),    # Service-ID[16bit]
    #     ShortField("inst_id", 0),   # Instance ID[16bit]
    #     ByteField("major_ver", 0),  # Major Version[8bit]               解码service instance的主要版本
    #     X3BytesField("ttl", 0)]     # TTL[24bit]                        以秒为单位的生命周期

    def guess_payload_class(self, payload):
        """ decode SDEntry depending on its type."""
        pl_type = struct.unpack(_SDEntry.TYPE_FMT, payload[_SDEntry.TYPE_PAYLOAD_I:_SDEntry.TYPE_PAYLOAD_I+1])[0]
        if pl_type in _SDEntry.TYPE_SRV:
            return SDEntry_Service
        elif pl_type in _SDEntry.TYPE_EVTGRP:
            return SDEntry_EventGroup


class SDEntry_Service(_SDEntry):
    """ Service Entry."""
    _defaults = {"type": _SDEntry.TYPE_SRV_FINDSERVICE}

    name = "Service Entry"
    fields_desc = [
        ByteField("type", 0),  # Type Field[8bit]                  用于表明Entry Type
        ByteField("index_1", 0),  # Index First Option Run[8bit]      在option array中运行的第一个选项的index
        ByteField("index_2", 0),  # Index Second Option Run[8bit]     在option array中运行的第二个选项的index
        BitField("n_opt_1", 0, 4),  # Number of Options 1[4bit]         第一个option array的数量
        BitField("n_opt_2", 0, 4),  # Number of Options 2[4bit]         第二个option array的数量
        ShortField("srv_id", 0),  # Service-ID[16bit]
        ShortField("inst_id", 0),  # Instance ID[16bit]
        ByteField("major_ver", 0),  # Major Version[8bit]               解码service instance的主要版本
        X3BytesField("ttl", 0),  # TTL[24bit]                        以秒为单位的生命周期
        IntField("minor_ver", 0)]   # Minor Version[32bit]            解码service instance的次要版本


class SDEntry_EventGroup(_SDEntry):
    """ EventGroup Entry."""
    _defaults = {"type": _SDEntry.TYPE_EVTGRP_SUBSCRIBE}

    name = "Eventgroup Entry"
    fields_desc = [
        ByteField("type", 0),  # Type Field[8bit]                  用于表明Entry Type
        ByteField("index_1", 0),  # Index First Option Run[8bit]      在option array中运行的第一个选项的index
        ByteField("index_2", 0),  # Index Second Option Run[8bit]     在option array中运行的第二个选项的index
        BitField("n_opt_1", 0, 4),  # Number of Options 1[4bit]         第一个option array的数量
        BitField("n_opt_2", 0, 4),  # Number of Options 2[4bit]         第二个option array的数量
        ShortField("srv_id", 0),  # Service-ID[16bit]
        ShortField("inst_id", 0),  # Instance ID[16bit]
        ByteField("major_ver", 0),  # Major Version[8bit]               解码service instance的主要版本
        X3BytesField("ttl", 0),  # TTL[24bit]                        以秒为单位的生命周期
        BitField("res", 0, 12),             # Reserved[12bit]
        BitField("cnt", 0, 4),              # Counter[4bit]         用于区分同一订阅者相同的subscribe eventgroups (only difference in endpoint)
        ShortField("eventgroup_id", 0)]     # Eventgroup ID[16bit]  传输Eventgroup的ID


# SD Option
#  - Configuration
#  - LoadBalancing
#  - IPv4 EndPoint
#  - IPv6 EndPoint
#  - IPv4 MultiCast
#  - IPv6 MultiCast
#  - IPv4 EndPoint
#  - IPv6 EndPoint
class _SDOption(_SDPacketBase):
    """ Base class for SDOption_* packages."""
    TYPE_FMT = ">B"
    TYPE_PAYLOAD_I = 2

    CFG_TYPE = 0x01                 # TYPE: configuration option
    CFG_OVERALL_LEN = 4             # overall length of CFG SDOption,empty 'cfg_str' (to be used from UT)
    LOADBALANCE_TYPE = 0x02         # TYPE: load balancing option
    LOADBALANCE_LEN = 0x05          # Length[16bit]
    LOADBALANCE_OVERALL_LEN = 8     # overall length of LB SDOption (to be used from UT)
    IP4_ENDPOINT_TYPE = 0x04        # TYPE: IPv4 Endpoint Option
    IP4_ENDPOINT_LEN = 0x0009       # Length[16bit]
    IP4_MCAST_TYPE = 0x14           # TYPE: IPv4 Multicast Option
    IP4_MCAST_LEN = 0x0009          # Length[16bit]
    IP4_SDENDPOINT_TYPE = 0x24      # TYPE: IPv4 SD Endpoint Option
    IP4_SDENDPOINT_LEN = 0x0009     # Length[16bit]
    IP4_OVERALL_LEN = 12            # overall length of IP4 SDOption (to be used from UT)
    IP6_ENDPOINT_TYPE = 0x06        # TYPE: IPv6 Endpoint Option
    IP6_ENDPOINT_LEN = 0x0015       # Length[16bit]
    IP6_MCAST_TYPE = 0x16           # TYPE: IPv6 Multicast Option
    IP6_MCAST_LEN = 0x0015          # Length[16bit]
    IP6_SDENDPOINT_TYPE = 0x26      # TYPE: IPv6 SD Endpoint Option
    IP6_SDENDPOINT_LEN = 0x0015     # Length[16bit]
    IP6_OVERALL_LEN = 24            # overall length of IP6 SDOption (to be used from UT)

    def guess_payload_class(self, payload):
        """ decode SDOption depending on its type."""
        pl_type = struct.unpack(_SDOption.TYPE_FMT, payload[_SDOption.TYPE_PAYLOAD_I:_SDOption.TYPE_PAYLOAD_I+1])[0]

        if pl_type == _SDOption.CFG_TYPE:
            return SDOption_Config
        elif pl_type == self.LOADBALANCE_TYPE:
            return SDOption_LoadBalance
        elif pl_type == self.IP4_ENDPOINT_TYPE:
            return SDOption_IP4_EndPoint
        elif pl_type == self.IP4_MCAST_TYPE:
            return SDOption_IP4_Multicast
        elif pl_type == self.IP4_SDENDPOINT_TYPE:
            return SDOption_IP4_SD_EndPoint
        elif pl_type == self.IP6_ENDPOINT_TYPE:
            return SDOption_IP6_EndPoint
        elif pl_type == self.IP6_MCAST_TYPE:
            return SDOption_IP6_Multicast
        elif pl_type == self.IP6_SDENDPOINT_TYPE:
            return SDOption_IP6_SD_EndPoint


class _SDOption_Header(_SDOption):
    fields_desc = [
        ShortField("len", None),    # Length    从Reserved开始到Option结束的长度
        ByteField("type", 0),       # Type      用于判断Option的格式
        ByteField("res_hdr", 0)]    # Reserved  应该设置为0x00


class _SDOption_Tail(_SDOption):
    fields_desc = [
        ByteField("res_tail", 0),                                           # Reserved                  应该设置为0x00
        ByteEnumField("l4_proto", 0x06, {0x06: "TCP", 0x11: "UDP"}),        # Transport Protocol[8bit]  用于判断传输层协议
        ShortField("port", 0)]                                              # Transport Protocol Port Number[16bit]


class _SDOption_IP4(_SDOption):
    fields_desc = [
        _SDOption_Header,
        IPField("addr", "0.0.0.0"),
        _SDOption_Tail]


class _SDOption_IP6(_SDOption):
    fields_desc = [
        _SDOption_Header,
        IP6Field("addr", "2001:cdba:0000:0000:0000:0000:3257:9652"),
        _SDOption_Tail]


class SDOption_Config(_SDOption):
    # offset to be added upon length calculation (corresponding to header's "Reserved" field)
    LEN_OFFSET = 0x01

    name = "Config Option"
    # default values specification
    _defaults = {'type': _SDOption.CFG_TYPE}
    # package fields definiton
    fields_desc = [
        _SDOption_Header,
        StrField("cfg_str", "")]

    def post_build(self, p, pay):
        # length computation excluding 16b_length and 8b_type
        l = self.len
        if l is None:
            l = len(self.cfg_str) + self.LEN_OFFSET
            p = struct.pack("!H", l) + p[2:]
        return p + pay


class SDOption_LoadBalance(_SDOption):
    name = "LoadBalance Option"
    # default values specification
    _defaults = {'type': _SDOption.LOADBALANCE_TYPE,
                 'len': _SDOption.LOADBALANCE_LEN}
    # package fields definiton
    fields_desc = [
        _SDOption_Header,
        ShortField("priority", 0),      # Priority[16bit]   值越低优先级越高
        ShortField("weight", 0)]        # Weight[16bit]     值越大表明越有可能被选中


# SDOPTIONS : IPv4-specific
class SDOption_IP4_EndPoint(_SDOption_IP4):
    name = "IP4 EndPoint Option"
    # default values specification
    _defaults = {'type': _SDOption.IP4_ENDPOINT_TYPE, 'len': _SDOption.IP4_ENDPOINT_LEN}


class SDOption_IP4_Multicast(_SDOption_IP4):
    name = "IP4 Multicast Option"
    # default values specification
    _defaults = {'type': _SDOption.IP4_MCAST_TYPE, 'len': _SDOption.IP4_MCAST_LEN}


class SDOption_IP4_SD_EndPoint(_SDOption_IP4):
    name = "IP4 SDEndPoint Option"
    # default values specification
    _defaults = {'type': _SDOption.IP4_SDENDPOINT_TYPE, 'len': _SDOption.IP4_SDENDPOINT_LEN}


# SDOPTIONS : IPv6-specific
class SDOption_IP6_EndPoint(_SDOption_IP6):
    name = "IP6 EndPoint Option"
    # default values specification
    _defaults = {'type': _SDOption.IP6_ENDPOINT_TYPE, 'len': _SDOption.IP6_ENDPOINT_LEN}


class SDOption_IP6_Multicast(_SDOption_IP6):
    name = "IP6 Multicast Option"
    # default values specification
    _defaults = {'type': _SDOption.IP6_MCAST_TYPE, 'len': _SDOption.IP6_MCAST_LEN}


class SDOption_IP6_SD_EndPoint(_SDOption_IP6):
    name = "IP6 SDEndPoint Option"
    # default values specification
    _defaults = {'type': _SDOption.IP6_SDENDPOINT_TYPE, 'len': _SDOption.IP6_SDENDPOINT_LEN}


#
# SD PACKAGE DEFINITION
#
class SD(_SDPacketBase):
    """
    SD Packet

    NOTE :   when adding 'entries' or 'options', do not use list.append() method but create a new list
    e.g. :  p = SD()
            p.option_array = [SDOption_Config(),SDOption_IP6_EndPoint()]
    """
    # Message ID[32bit]     value=0xFFFF 8100
    SOMEIP_MSGID_SRVID = 0xffff
    SOMEIP_MSGID_SUBID = 0x1
    SOMEIP_MSGID_EVENTID = 0x100

    SOMEIP_PROTO_VER = 0x01                     # Protocol Version[8bit]
    SOMEIP_IFACE_VER = 0x01                     # Interface Version[8bit]
    SOMEIP_MSG_TYPE = SOMEIP.TYPE_NOTIFICATION  # Message Type[8bit]        value=0x02 NOTIFICATION

    name = "SD"
    # Flags definition: {"name":(mask,offset)}
    _sdFlag = collections.namedtuple('Flag', 'mask offset')
    FLAGSDEF = {
        "REBOOT": _sdFlag(mask=0x80, offset=7),   # ReBoot flag         用于表明是否发生ECU重启、Link down
        "UNICAST": _sdFlag(mask=0x40, offset=6)   # UniCast flag        支持使用单播接受
    }

    fields_desc = [
        ByteField("flags", 0),                                                                              # Flags[8bit]
        X3BytesField("res", 0),                                                                             # Reserved[24bit]
        FieldLenField("len_entry_array", None, length_of="entry_array", fmt="!I"),                          # Length of Entries Array[32bit]
        PacketListField("entry_array", None, cls=_SDEntry, length_from=lambda pkt:pkt.len_entry_array),     # Entries Array[variable size]
        FieldLenField("len_option_array", None, length_of="option_array", fmt="!I"),                        # Length of Options Array[32bit]
        PacketListField("option_array", None, cls=_SDOption, length_from=lambda pkt:pkt.len_option_array)]  # Options Array[variable size]

    def __init__(self, *args, **kwargs):
        super(SD, self).__init__(*args, **kwargs)
        self.explicit = 1

    def getFlag(self, name):
        """ get particular flag from bitfield."""
        name = name.upper()
        if name in self.FLAGSDEF:
            return (self.flags & self.FLAGSDEF[name].mask) >> self.FLAGSDEF[name].offset
        else:
            return None

    def setFlag(self, name, value):
        """
         用于设置SOMEIP header之后的Flags[8bit],Flags中包含两个标志位Reboot Flag和Unicast Flag
         param str name : name of the flag to set (see SD.FLAGSDEF)
         :param int value : either 0x1 or 0x0 (provided int will be ANDed with 0x01)
        """
        name = name.upper()
        if name in self.FLAGSDEF:
            self.flags = ((self.flags & ctypes.c_ubyte(~self.FLAGSDEF[name].mask).value) |
                          (value & 0x01) << self.FLAGSDEF[name].offset)

    def setEntryArray(self, entry_list):
        """
        Add entries to entry_array.
        :param entry_list: list of entries to be added. Single entry object also accepted
        """
        if isinstance(entry_list, list):
            self.entry_array = entry_list
        else:
            self.entry_array = [entry_list]

    def setOptionArray(self, option_list):
        """
        Add options to option_array.
        :param option_list: list of options to be added. Single option object also accepted
        """
        if isinstance(option_list, list):
            self.option_array = option_list
        else:
            self.option_array = [option_list]

    def getSomeip(self, stacked=False):
        """
        return SD-initialized SOME/IP packet
        :param stacked: boolean. Either just SOME/IP packet or stacked over SD-self
        """
        p = SOMEIP()
        p.msg_id.srv_id = SD.SOMEIP_MSGID_SRVID
        p.msg_id.sub_id = SD.SOMEIP_MSGID_SUBID
        p.msg_id.event_id = SD.SOMEIP_MSGID_EVENTID
        p.proto_ver = SD.SOMEIP_PROTO_VER
        p.iface_ver = SD.SOMEIP_IFACE_VER
        p.msg_type = SD.SOMEIP_MSG_TYPE

        if stacked:
            return p / self
        else:
            return p
