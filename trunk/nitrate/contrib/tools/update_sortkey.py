#/usr/bin/python

import os

TCMS_SETTINGS_MODULE = 'tcms.product_settings'
os.environ['DJANGO_SETTINGS_MODULE'] = TCMS_SETTINGS_MODULE

from tcms.testcases.models import TestCasePlan, TestCase
from tcms.testplans.models import TestPlan

def update_sortkey():
    for tc in TestCase.objects.all():
        sk = tc.sortkey
        TestCasePlan.objects.filter(case = tc).update(sortkey = sk)
    

if __name__ == '__main__':
    update_sortkey()