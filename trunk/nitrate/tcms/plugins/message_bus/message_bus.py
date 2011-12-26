# -*- coding: utf-8 -*-

import settings

from qpid.messaging import Connection

from tcms.plugins.message_bus.outgoing_message import OutgoingMessage

class MessageBus(object):
    ''' Core message bus '''

    _connection = None
    _session = None
    _sender = None

    @classmethod
    def initialize(cls):
        if not cls._connection:
            cls._connection = Connection(
                host = settings.BROKER_CONNECTION_INFO['host'],
                port = settings.BROKER_CONNECTION_INFO['port'],
                sasl_mechanisms = settings.BROKER_CONNECTION_INFO['sasl_mechanisms'])
            cls._connection.open()
            cls._session = cls._connection.session()
            cls._sender = cls._session.sender(settings.SENDER_ADDRESS)

    @classmethod
    def stop(cls):
        cls._session.close()
        cls._connection.close()
        cls._connection = None

    @classmethod
    def get_sender(cls):
        return cls._sender

    @classmethod
    def send(cls, msg_content, event_name, sync=True):
        o_msg = OutgoingMessage(raw_msg = msg_content, event_name = event_name)
        cls.get_sender().send(o_msg, sync=sync)

