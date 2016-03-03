# -*- coding: utf-8 -*-

"""
Copyright (C) 2010 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging
from json import dumps
from traceback import format_exc

# Django
from django.http import HttpResponse, HttpResponseServerError
from django.template.response import TemplateResponse

# Zato
from zato.admin.web.forms import ChangePasswordForm
from zato.admin.web.forms.security.wss import CreateForm, EditForm
from zato.admin.web.views import change_password as _change_password, Delete as _Delete, method_allowed
from zato.common import ZATO_WSS_PASSWORD_TYPES
from zato.common.odb.model import WSSDefinition

logger = logging.getLogger(__name__)

def _edit_create_response(service_response, action, name, password_type):
    return_data = {'id': service_response.data.id,
        'message': 'Successfully {0} the WS-Security definition [{1}]'.format(action, name),
        'password_type_raw':password_type,
        'password_type':ZATO_WSS_PASSWORD_TYPES[password_type]}

    return HttpResponse(dumps(return_data), content_type='application/javascript')

def _get_edit_create_message(params, prefix=''):
    """ Creates a base dictionary which can be used by both 'edit' and 'create' actions.
    """
    return {
        'id': params.get('id'),
        'cluster_id': params['cluster_id'],
        'name': params[prefix + 'name'],
        'is_active': bool(params.get(prefix + 'is_active')),
        'username': params[prefix + 'username'],
        'password_type': 'clear_text',
        'reject_empty_nonce_creat': bool(params.get(prefix + 'reject_empty_nonce_creat')),
        'reject_stale_tokens': bool(params.get(prefix + 'reject_stale_tokens')),
        'reject_expiry_limit': params[prefix + 'reject_expiry_limit'],
        'nonce_freshness_time': params[prefix + 'nonce_freshness_time'],
    }

@method_allowed('GET')
def index(req):
    items = []
    create_form = CreateForm()
    edit_form = EditForm(prefix='edit')
    change_password_form = ChangePasswordForm()

    if req.zato.cluster_id and req.method == 'GET':

        for item in req.zato.client.invoke('zato.security.wss.get-list', {'cluster_id':req.zato.cluster_id}):
            wss = WSSDefinition(item.id, item.name, item.is_active, item.username, None,
                    ZATO_WSS_PASSWORD_TYPES[item.password_type], item.reject_empty_nonce_creat,
                    item.reject_stale_tokens, item.reject_expiry_limit, item.nonce_freshness_time,
                    password_type_raw=item.password_type)

            items.append(wss)

    return_data = {'zato_clusters':req.zato.clusters,
        'cluster_id':req.zato.cluster_id,
        'choose_cluster_form':req.zato.choose_cluster_form,
        'items':items,
        'create_form': create_form,
        'edit_form': edit_form,
        'change_password_form': change_password_form
        }

    return TemplateResponse(req, 'zato/security/wss.html', return_data)

@method_allowed('POST')
def edit(req):
    """ Updates WS-S definitions's parameters (everything except for the password).
    """
    try:
        response = req.zato.client.invoke('zato.security.wss.edit', _get_edit_create_message(req.POST, prefix='edit-'))
        return _edit_create_response(response, 'updated', req.POST['edit-name'], req.POST['edit-password_type'])
    except Exception, e:
        msg = 'Could not update the WS-Security definition, e:[{e}]'.format(e=format_exc(e))
        logger.error(msg)
        return HttpResponseServerError(msg)

@method_allowed('POST')
def create(req):
    try:
        response = req.zato.client.invoke('zato.security.wss.create', _get_edit_create_message(req.POST))
        return _edit_create_response(response, 'created', req.POST['name'], req.POST['password_type'])
    except Exception, e:
        msg = "Could not create a WS-Security definition, e:[{e}]".format(e=format_exc(e))
        logger.error(msg)
        return HttpResponseServerError(msg)

class Delete(_Delete):
    url_name = 'security-wss-delete'
    error_message = 'Could not delete the WS-Security definition'
    service_name = 'zato.security.wss.delete'

@method_allowed('POST')
def change_password(req):
    return _change_password(req, 'zato.security.wss.change-password')
