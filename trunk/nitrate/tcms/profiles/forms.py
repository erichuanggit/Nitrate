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

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from django import forms
from django.contrib.auth.models import User

from models import UserProfile

IM_CHOICES = (
    (1, 'IRC'),
    (2, 'Jabber'),
    (3, 'MSN'),
    (4, 'Yahoo messenger'),
    (5, 'ICQ')
)

class UserProfileForm(forms.ModelForm):
    user = forms.CharField(widget=forms.HiddenInput)
    username = forms.RegexField(
        label=_("Username"), max_length=30, regex=r'^[\w.@+-]+$',
        help_text = _("Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only."),
        error_messages = {'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")}
    )
    first_name = forms.CharField(max_length=128, required = False)
    last_name = forms.CharField(max_length=128, required = False)
    email = forms.EmailField(label=_("E-mail"), max_length=75)
    im_type_id = forms.ChoiceField(choices = IM_CHOICES)
    
    class Meta:
        model = UserProfile
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        if kwargs.has_key('instance'):
            instance = kwargs['instance']
            self.initial['username'] = instance.user.username
            self.initial['first_name'] = instance.user.first_name
            self.initial['last_name'] = instance.user.last_name
            self.initial['email'] = instance.user.email
    
    def clean_user(self):
        if not self.instance.pk:
            return User.objects.get(pk = self.cleaned_data['user'])
        
        if self.instance.user.pk == int(self.cleaned_data['user']):
            return self.instance.user
        
        raise forms.ValidationError(_("User error."))
    
    def clean_username(self):
        username = self.cleaned_data["username"]
        if not self.instance.pk:
            return username
        
        if username == self.instance.user.username:
            return username
        
        try:
            User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username
        
        raise forms.ValidationError(_("A user with that username already exists."))
    
    def save(self, commit = True):
        from django.contrib.auth import get_backends
        
        instance = super(UserProfileForm, self).save(commit=commit)
        user = instance.user
        can_register = False
        
        for b in get_backends():
            if getattr(b, 'can_register'):
                can_register = True
        
        if can_register:
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']
        
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return instance
