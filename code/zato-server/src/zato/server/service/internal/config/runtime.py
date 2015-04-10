# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging, os
from os import path as p
from stat import S_IMODE
from traceback import format_exc

# Zato
from zato.server.service.internal import AdminService, AdminSIO

logger = logging.getLogger(__name__)

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

    def _append(self, name, pickup_dir, full_path, access_rights, ):

        self.items.append({
            'name':name, 'full_path':full_path, 'access_rights':access_rights, 'pickup_dir':pickup_dir
        })

    def _get_info(self, path, parent_dir=None):

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

    def get_list(self):
        pass

    def validate(self, name, pickup_dir, source):
        pass

    def edit(self, name, pickup_dir, source):
        pass

    def create(self, name, pickup_dir, source):
        pass

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
        return RuntimeConfigManager(self.server).get_list()
