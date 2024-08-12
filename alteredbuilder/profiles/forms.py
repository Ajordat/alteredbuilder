from django import forms
from django.core.validators import RegexValidator

from profiles.models import UserProfile


class UserProfileForm(forms.Form):
    template_name = ""
    bio = forms.CharField(
        max_length=UserProfile._meta.get_field("bio").max_length,
        widget=forms.Textarea(attrs={"cols": 40, "rows": 10}),
        required=False,
    )
    # bio = forms.Textarea(validators=[MaxLengthValidator(UserProfile._meta.get_field("bio").max_length)], attrs={"cols": 40, "rows": 10}, required=False)
    altered_handle = forms.CharField(required=False, validators=[])
    discord_public = forms.BooleanField(required=False)
