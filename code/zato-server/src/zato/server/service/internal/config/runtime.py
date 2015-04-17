# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging, os
from cStringIO import StringIO
from os import path as p
from stat import S_IMODE
from traceback import format_exc

# ConfigObj
from configobj import ConfigObj

# Zato
from zato.common.util import parse_key_value
from zato.server.service.internal import AdminService, AdminSIO

logger = logging.getLogger(__name__)

# ################################################################################################################################

class ValidationResult(object):
    def __init__(self, details, config):
        self.details = details
        self.is_valid = not details
        self.config = config

    def __nonzero__(self):
        return self.is_valid

# ################################################################################################################################

class RuntimeConfigManager(object):
    """ An object through which access to run-time config files is mediated,
    including all of CRUD. Raises exceptions if attempts are made to edit/create/delete
    files outside of what Zato is configured to use hence ensuring Zato won't be able
    to update arbitrary files on the file system.
    """
    def __init__(self, server, needs_read=True):
        self.server = server
        self.items = []
        if needs_read:
            self.read()

    def _append(self, name, pickup_dir, full_path, access_rights):
        """ Appends information on a given config file to our list of results.
        """
        self.items.append({
            'name':name, 'full_path':full_path, 'access_rights':access_rights, 'pickup_dir':pickup_dir
        })

    def _get_info(self, path, parent_dir=None):
        """ Establishes a full path + access rights of config file.
        """
        if not p.isabs(path):
            full_path = p.abspath(p.normpath(p.join(parent_dir or self.server.repo_location, path)))
        else:
            full_path = path

        try:
            access_rights = oct(S_IMODE(os.stat(full_path).st_mode))
        except OSError, e:
            logger.warn('Could not stat `%s` (%s), e:`%s`', full_path, path, format_exc(e))
            access_rights = None

        return full_path, access_rights

    def read(self):
        """ Reads a list of config files into self.items - doesn't read their contents.
        """
        for name, item in sorted(self.server.fs_server_config.runtime_config.iteritems()):

            # Regular static files
            if name != 'pickup_dir':
                self._append(name, None, *self._get_info(item))

            # Paths to pick up dirs (but can be just a single path as well)
            else:
                for dir_path in item if isinstance(item, list) else [item]:
                    full_pickup_dir = p.join(self.server.repo_location, dir_path)

                    if p.exists(full_pickup_dir):
                        for path in os.listdir(full_pickup_dir):
                            full_path = p.abspath(p.join(full_pickup_dir, path))
                            if p.isfile(full_path):
                                self._append(path, dir_path, *self._get_info(full_path, full_pickup_dir))
                    else:
                        logger.warn('No such directory `%s` (%s)`', full_pickup_dir, dir_path)

    def get_items(self):
        """ Returns a list of config files info.
        """
        return self.items

    def get_full_path(self, name, pickup_dir=None):
        """ Returns full path to a config file
        """
        for item in self.items:
            if item['name'] == name and item['pickup_dir'] == pickup_dir:
                return item['full_path']
        else:
            raise ValueError('No such item `{}` ({})'.format(name, pickup_dir))

    # API-wise it makes sense to add a separate function
    exists = get_full_path

    def get_source(self, name, pickup_dir=None):
        """ Returns source of a selected config file.
        """
        return open(self.get_full_path(name, pickup_dir)).read()

    def validate(self, source):
        """ Validates a config file's source.
        """
        details = ''
        config = None

        if not source:
            details = 'Config file is empty'
        else:
            try:
                config = ConfigObj(StringIO(source))
            except Exception, e:
                details = e.message

        return ValidationResult(details, config)

    def edit(self, name, pickup_dir, source):
        """ Validates and updates contents of an existing config file.
        """
        result = self.validate(source)
        if not result:
            raise ValueError('Invalid config file: `{}`'.format(result.details))

        # Will raise a ValueError if there is no such name or pickup_dir
        full_path = self.get_full_path(name, pickup_dir)

        # Ok, at that point we know that the source code is valid and that the path is OK,
        # so we can save the file now.
        f = open(full_path, 'wb')
        f.write(source)
        f.close()

    def create(self, name, pickup_dir, source):
        """ Creates a new config file in of the already existing pick directories.
        """

# ################################################################################################################################

class GetList(AdminService):
    """ Returns a list of run-time config files available.
    """
    name = 'tmp.runtime.get-list'

    class SimpleIO(AdminSIO):
        request_elem = 'zato_config_runtime_get_list_request'
        response_elem = 'zato_config_runtime_get_list_response'
        input_required = ('cluster_id',)
        output_required = ('name',)
        output_optional = ('pickup_dir', 'full_path', 'access_rights')
        output_repeated = True

    def handle(self):
        self.response.payload[:] = RuntimeConfigManager(self.server).get_items()

# ################################################################################################################################

class GetSource(AdminService):
    """ Returns source (contents) of a selected run-time config file.
    """
    name = 'tmp.runtime.get-source'

    class SimpleIO(AdminSIO):
        request_elem = 'zato_config_runtime_get_source_request'
        response_elem = 'zato_config_runtime_get_list_response'
        input_required = ('cluster_id', 'name')
        input_optional = ('pickup_dir',)
        output_optional = ('source',)

    def handle(self):
        self.response.payload = RuntimeConfigManager(self.server).validate(self.request.input.name, self.request.input.pickup_dir)

# ################################################################################################################################

class Validate(AdminService):
    """ Validates a given config file's contents.
    """
    name = 'tmp.runtime.validate'

    class SimpleIO(AdminSIO):
        request_elem = 'zato_config_runtime_validate_request'
        response_elem = 'zato_config_runtime_validate_response'
        input_required = ('cluster_id', 'source')
        output_required = ('is_valid',)
        output_optional = ('details',)

    def handle(self):
        result = RuntimeConfigManager(self.server).validate(self.request.input.source)

        self.response.payload.is_valid = result.is_valid
        self.response.payload.details = result.details
