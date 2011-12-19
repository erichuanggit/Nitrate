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

import unittest

from qpid.messaging import Message
from tcms.plugins.message_bus.outgoing_message import OutgoingMessage

class TestOutgoingMessage(unittest.TestCase):

    def testOutgoingMessageShouldRepresentMessage(self):
        raw_msg = 'hello world'
        event_name = 'bugs.add'

        o_msg = OutgoingMessage(raw_msg, event_name)

        self.assertTrue(isinstance(o_msg, Message))
        self.assertEqual(o_msg.content, raw_msg)
        self.assertEqual(o_msg.subject, 'tcms.%s' % event_name)
        self.assertTrue(hasattr(o_msg, 'properties'))

if __name__ == '__main__':
    unittest.main()

