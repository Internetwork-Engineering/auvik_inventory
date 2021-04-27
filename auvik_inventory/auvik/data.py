# -*- coding: utf-8 -*-
# vim: noai:et:tw=80:ts=4:ss=4:sts=4:sw=4:ft=python

"""
Title:              data.py
"""
import jsonpickle
import os
from sysdescrparser import sysdescrparser
from typing import (
    Union,
    Any,
    Dict,
    List,
    Optional,
    Iterable,
)
from src.auvik.constants import (
    AUVIK_NET_DEVICE_TYPES,
    NETWORK_TYPES,
    INTERFACE_TYPES,
    ALL_DEVICE_TYPES,
)
from src.constants import PRJ_DIR, NET_DEVICE_MAPPER
from src.exceptions import IEAutomationAuvikDeviceDataError
from src.util import time_formatter

# Typing shortcuts
UdLd = Union[dict, List[dict]]
UsP = Union[str, os.PathLike]
OUsP = Optional[UsP]

__all__ = [
    'AuvikDeviceData',
    'AuvikTenantData',
    'AuvikNetworkData',
]


class AuvikDeviceData:
    """ Used to store device data from AuvikAPI.
    Will raise exception if NOT device data.
    Loads and processes data during initialization.

    :param:dict:   data - dictionary from AuvikAPI
    """

    def __init__(
            self,
            data: dict,
            details: dict=None,
            warranty: dict=None,
            lifecycle: dict=None,
        ) -> None:
        if data['type'] != 'device':
            raise IEAutomationAuvikDeviceDataError(f"Invalid type: {data['type']}'")
        self.name = None
        self.ip = None
        self.os = None
        self.model = None
        self.version = None
        self.tenant = None
        self.nd_type = None
        self.load(data)
        # Details data
        if details:
            self.snmp_status = None
            self.login_status = None
            self.wmi_status = None
            self.vmware_status = None
            self.manage_status = None
            self.netflow_status = None
            self.connected_devices = []
            self.interfaces = []
            self.config_backup = False
            self.last_backup = None
            self.load_details(details)
        # Warranty data
        if warranty:
            self.service_coverage = None
            self.service_attachment = None
            self.contract_renewal = None
            self.warranty_coverage = None
            self.warranty_expiration = None
            self.recommended_software = None
            self.load_warranty(warranty)
        # Lifecycle data
        if lifecycle:
            self.sales_availability = None
            self.software_maintenance = None
            self.security_software_maintenance = None
            self.last_support = None
            self.load_lifecycle(lifecycle)

    def __str__(self):
        return f"{self.name},{self.ip},{self.os},{self.nd_type}"

    def __repr__(self):
        return f"<AuvikDeviceData[name={self.name}, ip={self.ip}]>"

    def load(self, data: dict) -> None:
        self._id = data['id']
        self.ips = data['attributes']['ipAddresses']
        self.name = data['attributes']['deviceName']
        self.device_type = data['attributes']['deviceType']
        self.make = data['attributes']['makeModel']
        self.vendor = data['attributes']['vendorName']
        self.software = data['attributes']['softwareVersion']
        self.serial = data['attributes']['serialNumber']
        self.description = data['attributes']['description']
        self.firmware = data['attributes']['firmwareVersion']
        self.status = data['attributes']['onlineStatus']
        self.last_seen = time_formatter(data['attributes']['lastSeenTime'])
        self.last_modified = time_formatter(data['attributes']['lastModified'])
        sys = sysdescrparser(self.description)
        self.os = sys.os
        self.model = sys.model
        self.version = sys.version
        self.tenant = AuvikTenantData(data['relationships']['tenant']['data'])
        self.process_ip()
        self.process_nd_type()

    @property
    def pretty_name(self) -> str:
        if not self.name or '@' in self.name:
            return 'Unknown'
        if ' ' in self.name:
            name = self.name.replace(' ', '_')
        else:
            name = self.name
        # Split on '.' to remove domain names
        if '.' in name:
            new_name = name.split('.')
            if len(new_name) <= 3:
                return new_name[0]
        return name

    def _as_dict(self) -> dict:
        _pretty_dict_ = {}
        for key, val in self.__dict__.items():
            if isinstance(val, list):
                _pretty_dict_[key] = len(val)
            else:
                _pretty_dict_[key] = val
        return _pretty_dict_

    def toJSON(self) -> object:
        return jsonpickle.encode(self, unpicklable=False)

    def is_net_device(self) -> bool:
        if self.device_type in AUVIK_NET_DEVICE_TYPES and \
            not self.name.__contains__(' Member '):
            return True
        return False

    def has_os(self) -> bool:
        if self.os != 'UNKNOWN':
            return True
        return False

    def process_ip(self) -> None:
        if not self.ip:
            if '@' in self.name:
                # Unknown device name contains the target IP
                self.ip = self.name.split('@')[1]
            elif self.ips:
                self.ip = self.ips[0]
            # ips = self.ips
            # if len(ips) > 1:
            #     # Remove duplicates
            #     ips = set(ips)
            #     # Turn back to list
            #     ips = list(ips)
            #     # Sort IPs in-place
            #     ips.sort()
            # # Always set to first 'lowest number' IP
            # self.ip = ips[0]

    def process_nd_type(self) -> None:
        if self.is_net_device():
            self.nd_type = "autodetect"
            if self.has_os():
                try:
                    self.nd_type = NET_DEVICE_MAPPER[self.os]
                except KeyError:
                    pass

    def load_details(self, data: dict) -> None:
        dd = data["attributes"]
        self.snmp_status = dd["discoveryStatus"]["snmp"]
        self.login_status = dd["discoveryStatus"]["login"]
        self.wmi_status = dd["discoveryStatus"]["wmi"]
        self.vmware_status = dd["discoveryStatus"]["vmware"]
        self.manage_status = dd["manageStatus"]
        self.netflow_status = dd["trafficInsightsStatus"]
        con_data = data["relationships"]["connectedDevices"]["data"]
        for con in con_data:
            self.connected_devices.append(con["attributes"]["deviceName"])
        int_data = data["relationships"]["interfaces"]["data"]
        for interface in int_data:
            mac = interface["attributes"]["macAddress"]
            name = interface["attributes"]["interfaceName"]
            if mac and mac not in ['null', 'Null', 'NULL', '', None]:
                self.interfaces.append({name:mac})
        cfg_data = data["relationships"]["configurations"]["data"]
        if cfg_data and len(cfg_data) >= 1:
            cfg_attr = cfg_data[0]["attributes"]
            self.config_backup = cfg_attr["isRunning"]
            self.last_backup = time_formatter(cfg_attr["backupTime"])

    def load_warranty(self, data: dict) -> None:
        wd = data["attributes"]
        self.service_coverage = wd["serviceCoverageStatus"]
        self.service_attachment = wd["serviceAttachmentStatus"]
        self.contract_renewal = wd["contractRenewalAvailability"]
        self.warranty_coverage = wd["warrantyCoverageStatus"]
        self.warranty_expiration = wd["warrantyExpirationDate"].split()[0]
        self.recommended_software = wd["recommendedSoftwareVersion"]

    def load_lifecycle(self, data: dict) -> None:
        ld = data["attributes"]
        self.sales_availability = ld["salesAvailability"]
        self.software_maintenance = ld["softwareMaintenanceStatus"]
        self.security_software_maintenance = ld["securitySoftwareMaintenanceStatus"]
        self.last_support = ld["lastSupportStatus"]


class AuvikTenantData:
    def __init__(self, data: dict) -> None:
        self._id = None
        self.domain = None
        self.tenant_type = None
        self.load(data)

    def __str__(self) -> str:
        return str(self.domain)

    def __repr__(self) -> str:
        return self.__str__()

    def load(self, data: dict) -> None:
        self._id = data['id']
        self.domain = data['attributes']['domainPrefix']
        try:
            self.tenant_type = data['attributes']['tenantType']
        except KeyError:
            self.tenant_type = None

    def _as_dict(self) -> dict:
        return self.__dict__


class AuvikNetworkData:
    def __init__(self, data: dict) -> None:
        self._id = None
        self.net_type = None
        self.name = None
        self.description = None
        self.scan_status = None
        self.last_modified = None
        self.devices= []
        self.load(data)

    def __str__(self) -> str:
        return f"{self.name}:{self.net_type}:{len(self.devices)} devices"

    def __repr__(self) -> str:
        return self.__str__()

    def load(self, data: dict) -> None:
        self._id = data['id']
        self.net_type = data['attributes']['networkType']
        self.name = data['attributes']['networkName']
        self.description = data['attributes']['description']
        self.scan_status = data['attributes']['scanStatus']
        self.last_modified = time_formatter(data['attributes']['lastModified'])
        self.tenant = AuvikTenantData(data['relationships']['tenant']['data'])
        try:
            devices = data['relationships']['devices']['data']
        except KeyError:
            devices = None
        if devices:
            for device in devices:
                self.devices.append({
                    "name": device['attributes']['deviceName'],
                    "id": device['id'],
                })

    def _as_dict(self) -> dict:
        return self.__dict__

