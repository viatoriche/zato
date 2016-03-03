# -*- coding: utf-8 -*-

"""
Copyright (C) 2010 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

""" Views related to the management of server's scheduler jobs.
"""

# stdlib
import logging
from cStringIO import StringIO
from datetime import datetime
from traceback import format_exc

# anyjson
from anyjson import dumps

# dateutil
from dateutil.parser import parse

# Django
from django.http import HttpResponse, HttpResponseServerError
from django.template.response import TemplateResponse

# pytz
from pytz import UTC

# Zato
from zato.admin.web import from_user_to_utc, from_utc_to_user
from zato.admin.web.views import get_js_dt_format, get_sample_dt, method_allowed, Delete as _Delete
from zato.admin.settings import job_type_friendly_names
from zato.admin.web.forms.scheduler import CronStyleSchedulerJobForm, \
     IntervalBasedSchedulerJobForm, OneTimeSchedulerJobForm
from zato.common import SCHEDULER, TRACE1, ZatoException
from zato.common.odb.model import CronStyleJob, IntervalBasedJob, Job
from zato.common.util import pprint

logger = logging.getLogger(__name__)

create_one_time_prefix = 'create-one_time'
create_interval_based_prefix = 'create-interval_based'
create_cron_style_prefix = 'create-cron_style'
edit_one_time_prefix = 'edit-one_time'
edit_interval_based_prefix = 'edit-interval_based'
edit_cron_style_prefix = 'edit-cron_style'

def _get_start_date(start_date):
    if not start_date:
        return ''

    if not isinstance(start_date, datetime):
        start_date = parse(start_date)

    return start_date.replace(tzinfo=UTC)

def _one_time_job_def(user_profile, start_date):
    start_date = _get_start_date(start_date)
    return 'Execute once on {0} at {1}'.format(
        from_utc_to_user(start_date, user_profile, 'date'),
        from_utc_to_user(start_date, user_profile, 'time'))

def _interval_based_job_def(user_profile, start_date, repeats, weeks, days, hours, minutes, seconds):

    buf = StringIO()

    if start_date:
        buf.write('Start on {0} at {1}.'.format(
            from_utc_to_user(start_date, user_profile, 'date'),
            from_utc_to_user(start_date, user_profile, 'time')))

    if not repeats:
        buf.write(' Repeat indefinitely.')
    else:
        if repeats == 1:
            buf.write(' Execute once.')
        elif repeats == 2:
            buf.write(' Repeat twice.')
        # .. my hand is itching to add 'repeats thrice.' here ;-)
        elif repeats > 2:
            buf.write(' Repeat ')
            buf.write(str(repeats))
            buf.write(' times.')

    interval = []
    buf.write(' Interval: ')
    for name, value in (('week',weeks), ('day',days),
                    ('hour',hours), ('minute',minutes),
                    ('second',seconds)):
        if value:
            try:
                value = int(value)
            except ValueError:
                logger.warn('Cannot convert `%s` `%s` to an int, `%s` `%s` `%s` `%s` `%s` `%s` `%s`',
                    name, value, start_date, repeats, weeks, days, hours, minutes, seconds)
            else:
                interval.append('{0} {1}{2}'.format(value, name, 's' if value > 1 else ''))

    buf.write(', '.join(interval))
    buf.write('.')

    return buf.getvalue()

def _get_success_message(action, job_type, job_name):

    msg = 'Successfully {0} the {1} job [{2}]'
    verb = 'created' if action == 'create' else 'updated'
    job_type = job_type.replace('_', '-')

    return msg.format(verb, job_type, job_name)


def _cron_style_job_def(user_profile, start_date, cron_definition):
    start_date = _get_start_date(start_date)

    buf = StringIO()
    buf.write('Start on {0} at {1}.'.format(
        from_utc_to_user(start_date, user_profile, 'date'),
        from_utc_to_user(start_date, user_profile, 'time')))
    buf.write('<br/>{0}'.format(cron_definition))

    return buf.getvalue()

def _get_create_edit_message(user_profile, cluster, params, form_prefix=""):
    """ A dictionary of core data which can be used by both 'edit' and 'create'
    actions, regardless of the job's type.
    """
    start_date = params.get(form_prefix + 'start_date', '')
    if start_date:
        start_date = from_user_to_utc(start_date, user_profile)

    return {
        'name': params[form_prefix + 'name'],
        'cluster_id': cluster.id,
        'id': params.get(form_prefix + 'id', ''),
        'is_active': bool(params.get(form_prefix + 'is_active')),
        'service': params.get(form_prefix + 'service', ''),
        'extra': params.get(form_prefix + 'extra', ''),
        'start_date': start_date.isoformat(),
    }

def _get_create_edit_one_time_message(user_profile, cluster, params, form_prefix=''):
    """ Creates a base document which can be used by both 'edit' and 'create'
    actions. Used when creating one_time jobs.
    """
    input_dict = _get_create_edit_message(user_profile, cluster, params, form_prefix)
    input_dict['job_type'] = SCHEDULER.JOB_TYPE.ONE_TIME

    return input_dict

def _get_create_edit_interval_based_message(user_profile, cluster, params, form_prefix=''):
    """ A dictionary of core data which can be used by both 'edit' and 'create'
    actions. Used when creating interval_based jobs.
    """
    input_dict =_get_create_edit_message(user_profile, cluster, params, form_prefix)
    input_dict['job_type'] = SCHEDULER.JOB_TYPE.INTERVAL_BASED
    input_dict['weeks'] = params.get(form_prefix + 'weeks', '')
    input_dict['days'] = params.get(form_prefix + 'days', '')
    input_dict['hours'] = params.get(form_prefix + 'hours', '')
    input_dict['seconds'] = params.get(form_prefix + 'seconds', '')
    input_dict['minutes'] = params.get(form_prefix + 'minutes', '')
    input_dict['repeats'] = params.get(form_prefix + 'repeats', '')

    return input_dict

def _get_create_edit_cron_style_message(user_profile, cluster, params, form_prefix=''):
    """ A dictionary of core data which can be used by both 'edit' and 'create'
    actions. Used when creating cron_style jobs.
    """
    input_dict =_get_create_edit_message(user_profile, cluster, params, form_prefix)
    input_dict['job_type'] = SCHEDULER.JOB_TYPE.CRON_STYLE
    input_dict['cron_definition'] = params[form_prefix + 'cron_definition']

    return input_dict

def _create_one_time(client, user_profile, cluster, params):
    """ Creates a one_time scheduler job.
    """
    logger.debug('About to create a one_time job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

    input_dict = _get_create_edit_one_time_message(user_profile, cluster, params, create_one_time_prefix+'-')
    response = client.invoke('zato.scheduler.job.create', input_dict)

    logger.debug('Successfully created a one_time job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

    return {'id': response.data.id, 'definition_text':_one_time_job_def(user_profile, input_dict['start_date'])}

def _create_interval_based(client, user_profile, cluster, params):
    """ Creates an interval_based scheduler job.
    """
    logger.debug('About to create an interval_based job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

    input_dict = _get_create_edit_interval_based_message(user_profile, cluster, params, create_interval_based_prefix+'-')
    response = client.invoke('zato.scheduler.job.create', input_dict)
    logger.debug('Successfully created an interval_based job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

    start_date = input_dict.get('start_date')
    if start_date:
        start_date = _get_start_date(start_date)
    repeats = params.get('create-interval_based-repeats')
    weeks = params.get('create-interval_based-weeks')
    days = params.get('create-interval_based-days')
    hours = params.get('create-interval_based-hours')
    minutes = params.get('create-interval_based-minutes')
    seconds = params.get('create-interval_based-seconds')

    definition = _interval_based_job_def(user_profile, start_date, repeats, weeks, days, hours, minutes, seconds)

    return {'id': response.data.id, 'definition_text':definition}

def _create_cron_style(client, user_profile, cluster, params):
    """ Creates a cron_style scheduler job.
    """
    logger.debug('About to create a cron_style job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

    input_dict = _get_create_edit_cron_style_message(user_profile, cluster, params, create_cron_style_prefix+'-')
    response = client.invoke('zato.scheduler.job.create', input_dict)

    if response.ok:
        cron_definition = response.data.cron_definition
        logger.debug('Successfully created a cron_style job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

        return {'id': response.data.id,
                'definition_text':_cron_style_job_def(user_profile,
                    input_dict['start_date'], cron_definition),
                'cron_definition': cron_definition}
    else:
        raise Exception(response.details)

def _edit_one_time(client, user_profile, cluster, params):
    """ Updates a one_time scheduler job.
    """
    logger.debug('About to change a one_time job, cluster.id:[{0}, params:[{1}]]'.format(cluster.id, params))

    input_dict = _get_create_edit_one_time_message(user_profile, cluster, params, edit_one_time_prefix+'-')
    client.invoke('zato.scheduler.job.edit', input_dict)
    logger.debug('Successfully updated a one_time job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

    return {'definition_text':_one_time_job_def(user_profile, input_dict['start_date']), 'id':params['edit-one_time-id']}

def _edit_interval_based(client, user_profile, cluster, params):
    """ Creates an interval_based scheduler job.
    """
    logger.debug('About to change an interval_based job, cluster.id:[{0}, params:[{1}]]'.format(cluster.id, params))

    input_dict = _get_create_edit_interval_based_message(user_profile, cluster, params, edit_interval_based_prefix+'-')
    client.invoke('zato.scheduler.job.edit', input_dict)
    logger.debug('Successfully updated an interval_based job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

    start_date = input_dict.get('start_date')
    if start_date:
        start_date = _get_start_date(start_date)
    repeats = params.get('edit-interval_based-repeats')
    weeks = params.get('edit-interval_based-weeks')
    days = params.get('edit-interval_based-days')
    hours = params.get('edit-interval_based-hours')
    minutes = params.get('edit-interval_based-minutes')
    seconds = params.get('edit-interval_based-seconds')

    definition = _interval_based_job_def(user_profile, start_date, repeats, weeks, days, hours, minutes, seconds)

    return {'definition_text':definition, 'id':params['edit-interval_based-id']}

def _edit_cron_style(client, user_profile, cluster, params):
    """ Creates an cron_style scheduler job.
    """
    logger.debug('About to change a cron_style job, cluster.id:[{0}, params:[{1}]]'.format(cluster.id, params))

    input_dict = _get_create_edit_cron_style_message(user_profile, cluster, params, edit_cron_style_prefix+'-')
    response = client.invoke('zato.scheduler.job.edit', input_dict)

    if response.ok:
        cron_definition = response.data.cron_definition
        logger.debug('Successfully updated a cron_style job, cluster.id:[{0}], params:[{1}]'.format(cluster.id, params))

        start_date = _get_start_date(input_dict.get('start_date'))
        definition = _cron_style_job_def(user_profile, start_date, cron_definition)

        return {'definition_text':definition, 'cron_definition': cron_definition, 'id':params['edit-cron_style-id']}
    else:
        raise Exception(response.details)

@method_allowed('GET', 'POST')
def index(req):
    try:
        jobs = []

        # Build a list of schedulers for a given Zato cluster.
        if req.zato.cluster_id and req.method == 'GET':

            # We have a server to pick the schedulers from, try to invoke it now.
            response = req.zato.client.invoke('zato.scheduler.job.get-list', {'cluster_id': req.zato.cluster_id})

            if response.has_data:
                for job_elem in response.data:

                    id = job_elem.id
                    name = job_elem.name
                    is_active = job_elem.is_active
                    job_type = job_elem.job_type
                    start_date = job_elem.start_date
                    service_name = job_elem.service_name
                    extra = job_elem.extra
                    job_type_friendly = job_type_friendly_names[job_type]

                    job = Job(id, name, is_active, job_type,
                              from_utc_to_user(start_date+'+00:00', req.zato.user_profile),
                              extra, service_name=service_name,
                              job_type_friendly=job_type_friendly)

                    if job_type == SCHEDULER.JOB_TYPE.ONE_TIME:
                        definition_text=_one_time_job_def(req.zato.user_profile, start_date)

                    elif job_type == SCHEDULER.JOB_TYPE.INTERVAL_BASED:
                        definition_text = _interval_based_job_def(req.zato.user_profile,
                            _get_start_date(job_elem.start_date),
                            job_elem.repeats, job_elem.weeks, job_elem.days,
                            job_elem.hours, job_elem.minutes, job_elem.seconds)

                        weeks = job_elem.weeks or ''
                        days = job_elem.days or ''
                        hours = job_elem.hours or ''
                        minutes = job_elem.minutes or ''
                        seconds = job_elem.seconds or ''
                        repeats = job_elem.repeats or ''

                        ib_job = IntervalBasedJob(None, None, weeks, days, hours, minutes,
                                            seconds, repeats)
                        job.interval_based = ib_job

                    elif job_type == SCHEDULER.JOB_TYPE.CRON_STYLE:
                        cron_definition = job_elem.cron_definition or ''
                        definition_text=_cron_style_job_def(req.zato.user_profile, start_date, cron_definition)

                        cs_job = CronStyleJob(None, None, cron_definition)
                        job.cron_style = cs_job

                    else:
                        msg = 'Unrecognized job type, name:[{0}], type:[{1}]'.format(name, job_type)
                        logger.error(msg)
                        raise ZatoException(msg)

                    job.definition_text = definition_text
                    jobs.append(job)
            else:
                logger.info('No jobs found, response:[{}]'.format(response))

        if req.method == 'POST':

            action = req.POST.get('zato_action', '')
            if not action:
                msg = 'req.POST contains no [zato_action] parameter.'
                logger.error(msg)
                return HttpResponseServerError(msg)

            job_type = req.POST.get('job_type', '')
            if action != 'execute' and not job_type:
                msg = 'req.POST contains no [job_type] parameter.'
                logger.error(msg)
                return HttpResponseServerError(msg)

            job_name = req.POST['{0}-{1}-name'.format(action, job_type)]

            # Try to match the action and a job type with an action handler..
            handler_name = '_' + action
            if action != 'execute':
                handler_name += '_' + job_type

            handler = globals().get(handler_name)
            if not handler:
                msg = ('No handler found for action [{0}], job_type:[{1}], '
                       'req.POST:[{2}], req.GET:[{3}].'.format(action, job_type,
                          pprint(req.POST), pprint(req.GET)))

                logger.error(msg)
                return HttpResponseServerError(msg)

            # .. invoke the action handler.
            try:
                response = handler(req.zato.client, req.zato.user_profile, req.zato.cluster, req.POST)
                response = response if response else ''
                if response:
                    response['message'] = _get_success_message(action, job_type, job_name)
                    response = dumps(response)
                return HttpResponse(response, content_type='application/javascript')
            except Exception, e:
                msg = ('Could not invoke action [%s], job_type:[%s], e:[%s]'
                       'req.POST:[%s], req.GET:[%s]') % (action, job_type,
                          format_exc(), pprint(req.POST), pprint(req.GET))

                logger.error(msg)
                return HttpResponseServerError(msg)

        return_data = {'zato_clusters':req.zato.clusters,
            'cluster_id':req.zato.cluster_id,
            'choose_cluster_form':req.zato.choose_cluster_form,
            'jobs':jobs,
            'friendly_names':job_type_friendly_names.items(),
            'create_one_time_form':OneTimeSchedulerJobForm(prefix=create_one_time_prefix),
            'create_interval_based_form':IntervalBasedSchedulerJobForm(prefix=create_interval_based_prefix),
            'create_cron_style_form':CronStyleSchedulerJobForm(prefix=create_cron_style_prefix),
            'edit_one_time_form':OneTimeSchedulerJobForm(prefix=edit_one_time_prefix),
            'edit_interval_based_form':IntervalBasedSchedulerJobForm(prefix=edit_interval_based_prefix),
            'edit_cron_style_form':CronStyleSchedulerJobForm(prefix=edit_cron_style_prefix),
            'sample_dt': get_sample_dt(req.zato.user_profile),
            }

        return_data.update(get_js_dt_format(req.zato.user_profile))

        return TemplateResponse(req, 'zato/scheduler.html', return_data)
    except Exception, e:
        msg = '<pre>Could not invoke the method, e:[{0}]</pre>'.format(format_exc(e))
        logger.error(msg)
        return HttpResponseServerError(msg)


class Delete(_Delete):
    url_name = 'scheduler-job-delete'
    error_message = 'Could not delete the job'
    service_name = 'zato.scheduler.job.delete'

@method_allowed('POST')
def execute(req, job_id, cluster_id):
    """ Executes a scheduler's job.
    """
    try:
        req.zato.client.invoke('zato.scheduler.job.execute', {'id':job_id})
    except Exception, e:
        msg = 'Could not execute the job. job_id:[{0}], cluster_id:[{1}], e:[{2}]'.format(job_id, cluster_id, format_exc(e))
        logger.error(msg)
        return HttpResponseServerError(msg)
    else:
        # 200 OK
        return HttpResponse()

@method_allowed('POST')
def get_definition(req, start_date, repeats, weeks, days, hours, minutes, seconds):
    start_date = _get_start_date(start_date)

    definition = _interval_based_job_def(start_date, repeats, weeks, days, hours, minutes, seconds)
    logger.log(TRACE1, 'definition:[{}]'.format(definition))

    return HttpResponse(definition)
