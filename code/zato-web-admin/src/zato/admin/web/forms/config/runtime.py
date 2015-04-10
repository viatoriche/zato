# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Django
from django import forms

class EditFileSourceForm(forms.Form):
    """ Form for the source code-level management of run-time config files.
    """
    source = forms.CharField(widget=forms.Textarea(
        attrs={'style':'overflow:auto; width:100%; white-space: pre-wrap;height:400px'}))
