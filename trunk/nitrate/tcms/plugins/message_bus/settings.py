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

# Plugin settings

'''
Configuration for QPID connection and
message bus integration
'''

BROKER_CONNECTION_INFOS = {
    'local': {
        'host': 'localhost',
        'port': 5672,
        'sasl_mechanisms': 'ANONYMOUS'
    },

    'qpid_dev': {
        'host': 'mixologist.lab.bos.redhat.com',
        'port': 5671,
        'sasl_mechanisms': 'GSSAPI'
    },

    'qpid_product': {
        'host': 'qpid.devel.redhat.com',
        'port': 5671,
        'sasl_mechanisms': 'GSSAPI'
    }
}

broker_ptr = 'local'

BROKER_CONNECTION_INFO = BROKER_CONNECTION_INFOS[broker_ptr]

ROUTING_KEY_PREFIX = 'tcms'
TOPIC_EXCHANGE = 'eso.topic'

SENDER_ADDRESS = '%s; { assert: always, node: { type: topic } }' % TOPIC_EXCHANGE
RECEIVER_ADDRESS = ''
