# -*- coding: utf-8 -*-

import os
import subprocess
import sys

from threading import Lock

from qpid.messaging import Connection
from qpid.messaging.exceptions import ConnectionError
from qpid.messaging.exceptions import ConnectError
from qpid.messaging.exceptions import AuthenticationFailure
from qpid.sasl import SASLError

from tcms.plugins.message_bus import settings as st
from tcms.plugins.message_bus.outgoing_message import OutgoingMessage
from tcms.plugins.message_bus.utils import refresh_HTTP_credential_cache

errlog = sys.stderr
write_errlog = lambda log_content: errlog.write(log_content + os.linesep)

errlog_write = lambda log_content: errlog.write(log_content)
errlog_writeline = lambda log_content: errlog.write(log_content + os.linesep)

class MessageBus(object):
    ''' Core message bus '''

    _connection = None
    _session = None
    _sender = None

    _lock_for_open_connection = Lock()

    @property
    def connection(self):
        return self._connection

    @property
    def session(self):
        return self._session

    @property
    def sender(self):
        return self._sender

    @property
    def status(self):
        return self._status

    def __connect_with_gssapi(self):
        ev_krb5ccname = 'KRB5CCNAME'
        old_ccache = os.getenv(ev_krb5ccname, None)
        new_ccache = refresh_HTTP_credential_cache()
        os.environ[ev_krb5ccname] = 'FILE:%s' % new_ccache

        options = {
            'host':            st.QPID_BROKER_HOST,
            'port':            st.QPID_BROKER_PORT,
            'sasl_mechanisms': st.QPID_BROKER_SASL_MECHANISMS,
            'transport':       st.QPID_BROKER_TRANSPORT,
        }
        self._connection = Connection(**options)

        try:
            self._connection.open()
        finally:
            if old_ccache:
                os.environ[ev_krb5ccname] = old_ccache
            else:
                # OS has no KRB5CCNAME originally.
                # The current one is unncessary after establishing the connection
                del os.environ[ev_krb5ccname]

    def __connect_as_regular(self):
        options = {
            'host':            st.QPID_BROKER_HOST,
            'port':            st.QPID_BROKER_PORT,
            'sasl_mechanisms': st.QPID_BROKER_SASL_MECHANISMS,
            'transport':       st.QPID_BROKER_TRANSPORT,
            'username':        st.AUTH_USERNAME,
            'password':        st.AUTH_PASSWORD,
        }
        self._connection = Connection(**options)
        self._connection.open()

    if st.USING_GSSAPI:
        __connect_broker = __connect_with_gssapi
    else:
        __connect_broker = __connect_as_regular

    def __establish(self):
        '''
        Establish a connection to QPID broker actually.

        The connection to QPID broker is alive forever,
        unless the Apache is stopped, the broker is down,
        or even the network is unavialable.

        MessageBus also saves the session and sender for
        subsequent request of sending messages.
        '''

        self.__connect_broker()
        self._session = self._connection.session()
        self._sender = self._session.sender(st.SENDER_ADDRESS)

    def __connect_broker_if_necessary(self):
        '''
        Establishing connection to QPID broker.
        '''

        self._lock_for_open_connection.acquire()

        try:
            if not self.connection:
                self.__establish()
        finally:
            self._lock_for_open_connection.release()

    def stop(self):
        '''
        Stop the connection to the QPID broker.

        This can be considered to clear MessageBus' environment also.
        '''

        if self._sender is not None:
            self._sender = None

        if self._session is not None:
            self._session.close()
            self._session = None

        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def send(self, msg_content, event_name, sync=True):
        '''
        Send a message to QPID broker.

        The routing key consists of the prefix defined in settings and event_name.
        '''

        try:
            self.__connect_broker_if_necessary()

        except AuthenticationFailure, err:
            errlog_writeline('AuthenticationError. Please check settings\'s configuration ' \
                             'and your authentication environment. Error message: ' + str(err))

        except ConnectError, err:
            errlog_writeline('ConnectError. ' + str(err))
            return

        try:
            o_msg = OutgoingMessage(raw_msg = msg_content, event_name = event_name)
            self.sender.send(o_msg, sync=sync)

        except ConnectionError, err:
            errlog_writeline('ConnectionError %s while sending message %s.' % \
                             (str(err), str(msg_content)))

            self.stop()
