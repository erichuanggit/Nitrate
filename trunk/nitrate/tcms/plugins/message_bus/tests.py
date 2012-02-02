# -*- coding: utf-8 -*-
# 
# Nitrate internal plugin is copyright 2010 Red Hat, Inc.
# 
# Nitrate is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. This program is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranties of TITLE, NON-INFRINGEMENT,
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# 
# The GPL text is available in the file COPYING that accompanies this
# distribution and at <http://www.gnu.org/licenses>.

# Plugin unit testing

import os
import re
import subprocess
import unittest

from cStringIO import StringIO

from qpid.messaging import Message
from qpid.messaging.exceptions import ConnectError
from qpid.messaging.exceptions import AuthenticationFailure
from qpid.sasl import SASLError

from tcms.plugins.message_bus import settings as st
from tcms.plugins.message_bus.outgoing_message import OutgoingMessage
from tcms.plugins.message_bus.message_bus import MessageBus

class TestSettings(unittest.TestCase):
    '''
    Ensure the necessary settings are valid in real run-time environment,
    which might be a test or production server. If you want to
    check whether messaging works in server, you can run this also.

    So, this test case is different from th rest of this tests module.
    '''

    def test_keytab(self):
        # If don't want to use GSSAPI, it is unnecessary to check keytab
        if not st.USING_GSSAPI:
            return

        keytab_filename = st.SERVICE_KEYTAB
        self.assert_(os.path.exists(keytab_filename),
            'Keytab file %s does not exist.' % keytab_filename)

        result = os.access(keytab_filename, os.R_OK)
        self.assert_(result, 'Have no privilege to access the keytab file.')

        po = subprocess.Popen(('klist -k -t %s' % keytab_filename).split(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = po.communicate()

        ore = re.compile(r'.* (\w+)/([\w.]+)@([\w.]+)')
        for line in stdout.split(os.linesep):
            om = ore.match(line)
            if not om: continue

            kt_service_name = om.group(1)
            kt_service_hostname = om.group(2)
            kt_realm = om.group(3)

            self.assertEqual(kt_service_name, st.SERVICE_NAME,
                'Keytab\'s service name %s does not match SERVICE_NAME in settings.' % kt_service_name)
            self.assertEqual(kt_service_hostname, st.SERVICE_HOSTNAME,
                'Keytab\'s hostname %s does not match SERVICE_HOSTNAME in settings.' % kt_service_hostname)
            self.assertEqual(kt_realm, st.REALM,
                'Keytab\'s realm %s does not match REALM in settings.' % kt_realm)

            # Test ends as long as there is one principal within keytab
            return

        self.fail('Keytab does not contain service name %s, hostname %s, ' \
                  'and realm %s set in settings.' % (
                    st.SERVICE_NAME, st.SERVICE_HOSTNAME, st.REALM))

    def test_service_principal(self):
        '''
        Ensure that developer do not modify the SERVICE_PRINCIPAL occassionally.

        Value of SERVICE_PRINCIPAL is generated by SERVICE_NAME, SERVICE_HOSTNAME,
        and REALM automatically. It is unnecessary to modify it manually.
        '''

        principal = '%s/%s@%s' % (st.SERVICE_NAME, st.SERVICE_HOSTNAME, st.REALM)
        self.assertEqual(principal, st.SERVICE_PRINCIPAL,
            'You do not need to modify the SERVICE_PRINCIPAL in settings, recover it now.')

    def test_broker_transport(self):

        self.assert_(st.QPID_BROKER_TRANSPORT in ('tcp', 'tcp+tls', 'ssl'),
            '%s is not one of tcp, tcp+tls and ssl' % st.QPID_BROKER_TRANSPORT)

    def test_broker_sasl_mechanisms(self):

        valid_mechenisms = ['ANONYMOUS', 'CRAM-MD5', 'DIGEST-MD5', 'GSSAPI', 'PLAIN']

        for name in st.QPID_BROKER_SASL_MECHANISMS.split(' '):
            self.assert_(name in valid_mechenisms, '%s is not a valid mechanism' % name)

        if st.USING_GSSAPI:
            self.assert_('GSSAPI' in st.QPID_BROKER_SASL_MECHANISMS.split(' '),
                'GSSAPI is enabled, but GSSAPI does not exist in QPID_BROKER_SASL_MECHANISMS')

class TestOutgoingMessage(unittest.TestCase):

    def testOutgoingMessageShouldRepresentMessage(self):
        '''
        Ensure the OutgoingMessage can represent a Message,
        which is provided by python-qpid package.

        The important thing is to check whether the instance of OutgoingMessage
        recognizes the message's content type.
        '''

        raw_msg = 'hello world'
        event_name = 'bugs.add'

        o_msg = OutgoingMessage(raw_msg, event_name)

        self.assertTrue(isinstance(o_msg, Message))
        self.assertEqual(o_msg.content, raw_msg)
        self.assertEqual(o_msg.subject, 'tcms.%s' % event_name)
        self.assertTrue(hasattr(o_msg, 'properties'))

        raw_msg = {}
        o_msg = OutgoingMessage(raw_msg, event_name)
        self.assertNotEqual(o_msg.content_type, None)
        self.assertEqual(o_msg.content_type, 'amqp/map')

class TestUtils(unittest.TestCase):

    def setUp(self):
        self.old_ccache = os.getenv('KRB5CCNAME', None)

    def tearDown(self):
        if self.old_ccache:
            os.environ['KRB5CCNAME'] = self.old_ccache

    def test_refresh_credential_cache(self):
        '''
        This test method depends on whether to use GSSAPI authentication mechanism.

        When this method throws Krb5Error, do check whether enable USING_GSSAPI and
        configure GSSAPI related configurations correctly.
        '''

        from tcms.plugins.message_bus.utils import refresh_HTTP_credential_cache

        old_cache = os.getenv('KRB5CCNAME', None)

        ccache_file = refresh_HTTP_credential_cache()
        os.environ['KRB5CCNAME'] = ccache_file

        self.assert_(os.path.exists(ccache_file),
            'The credential cache file was not be generated.')

        op = subprocess.Popen('klist'.split(),
            stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout, stderr = op.communicate()

        if old_cache:
            os.environ['KRB5CCNAME'] = old_cache
        else:
            del os.environ['KRB5CCNAME']

        reader = StringIO(stdout)
        line1 = reader.readline().strip(os.linesep)
        line2 = reader.readline().strip(os.linesep)
        reader.close()

        self.assertEqual(line1, 'Ticket cache: FILE:%s' % ccache_file,
            'Ticket cache file name does not match the newly generated.')
        self.assertEqual(line2, 'Default principal: %s' % st.SERVICE_PRINCIPAL,
            'Default principal within credential cache does not match the SERVICE_PRINCIPAL in settings')

class TestMessageBus(unittest.TestCase):

    def test_sending_message(self):
        msg_content = {
            'who': 'TestMessageBus.test_sending_message',
            'when': '2012-1-30 15:17:10',
            'percent': '100%',
            'errata_id': 1234
        }

        try:
            MessageBus().send(msg_content=msg_content, event_name='testrun.created')
        except AuthenticationFailure, err:
            # Something wrong with the authentication configuration,
            # or not allowed to send message with current ticket.
            self.fail(str(err))
        except SASLError, err:
            # Same as above, check the error's message for detial
            self.fail(str(err))
        except ConnectError, err:
            # Something wrong with the connection establishing
            self.fail(str(err))

if __name__ == '__main__':
    unittest.main()
