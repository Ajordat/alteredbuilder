from django import forms
from django.core.validators import RegexValidator

from profiles.models import UserProfile

PROFILE_PICTURES = [
    ("AX_AXIOM.png", "Axiom"),
    ("AX_SIERRA.png", "Sierra"),
    ("AX_TREYST.png", "Treyst"),
    ("AX_SUBHASH.png", "Subhash"),
    ("BR_BRAVOS.png", "Bravos"),
    ("BR_KOJO.png", "Kojo"),
    ("BR_ATSADI.png", "Atsadi"),
    ("BR_BASIRA.png", "Basira"),
    ("LY_LYRA.png", "Lyra"),
    ("LY_NEVENKA.png", "Nevenka"),
    ("LY_AURAQ.png", "Auraq"),
    ("LY_FEN.png", "Fen"),
    ("MU_MUNA.png", "Muna"),
    ("MU_TEIJA.png", "Teija"),
    ("MU_ARJUN.png", "Arjun"),
    ("MU_RIN.png", "Rin"),
    ("OR_ORDIS.png", "Ordis"),
    ("OR_SIGISMAR.png", "Sigismar"),
    ("OR_WARU.png", "Waru"),
    ("OR_GULRANG.png", "Gulrang"),
    ("YZ_YZMIR.png", "Yzmir"),
    ("YZ_AKESHA.png", "Akesha"),
    ("YZ_LINDIWE.png", "Lindiwe"),
    ("YZ_AFANAS.png", "Afanas"),
    ("NE_DEFAULT.png", "Default"),
]


class UserProfileForm(forms.Form):
    """Form to validate a User's profile modification."""

    template_name = "forms/submit_userprofile.html"
    avatar = forms.ChoiceField(
        choices=PROFILE_PICTURES, widget=forms.RadioSelect, label="Select your avatar"
    )
    bio = forms.CharField(
        max_length=UserProfile._meta.get_field("bio").max_length,
        widget=forms.Textarea(attrs={"cols": 40, "rows": 10}),
        required=False,
    )
    altered_handle = forms.CharField(
        required=False, validators=[RegexValidator(r".+_\d{4}$")]
    )
    discord_public = forms.BooleanField(required=False)
