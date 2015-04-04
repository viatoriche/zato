# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import os
from os import path as p
from stat import S_IMODE
from traceback import format_exc

# Zato
from zato.server.service.internal import AdminService, AdminSIO

class GetList(AdminService):
    """ Returns a list of run-time config files available.
    """
    name = 'tmp.runtime.get-list'
    class SimpleIO(AdminSIO):
        request_elem = 'zato_config_runtime_get_list_request'
        response_elem = 'zato_config_runtime_get_list_response'
        input_required = ('cluster_id',)
        output_required = ('name',)
        output_optional = ('full_path', 'access_rights')
        output_repeated = True

    def handle(self):
        for name, path in sorted(self.server.fs_server_config.runtime_config.iteritems()):
            if name != 'pickup_dir':

                if not p.isabs(path):
                    full_path = p.abspath(p.normpath(p.join(self.server.repo_location, path)))
                else:
                    full_path = path

                try:
                    access_rights = oct(S_IMODE(os.stat(full_path).st_mode))
                except OSError, e:
                    self.logger.warn('Could not stat `%s` (%s), e:`%s`', full_path, name, format_exc(e))
                    access_rights = None

                self.response.payload.append({'name':name, 'full_path':full_path, 'access_rights':access_rights})

