# -*- coding: utf-8 -*- 

import settings

from qpid.messaging import Message

class OutgoingMessage(Message):
    ''' A simple wrapper for constructing QPID specific message object and its routing key '''

    def __init__(self, raw_msg, event_name, *args, **kwargs):
        ''' Using extra two argument to initialize the outgoing message
            raw_msg: the raw message, which is sent by via QPID broker
            event_name: a name that is used to construct message's routing key.
                        This is an internal name mapping to:
                        testrun.create, testrun.progress, testrun.report, bugs.add, bugs.removal
                        There may be more than these in the future. Just following this naming rule is OK.
            The rest of arguments are the qpid's Message's.
        '''

        Message.__init__(self, *args, **kwargs)

        self.content = raw_msg

        # *** This is the outgoing message's routing key
        # *** The broker will route this message according to this routing key
        self.subject = '{routing_key_prefix}.{event_name}'.format(
            routing_key_prefix = settings.ROUTING_KEY_PREFIX,
            event_name = event_name)
