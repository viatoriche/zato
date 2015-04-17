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
from django.template.response import TemplateResponse

# Zato
from zato.admin.web.forms.config.runtime import EditFileSourceForm
from zato.admin.web.views import Index as _Index, method_allowed

logger = logging.getLogger(__name__)

class ConfigItem(object):
    def __init__(self):
        self.name = ''
        self.full_path = ''
        self.access_rights = ''

class Index(_Index):
    method_allowed = 'GET'
    url_name = 'config-runtime'
    template = 'zato/config/runtime/index.html'
    service_name = 'tmp.runtime.get-list'
    output_class = ConfigItem

    class SimpleIO(_Index.SimpleIO):
        input_required = ('cluster_id',)
        output_required = ('name', 'full_path', 'access_rights', 'pickup_dir')
        output_repeated = True

    def handle(self):
        return {}

@method_allowed('GET')
def edit(req, name, pickup_dir, cluster_id):

    return_data = {
        'form': EditFileSourceForm({'source':'zzz'}),
        'name': name,
        'pickup_dir': pickup_dir,
        'cluster_id': cluster_id
    }

    return TemplateResponse(req, 'zato/config/runtime/edit.html', return_data)

@method_allowed('POST')
def edit_validate_save(req, name, pickup_dir, cluster_id):
    return 'zzz'