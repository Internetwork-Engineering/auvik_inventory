# -*- coding: utf-8 -*-
# vim: noai:et:tw=80:ts=4:ss=4:sts=4:sw=4:ft=python

'''
Title:              spec.py
Description:        Spec for AuvikAPI
Author:             Ricky Laney
Version:            0.1.0
'''
import json
import os
from typing import Union
from src.auvik.constants import (
    ALL_DEVICE_TYPES,
    NET_DEVICE_TYPES,
    INTERFACE_TYPES,
    NETWORK_TYPES,
)
from src.constants import PRJ_DIR
from src.exceptions import IEAutomationAuvikSpecError

AUVIK_SPEC = os.path.join(PRJ_DIR, 'docs/auvik_api_spec.json')


class AuvikSpec:
    """ Auvik's OpenAPI spec class for filtering and validation
    """

    def __init__(self, spec_file=AUVIK_SPEC) -> None:
        self.spec_file = spec_file
        self.spec = self.load_spec()
        self.server_url = self.spec['servers'][0]['url']

    def load_spec(self) -> None:
        """ Loads the OpenAPI spec
        """
        if not os.path.isfile(self.spec_file):
            raise IEAutomationAuvikSpecError(f"Not a valid spec file: {spec_file}")
        with open(self.spec_file) as sf:
            spec = json.load(sf)
        return spec

    @property
    def paths(self) -> list:
        return [k for k in self.spec['paths'].keys()]

    @property
    def tags(self) -> list:
        return [k['name'] for k in self.spec['tags']]

    def _check_path(self, path: str) -> Union[None, IEAutomationSpecError]:
        if path not in self.paths:
            raise IEAutomationAuvikSpecError(f"Invalid path: {path}")

    def _check_tag(self, tag: str) -> Union[None, IEAutomationSpecError]:
        if tag not in self.tags:
            raise IEAutomationAuvikSpecError(f"Invalid tag: {tag}")

    def paths_by_tag(self, tag: str) -> list:
        """ Get a list of URL paths for specific tag
        """
        self._check_tag(tag)
        return [k for k,v in self.spec['paths'].items() \
                if tag in v['get']['tags']]

    def path_operation_id(self, path: str) -> str:
        self._check_path(path)
        return self.spec['paths'][path]['get']['operationId']

    def path_params(self, path: str) -> list:
        """ Get a list of parameters for a URL path
        """
        self._check_path(path)
        return [p for p in self.spec['paths'][path]['get']['parameters']]

    def required_path_params(self, path: str) -> list:
        """ Get a list of required parameters for a URL path
        """
        self._check_path(path)
        return [p for p in self.path_params(path) \
                if p['required'] == 'true']

    def query_path_params(self, path: str) -> list:
        """ Get a list of query parameters for a URL path
        """
        self._check_path(path)
        return [p for p in self.path_params(path) \
                if p['in'] == 'query']

    def path_only_params(self, path: str) -> list:
        """ Get a list of query parameters for a URL path
        """
        self._check_path(path)
        return [p for p in self.path_params(path) \
                if p['in'] == 'path']

