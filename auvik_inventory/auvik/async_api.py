# -*- coding: utf-8 -*-
# vim: noai:et:tw=80:ts=4:ss=4:sts=4:sw=4:ft=python

"""
Title:              main.py
"""

import aiohttp
from aiohttp import ClientSession, BasicAuth
from alive_progress import alive_bar
import base64
from datetime import datetime
import os
import ssl
from typing import (
    Union,
    Dict,
    List,
    Optional,
)
# Mylibs
from src.auvik.spec import AuvikSpec
from src.exceptions import IEAutomationError, IEAutomationSSLError

# Typing shortcuts
UdLd = Union[dict, List[dict]]
UsP = Union[str, os.PathLike]

default_url = "https://auvikapi.us1.my.auvik.com/v1"
BASE_URL = os.getenv("AUVIK_API_URL")
USER = os.getenv("AUVIK_API_USER")
API_KEY = os.getenv("AUVIK_API_KEY")
DOMAIN = os.getenv("AUVIK_API_DOMAIN")
SSL_CERT = os.getenv("AUVIK_API_SSL_CERT")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)



# async def get_book_details_async(isbn, session):
#     """Get book details using Google Books API (asynchronously)"""
#     url = GOOGLE_BOOKS_URL + isbn
#     try:
#         response = await session.request(method='GET', url=url)
#         response.raise_for_status()
#         print(f"Response status ({url}): {response.status}")
#     except HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err}")
#     except Exception as err:
#         print(f"An error ocurred: {err}")
#     response_json = await response.json()
#     return response_json
#
#
# async def run_program(isbn, session):
#     """Wrapper for running program in an asynchronous manner"""
#     try:
#         response = await get_book_details_async(isbn, session)
#         parsed_response = extract_fields_from_response(response)
#         print(f"Response: {json.dumps(parsed_response, indent=2)}")
#     except Exception as err:
#         print(f"Exception occured: {err}")
#         pass
#
# async with ClientSession() as session:
#     await asyncio.gather(*[run_program(isbn, session) for isbn in LIST_ISBN])
import aiohttp
import asyncio

async def fetch(client):
    async with client.get('http://python.org') as resp:
        assert resp.status == 200
        return await resp.text()

async def main():
    async with aiohttp.ClientSession() as client:
        html = await fetch(client)
        print(html)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

class AuvikAPI:
    """ Main entry point for the Auvik API
    """
    def __init__(self,
            user: str=None,
            api_key: str=None,
            ssl_cert: UsP=None,
            timeout: int=15) -> None:
        self.spec = AuvikSpec()
        self.base_url = BASE_URL or self.spec.server_url
        self.url = None
        self._user = user or USER
        self._api_key = api_key or API_KEY
        self.auth = BasicAuth(self._user, self._api_key)
        self._cert = os.path.join(ROOT, f"ssl/{ssl_cert or SSL_CERT}")
        if os.path.isfile(self._cert):
            self.ssl = ssl.create_default_context(cafile=self._cert)
        else:
            raise IEAutomationError(f"You MUST use SSL encryption!")
            # self.ssl = False
            # Disable warnings
            # requests.packages.urllib3.disable_warnings()
        self._timeout = timeout
        self.loop = asyncio.get_event_loop()
        self.session = ClientSession(auth=self.auth)


    def _add_to_base_url(self, path: str) -> str:
        if not path.startswith('/'):
            path = f"/{path}"
        return f"{self.base_url}{path}"


    def _set_url(self, url: str) -> None:
        if url.startswith(self.base_url):
            self.url = url
        else:
            self.url = self._add_to_base_url(url)


    async def _async_get(self) -> UdLd:
        """ Private method that performs specialized async GET operations.
        """
        async with self.session as session:
            async with session.get(self.url, ssl=self.ssl) as response:
                return await response.json()


    async def _get(self, url: str=None, *, return_data: bool=True, recurse: bool=False) -> UdLd:
        if not url and not self.url:
            raise IEAutomationError(f"No URL provided nor set via attribute")
        if url:
            self._set_url(url)
        if recurse:
            return await self._get_recursive()
        results = await self._async_get()
        if results:
            return results['data'] if return_data else results
        else:
            raise IEAutomationError(f"HTTP error code: {results}")


    async def _get_recursive(self) -> UdLd:
        """ Private method recursive GET operation.
        This is called by using the _get() method with recurse=True.
        """
        results = await self._get(return_data=False)
        data = results['data']
        counter = 1
        no_pages = results['meta']['totalPages']
        pages_left = int(no_pages) - counter
        # Go get results and extend data (an iteration)
        with alive_bar(pages_left, bar='smooth') as bar:
            # Now check for a 'next' link and recurse if found
            while 'next' in results['links'].keys():
                self.url = results['links']['next']
                results = await self._get(return_data=False)
                data.extend(results['data'])
                counter += 1
                bar()
        # No more 'next' links return data
        return data


    async def get_tenants(self) -> Dict:
        """ Get a list of tenants for your default domain.
        """
        url_path = "/tenants"
        return await self._get(url_path)


    async def get_tenant_id_by_name(self, name: str) -> str:
        """ Get the id of tenant by name. Uses 'name' in 'actual_name_from_API'.
        """
        for tenant in self.get_tenants():
            if name in tenant['attributes']['domainPrefix']:
                return tenant['id']


    async def get_tenant_detail(self, domain: str=DOMAIN, name: str=None, tenant_id: str=None) -> Dict:
        """ Get details for a tenant.
        """
        if name is None and tenant_id is None:
            raise AuvikAPIError("Provide either name or id of the tenant")
        elif name and not tenant_id:
            tenant_id = get_tenant_id_by_name(name)
        url_path = f"/tenants/detail/{tenant_id}?tenantDomainPrefix={domain}"
        return await self._get(url_path)


    async def get_tenant_inventory(self, tenant_ids: Union[str, list], recurse: bool=False) -> Dict:
        """ Get a list of network devices from one or more tenant ids.
        """
        tenants = [','.join(t) for t in tenant_ids] \
            if isinstance(tenant_ids, list) else tenant_ids
        url_path = f"/inventory/device/info?tenants={tenants}"
        return await self._get(url_path, recurse=recurse)


    async def get_device_info(self, device_id: str, detail: bool=False, fields: Union[str, list]=None) -> Dict:
        """ Get general info about a device.
        """
        url_path = f"/inventory/device/info/{device_id}"
        if detail:
            url_path = f"{url_path}?include=deviceDetail"
            if fields:
                include = [','.join(f) for f in fields] if isinstance(fields, list) else fields
                url_path = f"{url_path}&fields[deviceDetail]={include}"
        return await self._get(url_path)


    async def get_device_detail(self, device_id: str) -> Dict:
        """ Get detail about a device.
        """
        url_path = f"/inventory/device/detail/{device_id}"
        return await self._get(url_path)


    async def get_device_extended_detail(self, device_id: str) -> Dict:
        """ Get extended detail about a device.
        """
        url_path = f"/inventory/device/detail/extended/{device_id}"
        return await self._get(url_path)


    async def get_device_warranty_info(self, device_id: str) -> Dict:
        """ Get extended details about a device.
        """
        url_path = f"/inventory/device/warranty/{device_id}"
        return await self._get(url_path)


    async def get_device_lifecycle_info(self, device_id: str) -> Dict:
        """ Get extended details about a device.
        """
        url_path = f"/inventory/device/lifecycle/{device_id}"
        return await self._get(url_path)
