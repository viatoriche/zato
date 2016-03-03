# -*- coding: utf-8 -*-

"""
Copyright (C) 2010 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Django
from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login
from django.views.static import serve as django_static_serve

# Zato
from zato.admin import settings
from zato.admin.web.views import account, cluster, http_soap, kvdb, load_balancer, main, scheduler, service, stats
from zato.admin.web.views.channel import amqp as channel_amqp
from zato.admin.web.views.channel import jms_wmq as channel_jms_wmq
from zato.admin.web.views.channel import zmq as channel_zmq
from zato.admin.web.views.cloud.aws import s3 as cloud_aws_s3
from zato.admin.web.views.cloud.openstack import swift as cloud_openstack_swift
from zato.admin.web.views.definition import amqp as def_amqp
from zato.admin.web.views.definition import cassandra as def_cassandra
from zato.admin.web.views.definition import jms_wmq as def_jms_wmq
from zato.admin.web.views.email import imap as email_imap
from zato.admin.web.views.email import smtp as email_smtp
from zato.admin.web.views.kvdb.data_dict import dictionary, impexp, translation
from zato.admin.web.views.message import json_pointer, namespace, xpath
from zato.admin.web.views.notif.cloud.openstack import swift as notif_cloud_openstack_swift
from zato.admin.web.views.notif import sql as notif_sql
from zato.admin.web.views.outgoing import amqp as out_amqp
from zato.admin.web.views.outgoing import ftp as out_ftp
from zato.admin.web.views.outgoing import jms_wmq as out_jms_wmq
from zato.admin.web.views.outgoing import odoo as out_odoo
from zato.admin.web.views.outgoing import sql as out_sql
from zato.admin.web.views.outgoing import zmq as out_zmq
from zato.admin.web.views.pubsub import topics as pubsub_topics
from zato.admin.web.views.pubsub import consumers as pubsub_consumers
from zato.admin.web.views.pubsub import message as pubsub_message
from zato.admin.web.views.pubsub import producers as pubsub_producers
from zato.admin.web.views.query import cassandra as query_cassandra
from zato.admin.web.views.search import es
from zato.admin.web.views.search import solr
from zato.admin.web.views.security import apikey, aws, basic_auth, ntlm, oauth, openstack as openstack_security, rbac, \
     tech_account, wss, xpath as xpath_sec
from zato.admin.web.views.security.tls import ca_cert as tls_ca_cert, channel as tls_channel, key_cert as tls_key_cert

urlpatterns = [

# ################################################################################################################################

    # Main URLs

# ################################################################################################################################

    url(r'^accounts/login/$',
         login, {'template_name': 'zato/login.html'}),
    url(r'^$',
        main.index_redirect),
    url(r'^zato/$',
        login_required(main.index), name='main-page'),
    url(r'^logout/$',
        login_required(main.logout), name='logout'),
    ]

# ################################################################################################################################

urlpatterns += [

    # User accounts

    url(r'^account/settings/basic/$',
        login_required(account.settings_basic), name='account-settings-basic'),
    url(r'^account/settings/basic/save/$',
        login_required(account.settings_basic_save), name='account-settings-basic-save'),
    ]

# ################################################################################################################################

urlpatterns += [

    # Clusters

    url(r'^zato/cluster/$',
        login_required(cluster.index), name='cluster'),
    url(r'^zato/cluster/edit/$',
        login_required(cluster.edit), name='cluster-edit'),
    url(r'^zato/cluster/delete/(?P<id>.*)/$',
        login_required(cluster.delete), name='cluster-delete'),
    url(r'^zato/cluster/servers-state/(?P<cluster_id>.*)$',
        login_required(cluster.get_servers_state), name='cluster-servers-state'),
    url(r'^zato/cluster/get/by-id/(?P<cluster_id>.*)$',
        login_required(cluster.get_by_id), name='cluster-get-by-id'),
    url(r'^zato/cluster/get/by-name/(?P<cluster_name>.*)/$',
        login_required(cluster.get_by_name), name='cluster-get-by-name'),
    url(r'^zato/cluster/servers/$',
        login_required(cluster.servers), name='cluster-servers'),
    url(r'^zato/cluster/servers/edit/$',
        login_required(cluster.servers_edit), name='cluster-servers-edit'),
    url(r'^zato/cluster/servers/load-balancer/(?P<action>.*)/(?P<server_id>.*)/$',
        login_required(cluster.servers_add_remove_lb), name='cluster-servers-add-remove-lb'),
    url(r'^zato/cluster/servers/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(cluster.ServerDelete()), name=cluster.ServerDelete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # Load balancer

    url(r'^zato/load-balancer/get-addresses/cluster/(?P<cluster_id>.*)/$',
        login_required(load_balancer.get_addresses), name='lb-get-addresses'),
    url(r'^zato/load-balancer/manage/cluster/(?P<cluster_id>\d+)/validate-save/$',
        login_required(load_balancer.validate_save), name='lb-manage-validate-save'),
    url(r'^zato/load-balancer/manage/cluster/(?P<cluster_id>.*)/$', login_required(load_balancer.manage), name='lb-manage'),
    url(r'^zato/load-balancer/manage/source-code/cluster/(?P<cluster_id>.*)/validate-save$',
        login_required(load_balancer.validate_save_source_code), name='lb-manage-source-code-validate-save'),
    url(r'^zato/load-balancer/manage/source-code/cluster/(?P<cluster_id>.*)/$',
        login_required(load_balancer.manage_source_code), name='lb-manage-source-code'),
    url(r'^zato/load-balancer/remote-command/(?P<cluster_id>.*)/$',
        login_required(load_balancer.remote_command), name='lb-remote-command'),
    ]

# ################################################################################################################################

urlpatterns += [

    # Services

    url(r'^zato/service/$',
        login_required(service.Index()), name=service.Index.url_name),
    url(r'^zato/service/details$',
        login_required(service.Index()), name=service.Index.url_name),
    url(r'^zato/service/last-stats/(?P<service_id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(service.last_stats), name='service-last-stats'),
    url(r'^zato/service/cluster/(?P<cluster_id>.*)/upload/$',
        login_required(service.package_upload), name='service-package-upload'),
    url(r'^zato/service/create/$',
        login_required(service.create), name='service-create'),
    url(r'^zato/service/edit/$',
        login_required(service.Edit()), name=service.Edit.url_name),
    url(r'^zato/service/invoke/(?P<name>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(service.invoke), name='service-invoke'),
    url(r'^zato/service/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(service.Delete()), name=service.Delete.url_name),
    url(r'^zato/service/overview/(?P<service_name>.*)/$',
        login_required(service.overview), name='service-overview'),
    url(r'^zato/service/invoker/(?P<service_name>.*)/$',
        login_required(service.invoker), name='service-invoker'),
    url(r'^zato/service/source-info/(?P<service_name>.*)/$',
        login_required(service.source_info), name='service-source-info'),
    url(r'^zato/service/wsdl/(?P<service_name>.*)/cluster/(?P<cluster_id>.*)/upload/$',
        login_required(service.wsdl_upload), name='service-wsdl-upload'),
    url(r'^zato/service/wsdl/(?P<service_name>.*)/cluster/(?P<cluster_id>.*)/download/$',
        login_required(service.wsdl_download), name='service-wsdl-download'),
    url(r'^zato/service/wsdl/(?P<service_name>.*)/$', login_required(service.wsdl), name='service-wsdl'),
    url(r'^zato/service/request-response/(?P<service_name>.*)/cluster/(?P<cluster_id>.*)/configure/$',
        login_required(service.request_response_configure), name='service-request-response-configure'),
    url(r'^zato/service/request-response/(?P<service_name>.*)/$',
        login_required(service.request_response), name='service-request-response'),
    url(r'^zato/service/slow-response/details/(?P<cid>.*)/(?P<service_name>.*)/$',
        login_required(service.slow_response_details), name='service-slow-response-details'),
    url(r'^zato/service/slow-response/(?P<service_name>.*)/$',
        login_required(service.slow_response), name='service-slow-response'),
    ]

# ################################################################################################################################

# Messages..

# ################################################################################################################################

urlpatterns += [

    # .. Namespace
    url(r'^zato/messages/namespace/$',
        login_required(namespace.Index()), name=namespace.Index.url_name),
    url(r'^zato/messages/namespace/create/$',
        login_required(namespace.Create()), name=namespace.Create.url_name),
    url(r'^zato/messages/namespace/edit/$',
        login_required(namespace.Edit()), name=namespace.Edit.url_name),
    url(r'^zato/messages/namespace/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(namespace.Delete()), name=namespace.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. XPath
    url(r'^zato/messages/xpath/$',
        login_required(xpath.Index()), name=xpath.Index.url_name),
    url(r'^zato/messages/xpath/create/$',
        login_required(xpath.Create()), name=xpath.Create.url_name),
    url(r'^zato/messages/xpath/edit/$',
        login_required(xpath.Edit()), name=xpath.Edit.url_name),
    url(r'^zato/messages/xpath/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(xpath.Delete()), name=xpath.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. JSON Pointer
    url(r'^zato/messages/json-pointer/$',
        login_required(json_pointer.Index()), name=json_pointer.Index.url_name),
    url(r'^zato/messages/json-pointer/create/$',
        login_required(json_pointer.Create()), name=json_pointer.Create.url_name),
    url(r'^zato/messages/json-pointer/edit/$',
        login_required(json_pointer.Edit()), name=json_pointer.Edit.url_name),
    url(r'^zato/messages/json-pointer/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(json_pointer.Delete()), name=json_pointer.Delete.url_name),
    ]

# ################################################################################################################################

#   Security..

# ################################################################################################################################

urlpatterns += [

    # .. API keys

    url(r'^zato/security/apikey/$',
        login_required(apikey.Index()), name=apikey.Index.url_name),
    url(r'^zato/security/apikey/$',
        login_required(apikey.Index()), name=apikey.Index.url_name),
    url(r'^zato/security/apikey/create/$',
        login_required(apikey.Create()), name=apikey.Create.url_name),
    url(r'^zato/security/apikey/edit/$',
        login_required(apikey.Edit()), name=apikey.Edit.url_name),
    url(r'^zato/security/apikey/change-password/$',
        login_required(apikey.change_password), name='security-apikey-change-password'),
    url(r'^zato/security/apikey/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(apikey.Delete()), name=apikey.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. AWS

    url(r'^zato/security/aws/$',
        login_required(aws.Index()), name=aws.Index.url_name),
    url(r'^zato/security/aws/$',
        login_required(aws.Index()), name=aws.Index.url_name),
    url(r'^zato/security/aws/create/$',
        login_required(aws.Create()), name=aws.Create.url_name),
    url(r'^zato/security/aws/edit/$',
        login_required(aws.Edit()), name=aws.Edit.url_name),
    url(r'^zato/security/aws/change-password/$',
        login_required(aws.change_password), name='security-aws-change-password'),
    url(r'^zato/security/aws/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(aws.Delete()), name=aws.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. HTTP Basic Auth

    url(r'^zato/security/basic-auth/$',
        login_required(basic_auth.Index()), name=basic_auth.Index.url_name),
    url(r'^zato/security/basic-auth/$',
        login_required(basic_auth.Index()), name=basic_auth.Index.url_name),
    url(r'^zato/security/basic-auth/create/$',
        login_required(basic_auth.Create()), name=basic_auth.Create.url_name),
    url(r'^zato/security/basic-auth/edit/$',
        login_required(basic_auth.Edit()), name=basic_auth.Edit.url_name),
    url(r'^zato/security/basic-auth/change-password/$',
        login_required(basic_auth.change_password), name='security-basic-auth-change-password'),
    url(r'^zato/security/basic-auth/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(basic_auth.Delete()), name=basic_auth.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. NTLM

    url(r'^zato/security/ntlm/$',
        login_required(ntlm.Index()), name=ntlm.Index.url_name),
    url(r'^zato/security/ntlm/$',
        login_required(ntlm.Index()), name=ntlm.Index.url_name),
    url(r'^zato/security/ntlm/create/$',
        login_required(ntlm.Create()), name=ntlm.Create.url_name),
    url(r'^zato/security/ntlm/edit/$',
        login_required(ntlm.Edit()), name=ntlm.Edit.url_name),
    url(r'^zato/security/ntlm/change-password/$',
        login_required(ntlm.change_password), name='security-ntlm-change-password'),
    url(r'^zato/security/ntlm/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(ntlm.Delete()), name=ntlm.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. OAuth

    url(r'^zato/security/oauth/$',
        login_required(oauth.Index()), name=oauth.Index.url_name),
    url(r'^zato/security/oauth/$',
        login_required(oauth.Index()), name=oauth.Index.url_name),
    url(r'^zato/security/oauth/create/$',
        login_required(oauth.Create()), name=oauth.Create.url_name),
    url(r'^zato/security/oauth/edit/$',
        login_required(oauth.Edit()), name=oauth.Edit.url_name),
    url(r'^zato/security/oauth/change-password/$',
        login_required(oauth.change_secret), name='security-oauth-change-secret'),
    url(r'^zato/security/oauth/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(oauth.Delete()), name=oauth.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. OpenStack security

    url(r'^zato/security/openstack_security/$',
        login_required(openstack_security.Index()), name=openstack_security.Index.url_name),
    url(r'^zato/security/openstack_security/$',
        login_required(openstack_security.Index()), name=openstack_security.Index.url_name),
    url(r'^zato/security/openstack_security/create/$',
        login_required(openstack_security.Create()), name=openstack_security.Create.url_name),
    url(r'^zato/security/openstack_security/edit/$',
        login_required(openstack_security.Edit()), name=openstack_security.Edit.url_name),
    url(r'^zato/security/openstack_security/change-password/$',
        login_required(openstack_security.change_password), name='security-openstack-change-password'),
    url(r'^zato/security/openstack_security/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(openstack_security.Delete()), name=openstack_security.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. RBAC - Roles

    url(r'^zato/security/rbac/role/$',
        login_required(rbac.role.Index()), name=rbac.role.Index.url_name),
    url(r'^zato/security/rbac/role/create/$',
        login_required(rbac.role.Create()), name=rbac.role.Create.url_name),
    url(r'^zato/security/rbac/role/edit/$',
        login_required(rbac.role.Edit()), name=rbac.role.Edit.url_name),
    url(r'^zato/security/rbac/role/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(rbac.role.Delete()), name=rbac.role.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. RBAC - Client roles

    url(r'^zato/security/rbac/client-role/$',
        login_required(rbac.client_role.Index()), name=rbac.client_role.Index.url_name),
    url(r'^zato/security/rbac/client-role/create/$',
        login_required(rbac.client_role.Create()), name=rbac.client_role.Create.url_name),
    url(r'^zato/security/rbac/client-role/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(rbac.client_role.Delete()), name=rbac.client_role.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. RBAC - Permissions

    url(r'^zato/security/rbac/permission/$',
        login_required(rbac.permission.Index()), name=rbac.permission.Index.url_name),
    url(r'^zato/security/rbac/permission/create/$',
        login_required(rbac.permission.Create()), name=rbac.permission.Create.url_name),
    url(r'^zato/security/rbac/permission/edit/$',
        login_required(rbac.permission.Edit()), name=rbac.permission.Edit.url_name),
    url(r'^zato/security/rbac/permission/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(rbac.permission.Delete()), name=rbac.permission.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. RBAC - Role Permissions

    url(r'^zato/security/rbac/role-permission/$',
        login_required(rbac.role_permission.Index()), name=rbac.role_permission.Index.url_name),
    url(r'^zato/security/rbac/role-permission/create/$',
        login_required(rbac.role_permission.Create()), name=rbac.role_permission.Create.url_name),
    url(r'^zato/security/rbac/role-permission/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(rbac.role_permission.Delete()), name=rbac.role_permission.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. Technical accounts

    url(r'^zato/security/tech-account/$',
        login_required(tech_account.Index()), name=tech_account.Index.url_name),
    url(r'^zato/security/tech-account/create/$',
        login_required(tech_account.Create()), name=tech_account.Create.url_name),
    url(r'^zato/security/tech-account/edit/$',
        login_required(tech_account.Edit()), name=tech_account.Edit.url_name),
    url(r'^zato/security/tech-account/change-password/$',
        login_required(tech_account.change_password), name='security-tech-account-change-password'),
    url(r'^zato/security/tech-account/get/by-id/(?P<tech_account_id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(tech_account.get_by_id), name='security-tech-account-get-by-id'),
    url(r'^zato/security/tech-account/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(tech_account.delete), name='security-tech-account-delete'),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. TLS - channel security based on client certificates

    url(r'^zato/security/tls/channel/$',
        login_required(tls_channel.Index()), name=tls_channel.Index.url_name),
    url(r'^zato/security/tls/channel/create/$',
        login_required(tls_channel.Create()), name=tls_channel.Create.url_name),
    url(r'^zato/security/tls/channel/edit/$',
        login_required(tls_channel.Edit()), name=tls_channel.Edit.url_name),
    url(r'^zato/security/tls/channel/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(tls_channel.Delete()), name='security-tls-channel-delete'),

    # .. TLS - keys and certificates Zato itself uses in outgoing connections

    url(r'^zato/security/tls/key-cert/$',
        login_required(tls_key_cert.Index()), name=tls_key_cert.Index.url_name),
    url(r'^zato/security/tls/key-cert/create/$',
        login_required(tls_key_cert.Create()), name=tls_key_cert.Create.url_name),
    url(r'^zato/security/tls/key-cert/edit/$',
        login_required(tls_key_cert.Edit()), name=tls_key_cert.Edit.url_name),
    url(r'^zato/security/tls/key-cert/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(tls_key_cert.Delete()), name='security-tls-key-cert-delete'),

    # .. TLS - CA certs signing off certificates of endpoints Zato services invoke

    url(r'^zato/security/tls/ca-cert/$',
        login_required(tls_ca_cert.Index()), name=tls_ca_cert.Index.url_name),
    url(r'^zato/security/tls/ca-cert/create/$',
        login_required(tls_ca_cert.Create()), name=tls_ca_cert.Create.url_name),
    url(r'^zato/security/tls/ca-cert/edit/$',
        login_required(tls_ca_cert.Edit()), name=tls_ca_cert.Edit.url_name),
    url(r'^zato/security/tls/ca-cert/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(tls_ca_cert.Delete()), name='security-tls-ca-cert-delete'),

    ]

# ################################################################################################################################

urlpatterns += [

    # .. WS-Security

    url(r'^zato/security/wss/$',
        login_required(wss.index), name='security-wss'),
    url(r'^zato/security/wss/create/$',
        login_required(wss.create), name='security-wss-create'),
    url(r'^zato/security/wss/edit/$',
        login_required(wss.edit), name='security-wss-edit'),
    url(r'^zato/security/wss/change-password/$',
        login_required(wss.change_password), name='security-wss-change-password'),
    url(r'^zato/security/wss/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(wss.Delete()), name=wss.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. XPath

    url(r'^zato/security/xpath/$',
        login_required(xpath_sec.Index()), name=xpath_sec.Index.url_name),
    url(r'^zato/security/xpath/$',
        login_required(xpath_sec.Index()), name=xpath_sec.Index.url_name),
    url(r'^zato/security/xpath/create/$',
        login_required(xpath_sec.Create()), name=xpath_sec.Create.url_name),
    url(r'^zato/security/xpath/edit/$',
        login_required(xpath_sec.Edit()), name=xpath_sec.Edit.url_name),
    url(r'^zato/security/xpath/change-password/$',
        login_required(xpath_sec.change_password), name='security-xpath-change-password'),
    url(r'^zato/security/xpath/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(xpath_sec.Delete()), name=xpath_sec.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # Scheduler

    url(r'^zato/scheduler/$', login_required(scheduler.index), name='scheduler'),
    url(r'^zato/scheduler/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(scheduler.Delete()), name=scheduler.Delete.url_name),
    url(r'^zato/scheduler/execute/(?P<job_id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(scheduler.execute), name='scheduler-job-execute'),
    url(r'^zato/scheduler/get-definition/(?P<start_date>.*)/(?P<repeat>.*)/'
        '(?P<weeks>.*)/(?P<days>.*)/(?P<hours>.*)/(?P<minutes>.*)/(?P<seconds>.*)/$',
        login_required(scheduler.get_definition), name='scheduler-job-get-definition'),
    ]

# ################################################################################################################################

#   Definitions

# ################################################################################################################################

urlpatterns += [

    # .. AMQP

    url(r'^zato/definition/amqp/$',
        login_required(def_amqp.Index()), name=def_amqp.Index.url_name),
    url(r'^zato/definition/amqp/create/$',
        login_required(def_amqp.Create()), name=def_amqp.Create.url_name),
    url(r'^zato/definition/amqp/edit/$',
        login_required(def_amqp.Edit()), name=def_amqp.Edit.url_name),
    url(r'^zato/definition/amqp/change-password/$',
        login_required(def_amqp.change_password), name='def-amqp-change-password'),
    url(r'^zato/definition/amqp/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(def_amqp.Delete()), name=def_amqp.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. Cassandra

    url(r'^zato/definition/cassandra/$',
        login_required(def_cassandra.Index()), name=def_cassandra.Index.url_name),
    url(r'^zato/definition/cassandra/create/$',
        login_required(def_cassandra.Create()), name=def_cassandra.Create.url_name),
    url(r'^zato/definition/cassandra/edit/$',
        login_required(def_cassandra.Edit()), name=def_cassandra.Edit.url_name),
    url(r'^zato/definition/cassandra/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(def_cassandra.Delete()), name=def_cassandra.Delete.url_name),
    url(r'^zato/definition/cassandra/change-password/$',
        login_required(def_cassandra.change_password), name='definition-cassandra-change-password'),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. JMS WebSphere MQ

    url(r'^zato/definition/jms-wmq/$',
        login_required(def_jms_wmq.Index()), name=def_jms_wmq.Index.url_name),
    url(r'^zato/definition/jms-wmq/create/$',
        login_required(def_jms_wmq.Create()), name=def_jms_wmq.Create.url_name),
    url(r'^zato/definition/jms-wmq/edit/$',
        login_required(def_jms_wmq.Edit()), name=def_jms_wmq.Edit.url_name),
    url(r'^zato/definition/jms-wmq/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(def_jms_wmq.Delete()), name=def_jms_wmq.Delete.url_name),
    ]

# ################################################################################################################################

#   Outgoing connections

# ################################################################################################################################

urlpatterns += [

    # .. AMQP

    url(r'^zato/outgoing/amqp/$',
        login_required(out_amqp.Index()), name=out_amqp.Index.url_name),
    url(r'^zato/outgoing/amqp/create/$',
        login_required(out_amqp.create), name='out-amqp-create'),
    url(r'^zato/outgoing/amqp/edit/$',
        login_required(out_amqp.edit), name='out-amqp-edit'),
    url(r'^zato/outgoing/amqp/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(out_amqp.Delete()), name=out_amqp.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. FTP

    url(r'^zato/outgoing/ftp/$',
        login_required(out_ftp.Index()), name=out_ftp.Index.url_name),
    url(r'^zato/outgoing/ftp/create/$',
        login_required(out_ftp.Create()), name=out_ftp.Create.url_name),
    url(r'^zato/outgoing/ftp/edit/$',
        login_required(out_ftp.Edit()), name=out_ftp.Edit.url_name),
    url(r'^zato/outgoing/ftp/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(out_ftp.Delete()), name=out_ftp.Delete.url_name),
    url(r'^zato/outgoing/ftp/change-password/$',
        login_required(out_ftp.change_password), name='out-ftp-change-password'),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. JMS WebSphere MQ

    url(r'^zato/outgoing/jms-wmq/$',
        login_required(out_jms_wmq.index), name='out-jms-wmq'),
    url(r'^zato/outgoing/jms-wmq/create/$',
        login_required(out_jms_wmq.create), name='out-jms-wmq-create'),
    url(r'^zato/outgoing/jms-wmq/edit/$',
        login_required(out_jms_wmq.edit), name='out-jms-wmq-edit'),
    url(r'^zato/outgoing/jms-wmq/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(out_jms_wmq.Delete()), name=out_jms_wmq.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. Odoo

    url(r'^zato/outgoing/odoo/$',
        login_required(out_odoo.Index()), name=out_odoo.Index.url_name),
    url(r'^zato/outgoing/odoo/create/$',
        login_required(out_odoo.Create()), name=out_odoo.Create.url_name),
    url(r'^zato/outgoing/odoo/edit/$',
        login_required(out_odoo.Edit()), name=out_odoo.Edit.url_name),
    url(r'^zato/outgoing/odoo/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(out_odoo.Delete()), name=out_odoo.Delete.url_name),
    url(r'^zato/outgoing/odoo/change-password/$',
        login_required(out_odoo.change_password), name='out-odoo-change-password'),
    url(r'^zato/outgoing/odoo/ping/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(out_odoo.ping), name='out-odoo-ping'),
    ]

# ################################################################################################################################

urlpatterns += [

    # SQL connection pools

    url(r'^zato/outgoing/sql/$',
        login_required(out_sql.index), name='out-sql'),
    url(r'^zato/outgoing/sql/create/$',
        login_required(out_sql.create), name='out-sql-create'),
    url(r'^zato/outgoing/sql/ping/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(out_sql.ping), name='out-sql-ping'),
    url(r'^zato/outgoing/sql/edit/$',
        login_required(out_sql.edit), name='out-sql-edit'),
    url(r'^zato/outgoing/sql/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(out_sql.Delete()), name=out_sql.Delete.url_name),
    url(r'^zato/outgoing/sql/change-password/$',
        login_required(out_sql.change_password), name='out-sql-change-password'),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. ZeroMQ
    url(r'^zato/outgoing/zmq/$',
        login_required(out_zmq.Index()), name=out_zmq.Index.url_name),
    url(r'^zato/outgoing/zmq/create/$',
        login_required(out_zmq.Create()), name=out_zmq.Create.url_name),
    url(r'^zato/outgoing/zmq/edit/$',
        login_required(out_zmq.Edit()), name=out_zmq.Edit.url_name),
    url(r'^zato/outgoing/zmq/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(out_zmq.Delete()), name=out_zmq.Delete.url_name),
    ]

# ################################################################################################################################

#   Channels

# ################################################################################################################################

urlpatterns += [

    # .. AMQP
    url(r'^zato/channel/amqp/$',
        login_required(channel_amqp.Index()), name=channel_amqp.Index.url_name),
    url(r'^zato/channel/amqp/create/$',
        login_required(channel_amqp.create), name='channel-amqp-create'),
    url(r'^zato/channel/amqp/edit/$',
        login_required(channel_amqp.edit), name='channel-amqp-edit'),
    url(r'^zato/channel/amqp/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(channel_amqp.Delete()), name=channel_amqp.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. JMS WebSphere MQ
    url(r'^zato/channel/jms-wmq/$',
        login_required(channel_jms_wmq.Index()), name=channel_jms_wmq.Index.url_name),
    url(r'^zato/channel/jms-wmq/create/$',
        login_required(channel_jms_wmq.create), name='channel-jms-wmq-create'),
    url(r'^zato/channel/jms-wmq/edit/$',
        login_required(channel_jms_wmq.edit), name='channel-jms-wmq-edit'),
    url(r'^zato/channel/jms-wmq/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(channel_jms_wmq.Delete()), name=channel_jms_wmq.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. ZeroMQ
    url(r'^zato/channel/zmq/$',
        login_required(channel_zmq.Index()), name=channel_zmq.Index.url_name),
    url(r'^zato/channel/zmq/create/$',
        login_required(channel_zmq.Create()), name=channel_zmq.Create.url_name),
    url(r'^zato/channel/zmq/edit/$',
        login_required(channel_zmq.Edit()), name=channel_zmq.Edit.url_name),
    url(r'^zato/channel/zmq/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(channel_zmq.Delete()), name=channel_zmq.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # HTTP/SOAP

    url(r'^zato/http-soap/$',
        login_required(http_soap.index), name='http-soap'),
    url(r'^zato/http-soap/details/(?P<connection>.*)/(?P<transport>.*)/(?P<id>.*)/(?P<name>.*)/(?P<cluster_id>.*)/$',
        login_required(http_soap.details), name='http-soap-details'),
    url(r'^zato/http-soap/audit/set-state/(?P<connection>.*)/(?P<transport>.*)/(?P<id>.*)/(?P<name>.*)/(?P<cluster_id>.*)/$',
        login_required(http_soap.audit_set_state), name='http-soap-audit-set-state'),
    url(r'^zato/http-soap/audit/set-config/(?P<connection>.*)/(?P<transport>.*)/(?P<id>.*)/(?P<name>.*)/(?P<cluster_id>.*)/$',
        login_required(http_soap.audit_set_config), name='http-soap-audit-set-config'),
    url(r'^zato/http-soap/audit/log/(?P<connection>.*)/(?P<transport>.*)/(?P<conn_id>.*)/(?P<conn_name>.*)/(?P<cluster_id>.*)/$',
        login_required(http_soap.audit_log), name='http-soap-audit-log'),
    url(r'^zato/http-soap/audit/item/(?P<connection>.*)/(?P<transport>.*)/(?P<conn_id>.*)/(?P<conn_name>.*)/(?P<cluster_id>.*)/(?P<id>.*)/$',
        login_required(http_soap.audit_item), name='http-soap-audit-item'),
    ]

# ################################################################################################################################

urlpatterns += [

    url(r'^zato/http-soap/create/$',
        login_required(http_soap.create), name='http-soap-create'),
    url(r'^zato/http-soap/edit/$',
        login_required(http_soap.edit), name='http-soap-edit'),
    url(r'^zato/http-soap/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(http_soap.delete), name='http-soap-delete'),
    url(r'^zato/http-soap/ping/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(http_soap.ping), name='http-soap-ping'),
    url(r'^zato/http-soap/reload-wsdl/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(http_soap.reload_wsdl), name='http-soap-reload-wsdl'),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. ZeroMQ

    url(r'^zato/channel/zmq/$',
        login_required(channel_zmq.Index()), name=channel_zmq.Index.url_name),
    url(r'^zato/channel/zmq/create/$',
        login_required(channel_zmq.Create()), name=channel_zmq.Create.url_name),
    url(r'^zato/channel/zmq/edit/$',
        login_required(channel_zmq.Edit()), name=channel_zmq.Edit.url_name),
    url(r'^zato/channel/zmq/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(channel_zmq.Delete()), name=channel_zmq.Delete.url_name),
    ]

# ################################################################################################################################

#   Search

# ################################################################################################################################

urlpatterns += [

    # .. ElasticSearch

    url(r'^zato/search/es/$',
        login_required(es.Index()), name=es.Index.url_name),
    url(r'^zato/search/es/create/$',
        login_required(es.Create()), name=es.Create.url_name),
    url(r'^zato/search/es/edit/$',
        login_required(es.Edit()), name=es.Edit.url_name),
    url(r'^zato/search/es/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(es.Delete()), name=es.Delete.url_name),

    # .. Solr

    url(r'^zato/search/solr/$',
        login_required(solr.Index()), name=solr.Index.url_name),
    url(r'^zato/search/solr/create/$',
        login_required(solr.Create()), name=solr.Create.url_name),
    url(r'^zato/search/solr/edit/$',
        login_required(solr.Edit()), name=solr.Edit.url_name),
    url(r'^zato/search/solr/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(solr.Delete()), name=solr.Delete.url_name),
    url(r'^zato/search/solr/ping/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(solr.ping), name='search-solr-ping'),

    ]

# ################################################################################################################################

#   Notifications

# ################################################################################################################################

urlpatterns += [

    # .. OpenStack Swift

    url(r'^zato/notif/cloud/openstack/swift/$',
        login_required(notif_cloud_openstack_swift.Index()), name=notif_cloud_openstack_swift.Index.url_name),
    url(r'^zato/notif/cloud/openstack/swift/create/$',
        login_required(notif_cloud_openstack_swift.Create()), name=notif_cloud_openstack_swift.Create.url_name),
    url(r'^zato/notif/cloud/openstack/swift/edit/$',
        login_required(notif_cloud_openstack_swift.Edit()), name=notif_cloud_openstack_swift.Edit.url_name),
    url(r'^zato/notif/cloud/openstack/swift/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(notif_cloud_openstack_swift.Delete()), name=notif_cloud_openstack_swift.Delete.url_name),

    url(r'^zato/notif/sql/$',
        login_required(notif_sql.Index()), name=notif_sql.Index.url_name),
    url(r'^zato/notif/sql/create/$',
        login_required(notif_sql.Create()), name=notif_sql.Create.url_name),
    url(r'^zato/notif/sql/edit/$',
        login_required(notif_sql.Edit()), name=notif_sql.Edit.url_name),
    url(r'^zato/notif/sql/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(notif_sql.Delete()), name=notif_sql.Delete.url_name),

    ]

# ################################################################################################################################

#   Query

# ################################################################################################################################

urlpatterns += [

    # .. Cassandra

    url(r'^zato/query/cassandra/$',
        login_required(query_cassandra.Index()), name=query_cassandra.Index.url_name),
    url(r'^zato/query/cassandra/create/$',
        login_required(query_cassandra.Create()), name=query_cassandra.Create.url_name),
    url(r'^zato/query/cassandra/edit/$',
        login_required(query_cassandra.Edit()), name=query_cassandra.Edit.url_name),
    url(r'^zato/query/cassandra/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(query_cassandra.Delete()), name=query_cassandra.Delete.url_name),
    ]

# ################################################################################################################################

#   E-mail

# ################################################################################################################################

urlpatterns += [

    # .. IMAP

    url(r'^zato/email/imap/$',
        login_required(email_imap.Index()), name=email_imap.Index.url_name),
    url(r'^zato/email/imap/create/$',
        login_required(email_imap.Create()), name=email_imap.Create.url_name),
    url(r'^zato/email/imap/edit/$',
        login_required(email_imap.Edit()), name=email_imap.Edit.url_name),
    url(r'^zato/email/imap/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(email_imap.Delete()), name=email_imap.Delete.url_name),
    url(r'^zato/email/imap/ping/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(email_imap.ping), name='imap-email-ping'),
    url(r'^zato/email/imap/change-password/$',
        login_required(email_imap.change_password), name='email-imap-change-password'),

    # .. SMTP

    url(r'^zato/email/smtp/$',
        login_required(email_smtp.Index()), name=email_smtp.Index.url_name),
    url(r'^zato/email/smtp/create/$',
        login_required(email_smtp.Create()), name=email_smtp.Create.url_name),
    url(r'^zato/email/smtp/edit/$',
        login_required(email_smtp.Edit()), name=email_smtp.Edit.url_name),
    url(r'^zato/email/smtp/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(email_smtp.Delete()), name=email_smtp.Delete.url_name),
    url(r'^zato/email/smtp/ping/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(email_smtp.ping), name='smtp-email-ping'),
    url(r'^zato/email/smtp/change-password/$',
        login_required(email_smtp.change_password), name='email-smtp-change-password'),

    ]

# ################################################################################################################################

#   Cloud

# ################################################################################################################################

urlpatterns += [

    # .. OpenStack - S3

    url(r'^zato/cloud/aws/s3/$',
        login_required(cloud_aws_s3.Index()), name=cloud_aws_s3.Index.url_name),
    url(r'^zato/cloud/aws/s3/create/$',
        login_required(cloud_aws_s3.Create()), name=cloud_aws_s3.Create.url_name),
    url(r'^zato/cloud/aws/s3/edit/$',
        login_required(cloud_aws_s3.Edit()), name=cloud_aws_s3.Edit.url_name),
    url(r'^zato/cloud/aws/s3/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(cloud_aws_s3.Delete()), name=cloud_aws_s3.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # .. OpenStack - Swift

    url(r'^zato/cloud/openstack/swift/$',
        login_required(cloud_openstack_swift.Index()), name=cloud_openstack_swift.Index.url_name),
    url(r'^zato/cloud/openstack/swift/create/$',
        login_required(cloud_openstack_swift.Create()), name=cloud_openstack_swift.Create.url_name),
    url(r'^zato/cloud/openstack/swift/edit/$',
        login_required(cloud_openstack_swift.Edit()), name=cloud_openstack_swift.Edit.url_name),
    url(r'^zato/cloud/openstack/swift/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(cloud_openstack_swift.Delete()), name=cloud_openstack_swift.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    # Key/value DB

    url(r'^zato/kvdb/remote-command/$',
        login_required(kvdb.remote_command), name='kvdb-remote-command'),
    url(r'^zato/kvdb/remote-command/execute/$',
        login_required(kvdb.remote_command_execute), name='kvdb-remote-command-execute'),
    url(r'^zato/kvdb/data-dict/dictionary/$',
        login_required(dictionary.Index()), name=dictionary.Index.url_name),
    url(r'^zato/kvdb/data-dict/dictionary/create/$',
        login_required(dictionary.Create()), name=dictionary.Create.url_name),
    url(r'^zato/kvdb/data-dict/dictionary/edit/$',
        login_required(dictionary.Edit()), name=dictionary.Edit.url_name),
    url(r'^zato/kvdb/data-dict/dictionary/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(dictionary.Delete()), name=dictionary.Delete.url_name),
    ]

# ################################################################################################################################

urlpatterns += [

    url(r'^zato/kvdb/data-dict/translation/$',
        login_required(translation.Index()), name=translation.Index.url_name),
    url(r'^zato/kvdb/data-dict/translation/create/$',
        login_required(translation.Create()), name=translation.Create.url_name),
    url(r'^zato/kvdb/data-dict/translation/edit/$',
        login_required(translation.Edit()), name=translation.Edit.url_name),
    url(r'^zato/kvdb/data-dict/translation/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(translation.Delete()), name=translation.Delete.url_name),
    url(r'^zato/kvdb/data-dict/translation/get-key-list/$',
        login_required(translation.get_key_list), name='kvdb-data-dict-translation-get-key-list'),
    url(r'^zato/kvdb/data-dict/translation/get-value-list/$',
        login_required(translation.get_value_list), name='kvdb-data-dict-translation-get-value-list'),
    url(r'^zato/kvdb/data-dict/translation/translate/$',
        login_required(translation.translate), name='kvdb-data-dict-translation-translate'),
    ]

# ################################################################################################################################

urlpatterns += [

    url(r'^zato/kvdb/data-dict/impexp/$',
        login_required(impexp.index), name='kvdb-data-dict-impexp'),
    url(r'^zato/kvdb/data-dict/impexp/cluster/(?P<cluster_id>.*)/import/$',
        login_required(impexp.import_), name='kvdb-data-dict-impexp-import'),
    url(r'^zato/kvdb/data-dict/impexp/cluster/(?P<cluster_id>.*)/export/$',
        login_required(impexp.export), name='kvdb-data-dict-impexp-export'),
    ]

# ################################################################################################################################

#   Pub/sub

urlpatterns += [

    url(r'^zato/pubsub/consumers/cluster/(?P<cluster_id>.*)/topic/(?P<topic_name>.*)$',
        login_required(pubsub_consumers.Index()), name=pubsub_consumers.Index.url_name),
    url(r'^zato/pubsub/consumers/create/$',
        login_required(pubsub_consumers.Create()), name=pubsub_consumers.Create.url_name),
    url(r'^zato/pubsub/consumers/edit/$',
        login_required(pubsub_consumers.Edit()), name=pubsub_consumers.Edit.url_name),
    url(r'^zato/pubsub/consumers/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(pubsub_consumers.Delete()), name=pubsub_consumers.Delete.url_name),
    url(r'^zato/pubsub/consumers/clear/(?P<queue_type>.*)/(?P<client_id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(pubsub_consumers.clear_queue), name='pubsub-consumers-clear-queue'),

    url(r'^zato/pubsub/message/cluster/(?P<cluster_id>.*)/consumer-queue/(?P<sub_key>\w+)/(?P<topic_name>.*)$',
        login_required(pubsub_message.index_consumer_queue), name='pubsub-message-consumer-queue'),
    url(r'^zato/pubsub/message/cluster/(?P<cluster_id>.*)/topic/(?P<topic_name>.*)$',
        login_required(pubsub_message.index_topic), name='pubsub-message-topic'),
    url(r'^zato/pubsub/message/(?P<source_type>[a-z\-]+)/msg/(?P<msg_id>\w+)/cluster/(?P<cluster_id>\w+)/topic/(?P<topic_name>.*)$',
        login_required(pubsub_message.details), name='pubsub-message-details'),
    url(r'^zato/pubsub/message/delete/$',
        login_required(pubsub_message.delete), name='pubsub-message-delete'),

    url(r'^zato/pubsub/topics/publish/cluster/(?P<cluster_id>.*)/topic/(?P<topic>.*)$',
        login_required(pubsub_topics.publish), name='pubsub-topics-publish'),
    url(r'^zato/pubsub/topics/publish/action/cluster/(?P<cluster_id>.*)/topic/(?P<topic>.*)$',
        login_required(pubsub_topics.publish_action), name='pubsub-topics-publish-action'),

    url(r'^zato/pubsub/producers/cluster/(?P<cluster_id>.*)/topic/(?P<topic_name>.*)$',
        login_required(pubsub_producers.Index()), name=pubsub_producers.Index.url_name),
    url(r'^zato/pubsub/producers/create/$',
        login_required(pubsub_producers.Create()), name=pubsub_producers.Create.url_name),
    url(r'^zato/pubsub/producers/edit/$',
        login_required(pubsub_producers.Edit()), name=pubsub_producers.Edit.url_name),
    url(r'^zato/pubsub/producers/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(pubsub_producers.Delete()), name=pubsub_producers.Delete.url_name),

    url(r'^zato/pubsub/topics/$',
        login_required(pubsub_topics.Index()), name=pubsub_topics.Index.url_name),
    url(r'^zato/pubsub/topics/create/$',
        login_required(pubsub_topics.Create()), name=pubsub_topics.Create.url_name),
    url(r'^zato/pubsub/topics/edit/$',
        login_required(pubsub_topics.Edit()), name=pubsub_topics.Edit.url_name),
    url(r'^zato/pubsub/topics/delete/(?P<id>.*)/cluster/(?P<cluster_id>.*)/$',
        login_required(pubsub_topics.Delete()), name=pubsub_topics.Delete.url_name),

    # Statistics

    url(r'^zato/stats/trends/data/$',
        login_required(stats.stats_trends_data), name='stats-trends-data'),
    url(r'^zato/stats/trends/(?P<choice>.*)/$',
        login_required(stats.trends), name='stats-trends'),
    url(r'^zato/stats/summary/data/$',
        login_required(stats.stats_summary_data), name='stats-summary-data'),
    url(r'^zato/stats/summary/(?P<choice>.*)/$',
        login_required(stats.summary), name='stats-summary'),
    url(r'^zato/stats/settings/$',
        login_required(stats.settings), name='stats-settings'),
    url(r'^zato/stats/settings/save/$',
        login_required(stats.settings_save), name='stats-settings-save'),
    url(r'^zato/stats/maintenance/$',
        login_required(stats.maintenance), name='stats-maintenance'),
    url(r'^zato/stats/maintenance/delete/$',
        login_required(stats.maintenance_delete), name='stats-maintenance-delete'),
    ]

# ################################################################################################################################

urlpatterns += [

    # OpenID
    url('^openid/', include('django_openid_auth.urls')),
    ]

# ################################################################################################################################

if settings.DEBUG:
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', django_static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]
