from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'discord_public']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }
