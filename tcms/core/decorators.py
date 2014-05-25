# -*- coding: utf-8 -*-
# 
# Nitrate is copyright 2014 Red Hat, Inc.
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
#
# Authors:
#   Chenxiong Qi <cqi@redhat.com>

import inspect
import logging

from functools import wraps

from django.conf import settings
from kobo.django.xmlrpc.models import XmlRpcLog

__all__ = ('log_call',)

logger = logging.getLogger('nitrate.xmlrpc')

if settings.DEBUG:
    # To avoid pollute XMLRPC logs with those generated during development
    def create_log(user, method, args):
        log_msg = 'user: {0}, method: {1}, args: {2}'.format(
            user.username if hasattr(user, 'username') else user,
            method,
            args)
        logger.debug(log_msg)
else:
    create_log = XmlRpcLog.objects.create


def log_call(*args, **kwargs):
    '''Log XMLRPC-specific invocations

    This is copied from kobo.django.xmlrpc.decorators to add custom abitlities,
    so that we don't have to wait upstream to make the changes.

    Usage::

        from tcms.core.decorators import log_call
        @log_call(namespace='TestNamespace')
        def func(request):
            return None
    '''
    namespace = kwargs.get('namespace', '')
    if namespace:
        namespace = namespace + '.'

    def decorator(function):
        argspec = inspect.getargspec(function)
        # Each XMLRPC method has an HttpRequest argument as the first one,
        # it'll be ignored in the log.
        arg_names = argspec.args[1:]

        @wraps(function)
        def _new_function(request, *args, **kwargs):
            try:
                known_args = zip(arg_names, args)
                unknown_args = list(enumerate(args[len(arg_names):]))
                keyword_args = [(key, value) for key, value in kwargs.iteritems()
                                if (key, value) not in known_args]

                create_log(user=request.user,
                           method='%s%s' % (namespace, function.__name__),
                           args=str(known_args + unknown_args + keyword_args))
            except:
                pass
            return function(request, *args, **kwargs)
        return _new_function

    return decorator
