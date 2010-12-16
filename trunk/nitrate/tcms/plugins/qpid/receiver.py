#!/usr/bin/python

from pprint import pprint
from base import QPIDBase

class QPIDReceiver(QPIDBase):
    def __init__(self, url, **kwargs):
        super(QPIDSender, self).__init__(url, **kwargs)
        self.receiver = None
    
    def init_receiver(self):
        """Initial the receiver"""
        if not self.session:
            self.init_session()
        self.receiver = self.session.receiver(self.queue_name)
        
    def receive(self):
        """Listing the messages from server"""
        if not self.receiver:
            self.init_receiver()
            
        try:
            while True:
                message = self.receiver.fetch()
                content = message.content
                pprint({'props': message.properties})
                pprint(content)
                self.session.acknowledge(message)
        except KeyboardInterrupt:
            pass
        
        self.close()

# Test code
if __name__ == '__main__':
    r = QPIDReceiver()
    r.receive()
