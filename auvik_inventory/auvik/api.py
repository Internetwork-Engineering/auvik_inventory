# -*- coding: utf-8 -*-
# vim: noai:et:tw=80:ts=4:ss=4:sts=4:sw=4:ft=python

"""
Title:              main.py
"""

from alive_progress import alive_bar
from functools import cached_property
import logging
import os
from prettytable import PrettyTable
import requests
from typing import (
    Union,
    Dict,
    List,
    Optional,
    Iterable,
)
from auvik_inventory.data import AuvikDeviceData, AuvikTenantData, AuvikNetworkData
from auvik_inventory.filters import AuvikFilter
from auvik_inventory.config import Config
from auvik_inventory.constants import PRJ_DIR
from auvik_inventory.logger import Logger
from auvik_inventory.exceptions import (
    AuvikAPIError,
    AuvikSSLError,
    ConfigError,
)

# Typing shortcuts
UdLd = Union[dict, List[dict]]
UsP = Union[str, os.PathLike]
OUsP = Optional[UsP]
ADD = List[Union[AuvikDeviceData, dict]]
ATD = List[Union[AuvikTenantData, dict]]
Usl = Union[str, list]

__all__ = ['AuvikAPI']


class AuvikAPI:
    """ Main entry point for the Auvik API

    Line below are for disabling SSL and are for testing ONLY!
    # requests.packages.urllib3.disable_warnings()
    """
    DEFAULT_URL = "https://auvikapi.us1.my.auvik.com/v1"
    CERT_DIR = os.path.join(PRJ_DIR, f"ssl")

    def __init__(self, config_file: OUsP=None) -> None:
        # Create a Logger instance per AuvikAPI instance
        self.log = IELogger('auvik.api')
        if config_file:
            self.config = IEConfig(config_file)
        else:
            self.config = IEConfig()
        self._load_config()
        # Initialized blank attributes
        self.url = None


    def _load_config(self) -> None:
        if not hasattr(self.config, 'auvik_api'):
            raise IEAutomationConfigError("No valid Auvik API config found")
        device_filters = None
        if 'device_filters' in self.config.filters.keys():
            config_device_filters = self.config.filters['device_filters']
            if config_device_filters:
                device_filters = AuvikFilter(config_device_filters)
        self.device_filters = device_filters
        domain_filters = None
        if 'domains' in self.config.filters.keys():
            domain_filters = self.config.filters['domains']
        self.domain_filters = domain_filters
        self.show_progress = self.config.show_progress
        auvik_config = self.config.auvik_api
        self.base_url = auvik_config['AUVIK_API_URL'] or self.DEFAULT_URL
        self.domain = auvik_config['AUVIK_API_DOMAIN']
        self._user = auvik_config['AUVIK_API_USER']
        self._api_key = auvik_config['AUVIK_API_KEY']
        self.auth = (self._user, self._api_key.show())
        cert_file = auvik_config['AUVIK_API_SSL_CERT']
        self._cert = os.path.join(self.CERT_DIR, cert_file)
        if os.path.isfile(self._cert):
            self.log.debug("Valid cert file found")
            self.ssl = self._cert
        else:
            self.log.critical("You MUST use SSL encryption!")
            raise IEAutomationAuvikSSLError("You MUST use SSL encryption!")


    def _add_to_base_url(self, path: str) -> str:
        if not path.startswith('/'):
            path = f"/{path}"
        return f"{self.base_url}{path}"


    def _set_url(self, url: str) -> None:
        if not url.startswith(self.base_url):
            url = self._add_to_base_url(url)
        self.log.debug(f"New url set -> {url}")
        self.url = url


    def _join_things(self, things: Union[str, list]) -> Union[str, list]:
        if isinstance(things, list):
            if len(things) == 1:
                return things[0]
            else:
                # Ensure no duplicates here
                clean_things = set(things)
                return [','.join(t) for t in clean_things]
        else:
            return things


    def _get(
        self,
        url: str=None,
        *,
        return_data: bool=True,
        recurse: bool=False,
    ) -> UdLd:
        """ Private method that performs specialized GET operations.
        """
        if not url and not self.url:
            raise IEAutomationAuvikAPIError(f"No URL provided nor set via attribute")
        if url:
            self._set_url(url)
        if recurse:
            return self._get_recursive()
        self.log.debug(f"_get called for -> {self.url}")
        response = requests.get(self.url, auth=self.auth, verify=self.ssl)
        if response.ok:
            self.log.debug(f"OK Response -> {self.url}")
            results = response.json()
            return results['data'] if return_data else results
        else:
            raise IEAutomationAuvikAPIError(
                f"HTTP error code: {response.raise_for_status()}"
            )


    def _get_recursive(self) -> UdLd:
        """ Private method recursive GET operation.
        This is called by using the _get() method with recurse=True.
        """
        # Get first results
        results = self._get(return_data=False)
        # Save first data
        data = results['data']
        try:
            num_pages = results['meta']['totalPages']
        except KeyError:
            self.log.error("Get recursive called and no more pages exist")
            return data
        pages_left = int(num_pages) - 1
        self.log.debug(f"_get_recursive called with {pages_left} pages left")
        # Go get results and extend data (an iteration)
        if self.show_progress:
            title = 'Gathering data from Auvik API'
            with alive_bar(pages_left, title=title, bar='smooth') as bar:
                # Now check for a 'next' link and recurse if found
                while 'next' in results['links'].keys():
                    self.url = results['links']['next']
                    results = self._get(return_data=False)
                    data.extend(results['data'])
                    bar()
        else:
            while 'next' in results['links'].keys():
                self.url = results['links']['next']
                results = self._get(return_data=False)
                data.extend(results['data'])
        # No more 'next' links return data
        return data


    @cached_property
    def tenants(self) -> ATD:
        """ Get a list of tenants for your default domain.
        """
        tenants = []
        url_path = "/tenants"
        self.log.debug(f"Tenants for {self.domain}")
        for tenant in self._get(url_path):
            tenants.append(AuvikTenantData(tenant))
        self.log.debug(f"{len(tenants)} tenants found for {self.domain}")
        return tenants


    def get_tenant_id_by_name(self, name: str) -> str:
        """ Get the id of tenant by name.
        Logic -> if 'name' in 'actual_name_from_API'.
        Returns first hit.
        """
        for tenant in self.tenants:
            if name in tenant.domain:
                return tenant._id


    def get_tenant_detail(self, domain: str=None, name: str=None,
                          tenant_id: str=None) -> dict:
        """ Get details for a tenant.
        """
        if not domain:
            domain = self.domain
        if not name and not tenant_id:
            raise AuvikAPIError("Provide either name or id of the tenant")
        elif name and not tenant_id:
            tenant_id = get_tenant_id_by_name(name)
        url_path = f"/tenants/detail/{tenant_id}?tenantDomainPrefix={domain}"
        return self._get(url_path)


    def generate_query(self, tenants: Usl=None, tenant_ids: Usl=None) -> str:
        # Tenant_ids take precedence
        if tenant_ids:
            names = tenant_ids
        elif tenants:
            names = tenants
        elif self.domain_filters:
            names = self.domain_filters
        else:
            raise IEAutomationAuvikAPIError(
                "Must provide tenants, tenant_ids, or domain filters"
            )
        if isinstance(names, str):
            ids = self.get_tenant_id_by_name(names)
            self.log.debug(f"Generated query for {ids}")
        else:
            ids = [self.get_tenant_id_by_name(n) for n in names]
            self.log.debug(f"Generated query for {len(ids)} tenants")
        return self._join_things(ids)


    def get_tenant_inventory(self, tenants: Usl=None, tenant_ids: Usl=None,
                             recurse: bool=True) -> dict:
        """ Get a list of inventory from one or more tenant ids.
        """
        query = self.generate_query(tenants, tenant_ids)
        url_path = f"/inventory/device/info?tenants={query}"
        return self._get(url_path, recurse=recurse)


    def get_tenant_networks(self, tenants: Usl=None, tenant_ids: Usl=None,
                            recurse: bool=True) -> dict:
        """ Get a list of networks from one or more tenant ids.
        """
        query = self.generate_query(tenants, tenant_ids)
        url_path = f"/inventory/network/info?tenants={query}"
        return self._get(url_path, recurse=recurse)


    def get_tenant_configs(self, tenants: Usl=None, tenant_ids: Usl=None,
                             recurse: bool=True) -> dict:
        """ Get a list of configs from one or more tenant ids.
        """
        query = self.generate_query(tenants, tenant_ids)
        url_path = f"/inventory/configuration/info?tenants={query}"
        return self._get(url_path, recurse=recurse)


    def get_device_info(self, device_id: str, detail: bool=False,
                        fields: Usl=None) -> dict:
        """ Get general info about a device.
        """
        url_path = f"/inventory/device/info/{device_id}"
        if detail:
            url_path = f"{url_path}?include=deviceDetail"
            if fields:
                include = self._join_things(fields)
                url_path = f"{url_path}&fields[deviceDetail]={include}"
        return self._get(url_path)


    def get_device_detail(self, device_id: str) -> dict:
        """ Get detail about a device.
        """
        url_path = f"/inventory/device/detail/{device_id}"
        return self._get(url_path)


    def get_device_extended_detail(self, device_id: str) -> dict:
        """ Get extended detail about a device.
        """
        url_path = f"/inventory/device/detail/extended/{device_id}"
        return self._get(url_path)


    def get_device_warranty(self, device_id: str) -> dict:
        """ Get extended details about a device.
        """
        url_path = f"/inventory/device/warranty/{device_id}"
        return self._get(url_path)


    def get_device_lifecycle(self, device_id: str) -> dict:
        """ Get extended details about a device.
        """
        url_path = f"/inventory/device/lifecycle/{device_id}"
        return self._get(url_path)


    def get_device_details(self, item: dict) -> dict:
        try:
            details = self.get_device_detail(item['id'])
        except Exception as e:
            details = None
            self.log.debug(f"Failed detail_info with {e}")
        try:
            warranty = self.get_device_warranty(item['id'])
        except Exception as e:
            warranty = None
            self.log.debug(f"Failed warranty_info with {e}")
        try:
            lifecycle = self.get_device_lifecycle(item['id'])
        except Exception as e:
            lifecycle = None
            self.log.debug(f"Failed lifecycle_info with {e}")
        finally:
            return {
                "item": item,
                "details": details,
                "warranty": warranty,
                "lifecycle": lifecycle,
            }


    def get_devices(
        self,
        tenants: Usl=None,
        tenant_ids: Usl=None,
        details: bool=False,
        filters: str=None,
        return_objects: bool=True,
    ) -> ADD:
        inv_items = self.get_tenant_inventory(tenants=tenants,
                                              tenant_ids=tenant_ids)
        self.log.info(f"Processing {len(inv_items)} devices")
        all_devs = []
        with alive_bar(
            len(inv_items),
            title='Processing inventory',
            bar='smooth',
        ) as bar:
            for item in inv_items:
                item = self.get_device_details(item) if details else item
                if return_objects:
                    if details:
                        device = AuvikDeviceData(**item)
                    else:
                        device = AuvikDeviceData(item)
                else:
                    device = item
                all_devs.append(device)
                bar()
        if self.device_filters:
            self.log.debug(f"Global filtering {len(all_devs)} devices")
            all_devs = self.device_filters.filter_devices(all_devs)
        if filters:
            dev_filter = AuvikFilter(filters)
            self.log.debug(f"Local filtering {len(all_devs)} devices")
            all_devs = dev_filter.filter_devices(all_devs)
        self.log.info(f"Processed {len(all_devs)} devices")
        return all_devs


    def get_net_devices(
        self,
        tenants: Usl=None,
        tenant_ids: Usl=None,
        details: bool=False,
        filters: str=None,
        return_objects: bool=True,
    ) -> ADD:
        inv_items = self.get_tenant_inventory(tenants=tenants,
                                              tenant_ids=tenant_ids)
        self.log.info(f"Processing {len(inv_items)} network devices")
        net_devs = []
        with alive_bar(
            len(inv_items),
            title='Processing network devices',
            bar='smooth',
        ) as bar:
            for item in inv_items:
                if details:
                    item = self.get_device_details(item)
                    device = AuvikDeviceData(**item)
                else:
                    device = AuvikDeviceData(item)
                if device.is_net_device():
                    if return_objects:
                        net_devs.append(device)
                    else:
                        net_devs.append(item)
                else:
                    self.log.debug(f"Not a net device {device}")
                bar()
        if self.device_filters:
            self.log.debug(f"Global filtering {len(net_devs)} net devices")
            net_devs = self.device_filters.filter_devices(net_devs)
        if filters:
            dev_filter = AuvikFilter(filters)
            self.log.debug(f"Local filtering {len(net_devs)} net devices")
            net_devs = dev_filter.filter_devices(net_devs)
        self.log.info(f"Processed {len(net_devs)} net devices")
        return net_devs


    def get_networks(
        self,
        tenants: Usl=None,
        tenant_ids: Usl=None,
        filters: str=None,
        return_objects: bool=True,
    ) -> ADD:
        nets = self.get_tenant_networks(tenants=tenants, tenant_ids=tenant_ids)
        self.log.info(f"Processing {len(nets)} networks")
        all_nets = []
        with alive_bar(
            len(nets),
            title='Processing networks',
            bar='smooth',
        ) as bar:
            for net in nets:
                if return_objects:
                    network = AuvikNetworkData(net)
                else:
                    network = net
                all_nets.append(network)
                bar()
        self.log.info(f"Processed {len(all_nets)} networks")
        return all_nets


    def print_table(self, devices: ADD, filters: str=None) -> PrettyTable:
        self.log.debug(f"print_table with {len(devices)} devices")
        with alive_bar(len(devices), title='Creating table', bar='smooth') as bar:
            headers = devices[0]._as_dict().keys()
            ptable = PrettyTable(field_names=headers)
            for dev in devices:
                ptable.add_row(dev._as_dict().values())
                bar()
        return print(ptable)
