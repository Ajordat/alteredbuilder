from django import forms


class SubmitSessionForm(forms.Form):

    template_name = "forms/submit_session.html"
    session_key = forms.CharField(max_length=64, required=True)
