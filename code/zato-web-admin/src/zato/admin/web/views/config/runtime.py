# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging

# Django
from django.http import HttpResponse, HttpResponseServerError

# Zato
from zato.admin.web.views import Index as _Index, method_allowed

logger = logging.getLogger(__name__)

class ConfigItem(object):
    def __init__(self):
        self.name = ''
        self.full_path = ''

class Index(_Index):
    method_allowed = 'GET'
    url_name = 'config-runtime'
    template = 'zato/config/runtime/index.html'
    service_name = 'zato.config.runtime/get-list'
    output_class = ConfigItem

    class SimpleIO(_Index.SimpleIO):
        input_required = ('cluster_id',)
        output_required = ('name', 'full_path')
        output_repeated = True

    def handle(self):
        return {}

@method_allowed('GET')
def details(req, **kwargs):
    return 'zz'
