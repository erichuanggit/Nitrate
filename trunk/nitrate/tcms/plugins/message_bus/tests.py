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

import subprocess
import unittest

from itertools import *

from qpid.messaging import Message

import settings

from tcms.plugins.message_bus.outgoing_message import OutgoingMessage
from tcms.plugins.message_bus.message_bus import MessageBus

class TestOutgoingMessage(unittest.TestCase):

    def testOutgoingMessageShouldRepresentMessage(self):
        raw_msg = 'hello world'
        event_name = 'bugs.add'

        o_msg = OutgoingMessage(raw_msg, event_name)

        self.assertTrue(isinstance(o_msg, Message))
        self.assertEqual(o_msg.content, raw_msg)
        self.assertEqual(o_msg.subject, 'tcms.%s' % event_name)
        self.assertTrue(hasattr(o_msg, 'properties'))

class TestMessageBus(unittest.TestCase):

    binding_key = 'tcms.#'
    queue_name = 'tmp.qcx.test'

    # Initialized when setUp
    qmf_session = None

    def setUp(self):
        # Setup QPID environment
        cmd = 'qpid-config add exchange topic {0}'.format(settings.TOPIC_EXCHANGE).split()
        subprocess.Popen(cmd).wait()

        cmd = 'qpid-config add queue {0}'.format(self.queue_name).split()
        subprocess.Popen(cmd).wait()

        cmd = 'qpid-config bind {exchange_name} {queue_name} {binding_key}'.format(
            exchange_name = settings.TOPIC_EXCHANGE,
            queue_name = self.queue_name,
            binding_key = self.binding_key).split()
        subprocess.Popen(cmd).wait()

        # Initialize message bus
        MessageBus.initialize()

        # Initialize session for retreiving information from QPID server
        from qmf.console import Session

        self.qmf_session = Session()
        self.qmf_session.addBroker('{host}:{port}'.format(
            host = settings.BROKER_CONNECTION_INFO['host'],
            port = settings.BROKER_CONNECTION_INFO['port']))

    def tearDown(self):
        # Clear test environment in reverse order
        self.qmf_session.close()
        MessageBus.stop()

        cmd = 'qpid-config unbind {exchange_name} {queue_name}'.format(
            exchange_name = settings.TOPIC_EXCHANGE,
            queue_name = self.queue_name).split()
        subprocess.Popen(cmd).wait()

        cmd = 'qpid-config del queue {0} --force'.format(self.queue_name).split()
        subprocess.Popen(cmd).wait()

        cmd = 'qpid-config del exchange {0}'.format(settings.TOPIC_EXCHANGE).split()
        subprocess.Popen(cmd).wait()

    def get_queue_by_name(self, queues, name):
        # OMG, I'm crazy :D
        found_queues = [item for item in
            takewhile(lambda queue: queue.name == name,
                dropwhile(lambda queue: queue.name != name, queues))]

        return found_queues[0] if found_queues else None

    def get_msgdepth_from_statistics(self, statistics):
        # OMG, I'm crazy again! :D
        result = [item for item in
            takewhile(lambda item: item[0].name == 'msgDepth',
                dropwhile(lambda item: item[0].name != 'msgDepth', statistics))]

        return result[0][1] if result else None

    def testLongTermLongCreationAndReusable(self):
        conn = MessageBus._connection
        self.assertNotEqual(conn, None)
        self.assertTrue(conn.opened())
        self.assertTrue(conn.attached())

        sess = MessageBus._session
        self.assertNotEqual(sess, None)

        sender = MessageBus._sender
        self.assertNotEqual(sender, None)

    def testSendMessage(self):
        # Step 1:
        msg_content = 'hello world'
        event_name = 'bugs.add'
        self.assertEqual(MessageBus._connection.attached(), True)
        MessageBus.send(msg_content, event_name)

        # Step 2:
        queues = self.qmf_session.getObjects(_class='queue', _package='org.apache.qpid.broker')
        queue = self.get_queue_by_name(queues, self.queue_name)
        self.assertNotEqual(queue, None)

        msg_depth = self.get_msgdepth_from_statistics(queue.getStatistics())
        self.assertNotEqual(msg_depth, None)
        self.assertEqual(msg_depth, 1)

if __name__ == '__main__':
    unittest.main()

