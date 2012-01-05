# -*- coding: utf-8 -*-

from threading import Lock

import settings

from qpid.messaging import Connection
from qpid.sasl import SASLError

from tcms.plugins.message_bus.outgoing_message import OutgoingMessage
from tcms.plugins.message_bus.util import refresh_HTTP_credential_cache

class MessageBus(object):
    ''' Core message bus '''

    _connection = None
    _session = None
    _sender = None

    _reinitializing_connection = False
    _pending_msgs = []

    @classmethod
    def initialize(cls):
        if not cls._connection:
            cls._connection = Connection(
                host = settings.BROKER_CONNECTION_INFO['host'],
                port = settings.BROKER_CONNECTION_INFO['port'],
                sasl_mechanisms = settings.BROKER_CONNECTION_INFO['sasl_mechanisms'],
                transport = settings.BROKER_CONNECTION_INFO['transport'])
            cls._connection.open()
            cls._session = cls._connection.session()
            cls._sender = cls._session.sender(settings.SENDER_ADDRESS)

    @classmethod
    def _reinitialize(cls):
        l = Lock()
        l.acqire()

        cls._reinitializing_connection = True

        # Clean current environment
        cls.stop()

        import subprocess
        subprocess.Popen('logger tcms.error %s' % str(msg), shell=True)

        # messages will be sent after message bus environment is reinitialized.
        cls._pend_message((msg_content, event_name, sync))

        refresh_HTTP_credential_cache()
        cls.initialize()

        cls._reinitializing_connection = False

        # Send all pending messages and then clear
        for msg_content, event_name, sync in cls._pending_msgs:
            cls.send(msg_content, event_name, sync)
        cls._clear_pending_messages()

        l.release()

    @classmethod
    def _pend_message(cls, msg):
        '''
        Storing messages temporarily. And they can be sent after the connection reinitialized.
        '''

        cls._pending_msgs.append(msg)

    @classmethod
    def _clear_pending_messages(cls):
        cls._pending_msgs = []

    @classmethod
    def stop(cls):
        cls._sender = None
        cls._session.close()
        cls._session = None
        cls._connection.close()
        cls._connection = None

    @classmethod
    def get_sender(cls):
        return cls._sender

    @classmethod
    def send(cls, msg_content, event_name, sync=True):
        o_msg = OutgoingMessage(raw_msg = msg_content, event_name = event_name)

        try:
            if cls._reinitializing_connection:
                cls._pend_message((msg_content, event_name, sync))
            else:
                cls.get_sender().send(o_msg, sync=sync)

        except SASLError, msg:
            ''' Handle the the of expiration HTTP's ticket. '''
            cls._reinitialize()
