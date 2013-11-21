# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.utils import simplejson

from tcms.core import forms
from tcms.apps.testcases.forms import CaseCategoryForm
from tcms.apps.testcases.models import TestCaseCategory


class CategoryActions(object):
    """Category actions used by view function `category'"""
    # FIXME: it's unnecessary to pass tcs when construct this action object.
    #        because it will be used only when method update get called.
    #        *Meanwhile*, according to the interface getting selected TestCases
    #        requires REQUEST object only. So, just call that method within
    #        method update is enough.
    def __init__(self, request):
        self.ajax_response = {'rc': 0, 'response': 'ok', 'errors_list': []}
        self.request = request
        self.product_id = request.REQUEST.get('product')

    def __get_form(self):
        self.form = CaseCategoryForm(self.request.REQUEST)
        self.form.populate(product_id = self.product_id)
        return self.form

    def __check_form_validation(self):
        form = self.__get_form()
        if not form.is_valid():
            return 0, self.render_ajax(forms.errors_to_list(form))

        return 1, form

    def __check_perms(self, perm):
        return 1, True

    def update(self):
        is_valid, perm = self.__check_perms('change')
        if not is_valid:
            return perm

        is_valid, form = self.__check_form_validation()
        if not is_valid:
            return form

        category_pk = self.request.REQUEST.get('o_category')
        # FIXME: no exception hanlder when pk does not exist.
        category = TestCaseCategory.objects.get(pk=category_pk)
        # FIXME: lower performance. It's not necessary to update each TestCase
        # in this way.
        from tcms.apps.testcases.views import get_selected_testcases
        tcs = get_selected_testcases(self.request)
        for tc in tcs:
            tc.category = category
            tc.save()
        return self.render_ajax(self.ajax_response)

    def render_ajax(self, response):
        return HttpResponse(simplejson.dumps(self.ajax_response))

    def render_form(self):
        form = CaseCategoryForm(initial={
            'product': self.product_id,
            'category': self.request.REQUEST.get('o_category'),
        })
        form.populate(product_id = self.product_id)

        return HttpResponse(form.as_p())
