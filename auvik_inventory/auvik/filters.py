# -*- coding: utf-8 -*-
# vim: noai:et:tw=80:ts=4:ss=4:sts=4:sw=4:ft=python

'''
Title:              filters.py
'''
from src.exceptions import IEAutomationAuvikFilterError
from typing import List, Union

LUod = List[Union[object, dict]]

class AuvikFilter:
    ''' Filters for the Auvik API device inventory

    :param:str: filter_str = String used to filter objects.
    The string should be in 'key=val,key2=val2' format. Each item separated
    by ',' (comma) and key/val pair separated by '=' (equals).
    '''
    def __init__(self, filters: Union[str, list]) -> None:
        # Filter strings override config filters
        if isinstance(filters, str):
            self.filters = self._build_filters(filters)
        else:
            self.filters = filters

    @staticmethod
    def _build_filters(filter_str: str) -> list:
        filters = []
        items = filter_str.split(',')
        for item in items:
            if '=' not in item:
                raise IEAutomationAuvikFilterError(
                    f"Invalid filter item: {item}"
                )
            key, value = item.split('=')
            filters.append({key: value})
        return filters

    def is_valid_device(self, device: Union[object, dict]) -> bool:
        if not self.filters:
            return True
        else:
            for fil in self.filters:
                for fil_key, fil_val in fil.items():
                    device_value = None
                    if isinstance(device, dict):
                        if 'item' in device.keys():
                            device = device['item']
                        if fil_key in device.keys():
                            device_value = device.get(fil_key)
                    else:
                        if hasattr(device, fil_key):
                            device_value = getattr(device, fil_key)
                    if device_value and fil_val.lower() in device_value.lower():
                        continue
                    else:
                        return False
        return True

    def filter_devices(self, devices: LUod) -> LUod:
        valid_devices = [device for device in devices if \
                        self.is_valid_device(device)]
        return valid_devices

