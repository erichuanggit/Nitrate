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

from kobo.django.xmlrpc.models import XmlRpcLog


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
        def _new_function(request, *args, **kwargs):
            try:
                argspec = inspect.getargspec(function)
                arg_names = argspec[0][1:]
                known_args = zip(arg_names, args)
                unknown_args = list(enumerate(args[len(arg_names):]))
                keyword_args = [(key, value) for key, value in kwargs.iteritems()
                                if (key, value) not in known_args]

                log = XmlRpcLog()
                log.user = request.user
                log.method = '%s%s' % (namespace, function.__name__)
                log.args = str(known_args + unknown_args + keyword_args)
                log.save()
            except:
                pass
            return function(request, *args, **kwargs)

        _new_function.__name__ = function.__name__
        _new_function.__doc__ = function.__doc__
        _new_function.__dict__.update(function.__dict__)
        return _new_function

    return decorator