# -*- coding: utf-8 -*-


import unittest

from tcms.xmlrpc.testcaserun import update
from django.contrib.auth.models import User


class FakeRequest(object):

    def __init__(self):
        self.user = User.objects.get(username='cqi')


class TestCaseForRunUpdate(unittest.TestCase):
    '''Specific to testcaserun.update method

    Test for fixing issue TCMS-122

    Sample TestCaseRuns: 3479449, 3479450, 3479451
    '''

    def setUp(self):
        self.user = User.objects.get(username='cqi')

    def test_update(self):
        tcrs_to_update = [3479449, 3479450, 3479451]
        data_to_update = {
            'notes': 'test testcaserun.update',
            'assignee': self.user.pk,
        }
        request = FakeRequest()

        updated_tcrs = update(request, tcrs_to_update, data_to_update)

        self.assertEqual(len(updated_tcrs), 3)

        test_pks = [item['case_run_id'] for item in updated_tcrs]
        test_pks.sort()
        self.assertEqual(tcrs_to_update, test_pks)

        test_notes = [item['notes'] for item in updated_tcrs]
        for notes in test_notes:
            self.assertEqual(data_to_update['notes'], str(notes))

        test_assignees = [(item['assignee'], item['assignee_id'])
                          for item in updated_tcrs]
        for assignee, assignee_id in test_assignees:
            self.assertEqual(assignee, self.user.username)
            self.assertEqual(assignee_id, self.user.pk)


if __name__ == '__main__':
    unittest.main()
