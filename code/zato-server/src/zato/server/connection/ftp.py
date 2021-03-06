# -*- coding: utf-8 -*-

"""
Copyright (C) 2011 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging
from copy import deepcopy
from threading import RLock
from traceback import format_exc

# pyfilesystem
from fs.ftpfs import FTPFS, _GLOBAL_DEFAULT_TIMEOUT

# Zato
from zato.common import Inactive, SECRET_SHADOW, TRACE1

logger = logging.getLogger(__name__)

class FTPFacade(FTPFS):
    """ A thin wrapper around fs's FTPFS so it looks like the other Zato connection objects.
    """
    def conn(self):
        return self

class FTPStore(object):
    """ An object through which services access FTP connections.
    """
    def __init__(self):
        self.conn_params = {}
        self._lock = RLock()

    def _add(self, params):
        """ Adds one set of params to the list of connection parameters. Must not
        be called without holding onto self._lock
        """
        self.conn_params[params.name] = params

        msg = 'FTP params added:[{!r}]'

        if logger.isEnabledFor(TRACE1):
            logger.log(TRACE1, msg.format(params))

        elif logger.isEnabledFor(logging.DEBUG):
            params = deepcopy(params)
            params['password'] = SECRET_SHADOW
            logger.debug(params)

    def add_params(self, params_list):
        with self._lock:
            for params in params_list:
                self._add(params)

    def get_conn_names(self):
        """ Returns a list of UTF-8 connection names this store contains,
        sorted in ascending order.
        """
        with self._lock:
            return [elem.encode('utf-8') for elem in sorted(self.conn_params)]

    def get(self, name):
        with self._lock:
            params = self.conn_params[name]
            if params.is_active:
                timeout = float(params.timeout) if params.timeout else _GLOBAL_DEFAULT_TIMEOUT
                return FTPFacade(params.host, params.user, params.get('password'), params.acct, timeout, int(params.port), params.dircache)
            else:
                raise Inactive(params.name)

    def create_edit(self, params, old_name):
        with self._lock:
            if params:
                _name = old_name if old_name else params.name
                ftp = params.get(_name)
                try:
                    if ftp:
                        ftp.close()
                except Exception, e:
                    msg = 'Could not close the FTP connection [{0}], e [{1}]'.format(params.name, format_exc(e))
                    logger.warn(msg)
                finally:
                    self._add(params)

            if old_name and old_name != params.name:
                del self.conn_params[old_name]

            msg = 'FTP connection stored, name:[{}], old_name:[{}]'.format(params.name, old_name)
            logger.info(msg)

    def change_password(self, name, password):
        with self._lock:
            self.conn_params[name].password = password
            logger.info('Password updated - FTP connection [{}]'.format(name))

    def delete(self, name):
        with self._lock:
            del self.conn_params[name]
            logger.info('FTP connection [{}] deleted'.format(name))
