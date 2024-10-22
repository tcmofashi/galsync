# -*- coding: utf-8 -*-
import psutil
from psutil import net_if_addrs

AF_typs = {0: 'AF_UNSPEC',
           1: 'AF_FILE',
           2: 'AF_INET',  # ipv4地址
           3: 'AF_AX25',
           4: 'AF_IPX',
           5: 'AF_APPLETALK',
           6: 'AF_NETROM',
           7: 'AF_BRIDGE',
           8: 'AF_ATMPVC',
           9: 'AF_X25',
           10: 'AF_INET6',  # ipv6地址
           11: 'AF_ROSE',
           12: 'AF_DECnet',
           13: 'AF_NETBEUI',
           14: 'AF_SECURITY',
           15: 'AF_KEY',
           16: 'AF_NETLINK',
           17: 'AF_PACKET',  # ipv4的MAC地址
           18: 'AF_ASH',
           19: 'AF_ECONET',
           20: 'AF_ATMSVC',
           22: 'AF_SNA',
           23: 'AF_IRDA',
           24: 'AF_PPPOX',
           25: 'AF_WANPIPE',
           31: 'AF_BLUETOOTH'}

dic = psutil.net_if_addrs()
for k in dic:
    print (k, "----------")
    snics = dic[k]
    mac, ipv4, ipv6 = "", "", ""
    for s in snics:
        if type(s.family) == int:
            fam_int = s.family
            # print (s.family)
        else:
            fam_int = s.family.value
            # print (s.family.value)
        tp = AF_typs[fam_int]
        # print (tp)
        # print (tp=='AF_INET6',s.address)
        if tp in {'AF_LINK', 'AF_PACKET'}:
            mac = s.address
        if tp == 'AF_INET':
            ipv4 = s.address
        if tp == 'AF_INET6':
            ipv6 = s.address
    print(ipv4, ipv6)


