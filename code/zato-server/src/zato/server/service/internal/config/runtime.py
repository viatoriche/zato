# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.server.service.internal import AdminService, AdminSIO

class GetList(AdminService):
    """ Returns a list of run-time config files available.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_config_runtime_get_list_request'
        response_elem = 'zato_config_runtime_get_list_response'
        input_required = ('cluster_id',)
        output_required = ('name', 'full_path', 'access_rights')
        output_repeated = True

    def handle(self):
        pass
