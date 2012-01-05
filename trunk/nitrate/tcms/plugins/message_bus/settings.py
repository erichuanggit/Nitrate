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

import os

BROKER_CONNECTION_INFOS = {
    'local': {
        'host': 'localhost',
        'port': 5672,
        'sasl_mechanisms': 'ANONYMOUS'
    },

    'qpid_dev': {
        'host': 'mixologist.lab.bos.redhat.com',
        'port': 5671,
        'sasl_mechanisms': 'GSSAPI',
        'transport': 'ssl',
    },

    'qpid_product': {
        'host': 'qpid.devel.redhat.com',
        'port': 5671,
        'sasl_mechanisms': 'GSSAPI',
        'transport': 'ssl',
    }
}

# Using environment variable to control to which message broker message bus connects.
# By default, message bus connects to QPID production broker.
# :O MB stands for MessageBus. I just don't want a long name.
if 'NITRATE_MB_BROKER' in os.environ:
    broker_ptr = os.environ['NITRATE_MB_BROKER']
    if broker_ptr not in BROKER_CONNECTION_INFOS.keys():
        raise NameError('Cannot read broker\'s information. {0} does not exist.'.format(broker_ptr))
else:
    broker_ptr = 'qpid_product'

BROKER_CONNECTION_INFO = BROKER_CONNECTION_INFOS[broker_ptr]

ROUTING_KEY_PREFIX = 'tcms'
TOPIC_EXCHANGE = 'eso.topic'
TMP_RECEIVE_QUEUE = 'tmp.reading.errata'

SENDER_ADDRESS = '%s; { assert: always, node: { type: topic } }' % TOPIC_EXCHANGE
RECEIVER_ADDRESS = '''%s;
    {
        assert: always,
        create: receiver,
        node: {
            type: queue, durable: False,
            x-declare: {
                exclusive: True,
                auto_delete: True
            },
            x-bindings: [
                { exchange: "%s", queue: "%s", key: "tcms.#" },
                { exchange: "%s", queue: "%s", key: "secalert.tcms.#" }
            ]
        }
    }'''.replace(os.linesep, '') % (
        TMP_RECEIVE_QUEUE,
        TOPIC_EXCHANGE, TMP_RECEIVE_QUEUE,
        TOPIC_EXCHANGE, TMP_RECEIVE_QUEUE)

