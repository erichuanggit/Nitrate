# -*- coding: utf-8 -*-

import os
from threading import Lock

import settings

from qpid.messaging import Connection
from qpid.messaging.exceptions import AuthenticationFailure
from qpid.sasl import SASLError

from tcms.plugins.message_bus.outgoing_message import OutgoingMessage
from tcms.plugins.message_bus.utils import refresh_HTTP_credential_cache

class MessageBus(object):
    ''' Core message bus '''

    _connection = None
    _session = None
    _sender = None

    _reinitializing_connection = False
    _pending_msgs = []

    # Protect the connection initializatin to ensure that
    # only one thread within a Apache child process can establish connection to QPID broker.
    _lock_for_initialize_connection = Lock()

    def _initialize_connection_if_necessary(self):
        MessageBus._lock_for_initialize_connection.acquire()

        if MessageBus._connection == None:
            ev_krb5ccname = 'KRB5CCNAME'
            old_ccache = os.getenv(ev_krb5ccname)
            new_ccache = refresh_HTTP_credential_cache()
            os.environ[ev_krb5ccname] = 'FILE:%s' % new_ccache

            MessageBus._connection = Connection(
                host = settings.BROKER_CONNECTION_INFO['host'],
                port = settings.BROKER_CONNECTION_INFO['port'],
                sasl_mechanisms = settings.BROKER_CONNECTION_INFO['sasl_mechanisms'],
                transport = settings.BROKER_CONNECTION_INFO['transport'])
            MessageBus._connection.open()

            if old_ccache:
                os.environ[ev_krb5ccname] = old_ccache

            MessageBus._session = MessageBus._connection.session()
            MessageBus._sender = MessageBus._session.sender(settings.SENDER_ADDRESS)

        MessageBus._lock_for_initialize_connection.release()

    def _reinitialize(self, last_undelivered_msg=None):
        l = Lock()
        l.acqire()

        import subprocess

        subprocess.Popen('logger "tcms.debug begin reinitialize"', shell=True)

        MessageBus._reinitializing_connection = True

        # Clean current environment
        self.stop()

        # messages will be sent after message bus environment is reinitialized.

        subprocess.Popen('logger "tcms.debug pending message: %s"' % str(last_undelivered_msg), shell=True)
        self._pend_message(last_undelivered_msg)

        #refresh_HTTP_credential_cache()
        self._initialize_connection_if_necessary()

        MessageBus._reinitializing_connection = False

        # Send all pending messages and then clear
        for msg_content, event_name, sync in MessageBus._pending_msgs:
            self.send(msg_content, event_name, sync)
        self._clear_pending_messages()

        l.release()

    def _pend_message(self, msg):
        '''
        Storing messages temporarily. And they can be sent after the connection reinitialized.
        '''

        MessageBus._pending_msgs.append(msg)

    def _clear_pending_messages(self):
        MessageBus._pending_msgs = []

    def stop(self):
        if MessageBus._sender is not None:
            MessageBus._sender = None

        if MessageBus._session is not None:
            MessageBus._session.close()
            MessageBus._session = None

        if MessageBus._connection is not None:
            MessageBus._connection.close()
            MessageBus._connection = None

    def get_sender(self):
        return MessageBus._sender

    def send(self, msg_content, event_name, sync=True):
        o_msg = OutgoingMessage(raw_msg = msg_content, event_name = event_name, content_type='amqp/map')

        try:
            if MessageBus._reinitializing_connection:
                self._pend_message((msg_content, event_name, sync))
            else:
                self._initialize_connection_if_necessary()
                self.get_sender().send(o_msg, sync=sync)

        except SASLError, msg:
            ''' Handle the the of expiration HTTP's ticket. '''
            self._reinitialize((msg_content, event_name, sync))
