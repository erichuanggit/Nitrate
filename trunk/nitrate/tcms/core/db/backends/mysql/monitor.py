#!/usr/bin/env python
# Author: Chaobin Tang <ctang@redhat.com>

from django.core.exceptions import SuspiciousOperation
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader, Context
from tcms.core.middleware import RememberRequestMiddleware
import traceback, logging, re


ON = False
Log = None

PATTERN = re.compile(r'.*DELETE\s+FROM\s+`?test_case_texts`?.*', re.I)

def init_log():
    global Log
    logger = logging.getLogger('suspicious_operation')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(settings.SUSPICIOUS_OPERATION_LOG_FILE)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    Log = logger
init_log()

def decide_monitor_settings():
    '''
    Switch the working status
    of the monitor by settings
    defined in settings.py.
    Default to False.
    '''
    global ON
    status = getattr(settings, 'MONITOR_SUSPICIOUS', False)
    ON = status
decide_monitor_settings()

def mail_to_admin(subject, content):
    send_mail(
        subject,
        content,
        settings.EMAIL_FROM,
        [admin[1] for admin in settings.ADMINS]
    )

def extract_useful_info(query, args):
    stack_depth_limit = 20
    request = RememberRequestMiddleware.get_current_request()
    stack_info = traceback.extract_stack(limit=stack_depth_limit)
    tmpl = loader.get_template(settings.SUSPICIOUS_LOG_TEMPLATE)
    cxt = Context({
        'request': request,
        'stack_info': stack_info,
        'query': query,
        'query_args': args
    })
    content = tmpl.render(cxt)
    return content

def log_suspicious_operations(content):
    '''
    The following things are logged:
    1. all submitted data in request
    2. traceback
    3. query
    '''
    try:
        Log.info(content)
    except:
        pass

def is_suspicious(query, args):
    '''
    Attempting to check it against a sql in a form like this:
    'DELETE FROM `test_case_texts` WHERE `case_text_version` IN (1)'
    '''
    suspicious = False
    match = PATTERN.match(query)
    if match is not None:
        suspicious = True
    return suspicious

def report_suspicious_operations(content):
    subject = 'Suspicious Operation On TCMS Monitored!'
    mail_to_admin(subject, content)

def watchit(query, args):
    '''
    This function does what the current module says.
    '''
    if is_suspicious(query, args):
        useful_info = extract_useful_info(query, args)
        log_suspicious_operations(useful_info)
        report_suspicious_operations(useful_info)
        raise SuspiciousOperation('Sorry, this is considered a suspicious operation')