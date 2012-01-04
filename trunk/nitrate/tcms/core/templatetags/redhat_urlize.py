# -*- coding: utf-8 -*-
# 
# Nitrate is copyright 2010 Red Hat, Inc.
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

'''
For security purpose, only convert the valid links that ends with .redhat.com.
For the email address, just do the default action.

The redhat_urlize is ported from the core django urlize filter.
'''

import re
import string

from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeData, mark_safe
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.utils.html import escape
from django.utils.http import urlquote

from django import template

register = template.Library()

LEADING_PUNCTUATION  = ['(', '<', '&lt;']
TRAILING_PUNCTUATION = ['.', ',', ')', '>', '\n', '&gt;']

word_split_re = re.compile(r'(\s+)')
simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')
punctuation_re = re.compile('^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % \
    ('|'.join([re.escape(x) for x in LEADING_PUNCTUATION]),
    '|'.join([re.escape(x) for x in TRAILING_PUNCTUATION])))

def is_redhat_url(middle):
    if not middle:
        return False

    from urlparse import urlparse

    parse_result = urlparse(middle)
    if parse_result.scheme or parse_result.netloc:
        return parse_result.netloc.split(':')[0].endswith('redhat.com')
    
    # According to the RFC 1808, which is also documented
    #   within the urlparse module seciton of Python documentation, 
    #   it must add prefix // to the url for reteirving proper netloc    
    # So, reparse the new URL
    middle = '//%s' % middle
    parse_result = urlparse(middle)
    return parse_result.netloc.split(':')[0].endswith('redhat.com')

def urlize(text, trim_url_limit=None, nofollow=False, autoescape=False):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links and links ending in .org, .net or
    .com. Links can have trailing punctuation (periods, commas, close-parens)
    and leading punctuation (opening parens) and it'll still do the right
    thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_unicode(text))
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    for i, word in enumerate(words):
        match = None
        if '.' in word or '@' in word or ':' in word:
            match = punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            # Make URL we want to point to.
            url = None
            # The URL that ends with redhat.com is valid.
            # Here, only check the web site's URL but the Email address.
            if (middle.startswith('http://') or middle.startswith('https://')) and is_redhat_url(middle):
                url = urlquote(middle, safe='/&=:;#?+*')
            elif '@' not in middle and \
                    middle and middle[0] in string.ascii_letters + string.digits and is_redhat_url(middle):
                url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
            elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
                url = 'mailto:%s' % middle
                nofollow_attr = ''
            # Make link.
            if url:
                trimmed = trim_url(middle)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    url, trimmed = escape(url), escape(trimmed)
                middle = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, trimmed)
                words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
            else:
                if safe_input:
                    words[i] = mark_safe(word)
                elif autoescape:
                    words[i] = escape(word)
        elif safe_input:
            words[i] = mark_safe(word)
        elif autoescape:
            words[i] = escape(word)
    return u''.join(words)
urlize = allow_lazy(urlize, unicode)

@stringfilter
@register.filter(name='redhat_urlize')
def redhat_urlize(value, autoescape=None):
    """Converts URLs, which only ends with .redhat.com, in plain text into clickable links."""
    # Using my custom urlize above
    return mark_safe(urlize(value, nofollow=True, autoescape=autoescape))
redhat_urlize.is_safe=True
redhat_urlize.needs_autoescape = True

