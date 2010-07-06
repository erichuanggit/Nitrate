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
# 
# Authors:
#   Xuqing Kuang <xkuang@redhat.com>

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class RegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=30)
    email = forms.EmailField(max_length=30)
    password1 = forms.CharField(
        max_length=30, widget=forms.PasswordInput(render_value=False),
    )
    password2 = forms.CharField(
        max_length=30, widget=forms.PasswordInput(render_value=False),
    )
    
    class Meta:
        model = User
        fields = ("username",)
    
    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_("A user with that username already exists."))
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
    
    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.is_active = False
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
    
    def set_active_key(self):
        from models import UserActivateKey
        return UserActivateKey.set_random_key_for_user(user = self.instance)
    
    def send_confirm_mail(self, request, active_key, template_name = 'registeration/confirm_email.html'):
        from tcms.core.utils import mailto
        sn = request.get_host()
        cu = sn + active_key.activation_key
        mailto(
            template_name = template_name, to_mail = self.cleaned_data['email'],
            subject = 'Your new %s account confirmation' % sn,
            context = {
                'user': self.instance,
                'active_key': active_key,
                'confirm_url': cu,
            }
        )
        
        return
