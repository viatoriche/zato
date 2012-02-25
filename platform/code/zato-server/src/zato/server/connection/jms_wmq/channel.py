# -*- coding: utf-8 -*-

"""
Copyright (C) 2011 Dariusz Suchojad <dsuch at gefira.pl>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import errno, logging, os, socket, sys
from copy import deepcopy
from multiprocessing import Process
from threading import RLock, Thread
from traceback import format_exc

# Pika
from pika import BasicProperties

# Bunch
from bunch import Bunch

# Spring Python
from springpython.jms import WebSphereMQJMSException, NoMessageAvailableException
from springpython.jms.core import reserved_attributes
from springpython.jms.listener import MessageHandler, SimpleMessageListenerContainer

# Zato
from zato.common import ConnectionException, PORTS
from zato.common.broker_message import CHANNEL, DEFINITION, JMS_WMQ_CONNECTOR, MESSAGE_TYPE
from zato.common.util import new_rid, TRACE1
from zato.server.connection import setup_logging, start_connector as _start_connector
from zato.server.connection.jms_wmq import BaseJMSWMQConnection, BaseJMSWMQConnector

ENV_ITEM_NAME = 'ZATO_CONNECTOR_JMS_WMQ_CHANNEL_ID'

# Spring Python's 'text' is our 'payload' hence we need to do away with the 'text' attribute.
# In addition to that, we also need to get rid of all the magic methods.

MESSAGE_ATTRS = deepcopy(reserved_attributes)
MESSAGE_ATTRS.remove('text')
MESSAGE_ATTRS = MESSAGE_ATTRS - set(dir(object) + ["__weakref__", "__dict__", "__module__"])

class ConsumingConnection(BaseJMSWMQConnection):
    def __init__(self, factory, name, queue, callback):
        super(ConsumingConnection, self).__init__(factory, name)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queue = queue
        self.callback = callback
        self.keep_listening = False
        
    def _close(self):
        self.keep_listening = False
        super(ConsumingConnection, self)._close()
        
    def _on_connected(self):
        super(ConsumingConnection, self)._on_connected()
        
        self.keep_listening = True
        self.logger.debug('Starting listener for [{0}]'.format(self._conn_info()))
        
        while self.keep_listening:
            try:
                msg = self.factory.receive(self.queue, 1000)
                self.logger.log(TRACE1, 'Message received [{0}]'.format(str(msg).decode("utf-8")))
                
                if msg:
                    self.callback(msg)
                
            except NoMessageAvailableException, e:
                self.logger.log(TRACE1, 'No messages [{0}], queue [{1}]'.format(
                    self._conn_info(), self.queue))
                
            except WebSphereMQJMSException, e:
                self.logger.error('Caught [{0}], e.completion_code [{1}], '
                    'e.reason_code [{2}]'.format(format_exc(e), e.completion_code, e.reason_code))
              
                self.keep_listening = False
                self.close()
                
                self.factory._disconnecting = False
                self.keep_connecting = True
                self.start()
            except Exception, e:
                log_msg = 'Caught an exception [{0}]'.format(format_exc(e))
                self.logger.error(log_msg)
                raise 
        
class ConsumingConnector(BaseJMSWMQConnector):
    """ An AMQP consuming connector started as a subprocess. Each connection to an AMQP
    broker gets its own connector.
    """
    def __init__(self, repo_location=None, def_id=None, channel_id=None, init=True):
        super(ConsumingConnector, self).__init__(repo_location, def_id)
        self.broker_client_name = 'jms-wmq-consuming-connector'
        self.logger = logging.getLogger(self.__class__.__name__)
        self.channel_id = channel_id
        
        self.channel_lock = RLock()
        self.def_lock = RLock()
        
        self.def_ = Bunch()
        self.channel = Bunch()
        
        self.broker_push_client_pull_port = PORTS.BROKER_PUSH_CONSUMING_CONNECTOR_JMS_WMQ_PULL
        self.client_push_broker_pull_port = PORTS.CONSUMING_CONNECTOR_JMS_WMQ_PUSH_BROKER_PULL
        self.broker_pub_client_sub_port = PORTS.BROKER_PUB_CONSUMING_CONNECTOR_JMS_WMQ_SUB
        
        if init:
            self._init()
            self._setup_connector()
            
    def filter(self, msg):
        """ Can we handle the incoming message?
        """
        if super(ConsumingConnector, self).filter(msg):
            return True
            
        elif msg.action in(CHANNEL.JMS_WMQ_DELETE, CHANNEL.JMS_WMQ_EDIT):
            return self.channel.id == msg['id']
        
    def _setup_odb(self):
        super(ConsumingConnector, self)._setup_odb()
        
        item = self.odb.get_def_jms_wmq(self.server.cluster.id, self.def_id)
        self.def_.name = item.name
        self.def_.id = item.id
        self.def_.host = item.host
        self.def_.port = item.port
        self.def_.queue_manager = item.queue_manager
        self.def_.channel = item.channel
        self.def_.cache_open_send_queues = item.cache_open_send_queues
        self.def_.cache_open_receive_queues = item.cache_open_receive_queues
        self.def_.use_shared_connections = item.use_shared_connections
        self.def_.ssl = item.ssl
        self.def_.ssl_cipher_spec = item.ssl_cipher_spec
        self.def_.ssl_key_repository = item.ssl_key_repository
        self.def_.needs_mcd = item.needs_mcd
        self.def_.max_chars_printed = item.max_chars_printed
        
        item = self.odb.get_channel_jms_wmq(self.server.cluster.id, self.channel_id)
        self.channel.id = item.id
        self.channel.name = item.name
        self.channel.is_active = item.is_active
        self.channel.queue = str(item.queue)
        self.channel.service = item.service_name
        self.channel.listener = None
            
    def _recreate_listener(self):
        self._stop_connection()
        
        if self.channel.is_active:
            factory = self._get_factory()
            listener = self._listener(factory, self.channel.queue, self._on_message)
            self.channel.listener = listener

    def _listener(self, factory, queue, handler):
        """ Starts the listener in a new thread and returns it.
        """
        listener = ConsumingConnection(factory, self.channel.name, queue, handler)
        t = Thread(target=listener._run)
        t.start()
        
        return listener
        
    def _setup_connector(self):
        """ Sets up the connector on startup.
        """
        with self.def_lock:
            with self.channel_lock:
                self._recreate_listener()
            
    def _stop_connection(self):
        """ Stops the given channel's listener. The method must be called from 
        a method that holds onto all related RLocks.
        """
        if self.channel.get('listener'):
            listener = self.channel.listener
            listener.close()
            
    def _close_delete(self):
        """ Stops the connections, exits the process.
        """
        with self.def_lock:
            with self.channel_lock:
                self._stop_connection()
                self._close()
                
    def _on_message(self, msg):
        """ Invoked for each message taken off a WebSphere MQ queue.
        """
        with self.def_lock:
            with self.channel_lock:
                params = {}
                params['action'] = CHANNEL.JMS_WMQ_MESSAGE_RECEIVED
                params['service'] = self.channel.service
                params['rid'] = new_rid()
                params['payload'] = msg.text
                
                for attr in MESSAGE_ATTRS:
                    params[attr] = getattr(msg, attr, None)
                
                self.broker_client.send_json(params, msg_type=MESSAGE_TYPE.TO_PARALLEL_PULL)
                
    def on_broker_pull_msg_DEFINITION_JMS_WMQ_EDIT(self, msg, args=None):
        with self.def_lock:
            with self.channel_lock:
                self.def_ = msg
                self._recreate_listener()
                
    def on_broker_pull_msg_CHANNEL_JMS_WMQ_DELETE(self, msg, args=None):
        self._close_delete()
        
    def on_broker_pull_msg_CHANNEL_JMS_WMQ_EDIT(self, msg, args=None):
        with self.def_lock:
            with self.channel_lock:
                listener = self.channel.listener
                self.channel = msg
                self.channel.queue = str(self.channel.queue)
                self.channel.listener = listener
                self._recreate_listener()

def run_connector():
    """ Invoked on the process startup.
    """
    setup_logging()
    
    repo_location = os.environ['ZATO_REPO_LOCATION']
    def_id = os.environ['ZATO_CONNECTOR_DEF_ID']
    item_id = os.environ[ENV_ITEM_NAME]
    
    connector = ConsumingConnector(repo_location, def_id, item_id)
    
    logger = logging.getLogger(__name__)
    logger.debug('Starting JMS WebSphere MQ outgoing, repo_location [{0}], item_id [{1}], def_id [{2}]'.format(
        repo_location, item_id, def_id))
    
def start_connector(repo_location, item_id, def_id):
    _start_connector(repo_location, __file__, ENV_ITEM_NAME, def_id, item_id)
    
if __name__ == '__main__':
    run_connector()