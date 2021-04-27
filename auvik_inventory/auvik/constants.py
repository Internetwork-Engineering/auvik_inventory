# -*- coding: utf-8 -*-
# vim: noai:et:tw=80:ts=4:ss=4:sts=4:sw=4:ft=python

'''
Title:              constants.py
Description:        Constants for Auvik
Author:             Ricky Laney
Version:            0.1.0
'''
__all__ = [
    'AUVIK_NET_DEVICE_TYPES',
    'NETWORK_TYPES',
    'INTERFACE_TYPES',
    'ALL_DEVICE_TYPES',
]

AUVIK_NET_DEVICE_TYPES = [
    "switch",
    "l3Switch",
    "router",
    "firewall",
    "bridge",
    "hub",
    "loadBalancer",
    "packetProcessor",
    "chassis",
    "backhaul",
    "voipSwitch",
    "stack",
    "utm",
]

NETWORK_TYPES = [
    "routed",
    "vlan",
    "wifi",
    "loopback",
    "network",
    "layer2",
    "internet",
]

INTERFACE_TYPES = [
    "ethernet",
    "wifi",
    "bluetooth",
    "cdma",
    "coax",
    "cpu",
    "distributedVirtualSwitch",
    "firewire",
    "gsm",
    "ieee8023AdLag",
    "inferredWired",
    "inferredWireless",
    "interface",
    "linkAggregation",
    "loopback",
    "modem",
    "wimax",
    "optical",
    "other",
    "parallel",
    "ppp",
    "radiomac",
    "rs232",
    "tunnel",
    "unknown",
    "usb",
    "virtualBridge",
    "virtualNic",
    "virtualSwitch",
    "vlan",
]

ALL_DEVICE_TYPES = [
    "unknown",
    "switch",
    "l3Switch",
    "router",
    "accessPoint",
    "firewall",
    "workstation",
    "server",
    "storage",
    "printer",
    "copier",
    "hypervisor",
    "multimedia",
    "phone",
    "tablet",
    "handheld",
    "virtualAppliance",
    "bridge",
    "controller",
    "hub",
    "modem",
    "ups",
    "module",
    "loadBalancer",
    "camera",
    "telecommunications",
    "packetProcessor",
    "chassis",
    "airConditioner",
    "virtualMachine",
    "pdu",
    "ipPhone",
    "backhaul",
    "internetOfThings",
    "voipSwitch",
    "stack",
    "backupDevice",
    "timeClock",
    "lightingDevice",
    "audioVisual",
    "securityAppliance",
    "utm",
    "alarm",
    "buildingManagement",
    "ipmi",
    "thinAccessPoint",
    "thinClient"
]
