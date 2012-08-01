echo """auto $interface
iface $interface inet manual
    up ifconfig $interface up """ >> /etc/network/interfaces

