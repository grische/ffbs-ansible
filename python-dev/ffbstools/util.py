import binascii
import codecs
import ipaddress

def addresses_from_number(num):
    """calculates the client's addresses from its 14bit id"""
    v6base = 0x20010bf70381 << 80
    range_size = 10
    def as_v4(n):
        return str(ipaddress.IPv4Address(n))
    def as_v6(n):
        return str(ipaddress.IPv6Address(n))
    address4 = as_v4(0x0a000000 | (num << range_size) + 1)
    range4 = as_v4(0x0a000000 | (num << range_size))+'/'+str(32-range_size)
    address6 = as_v6(v6base | (num << 64) + 1)
    range6 = as_v6(v6base | (num << 64))+'/64'
    return dict(address4=address4, range4=range4, address6=address6, range6=range6)

def escape_pubkey(pubkey):
    return pubkey.replace('+','-').replace('/','_')

def unescape_pubkey(key):
    return key.replace('-','+').replace('_','/')

def verify_pubkey(pubkey):
    try:
        raw = codecs.decode(pubkey.encode(), 'base64')
        return len(raw) == 32
    except binascii.Error:
        return False

