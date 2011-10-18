import unittest
from django.test.client import Client
#from django.test import TestCase

class CaseTests(unittest.TestCase):

    def setUp(self):
        self.c = Client();
        self.case_id = 12345
        self.status_codes = [301, 302]

    def test_cases(self):
        response = self.c.get('/cases/')
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_new(self):
        response = self.c.get('/case/new/')
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_clone(self):
        response = self.c.get('/cases/clone/', {'case':12197})
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_cases_changestatus(self):
        response = self.c.get('/cases/changestatus/')
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_cases_priority(self):
        response = self.c.get('/cases/priority/')
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_getcase(self):
        location = '/case/%s' % self.case_id
        response = self.c.get(location)
        if response.status_code == 301:
            print response.path
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            assert response.status_code in self.status_codes

    def test_case_details(self):
        location = '/case/%s/details' % self.case_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            assert response.status_code in self.status_codes
#            self.assertEquals(response.status_code, 302)

    def test_case_edit(self):
        location = '/case/%s/edit/' % self.case_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_history(self):
        location = '/case/%s/history/' % self.case_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_changecaseorder(self):
        location = '/case/%s/changecaseorder/' % self.case_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_attachment(self):
        location = '/case/%s/attachment/' % self.case_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_log(self):
        location = '/case/%s/log/' % self.case_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_bug(self):
        location = '/case/%s/bug/' % self.case_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)

    def test_case_plan(self):
        location = '/case/%s/plan/' % self.case_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError, e:
            self.assertEquals(response.status_code, 302)


if __name__ == '__main__':
    unittest.main()

#jianchen test gerrit
