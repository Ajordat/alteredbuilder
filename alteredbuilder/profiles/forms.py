from django import forms
from django.core.validators import RegexValidator

from profiles.models import UserProfile


class UserProfileForm(forms.Form):
    """Form to validate a User's profile modification."""

    template_name = "forms/submit_userprofile.html"
    bio = forms.CharField(
        max_length=UserProfile._meta.get_field("bio").max_length,
        widget=forms.Textarea(attrs={"cols": 40, "rows": 10}),
        required=False,
    )
    altered_handle = forms.CharField(
        required=False, validators=[RegexValidator(r".+_\d{4}$")]
    )
    discord_public = forms.BooleanField(required=False)
