from django import forms
from django.utils.translation import gettext_lazy as _


class SubmitSessionForm(forms.Form):

    template_name = "forms/submit_session.html"
    session_key = forms.CharField(max_length=64, required=True)
