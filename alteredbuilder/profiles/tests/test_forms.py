from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from config.tests.utils import get_login_url
from profiles.forms import UserProfileForm


class EditProfileFormTestCase(TestCase):
    def test_invalid_profile_large_bio(self):
        form_data = {"bio": "-" * 1001}

        form = UserProfileForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertFormError(
            form, "bio", "Ensure this value has at most 1000 characters (it has 1001)."
        )

    def test_invalid_profile_invalid_handle(self):
        form_data = {"altered_handle": "this does not follow the required format"}

        form = UserProfileForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertFormError(form, "altered_handle", "Enter a valid value.")

    def test_valid_profile_unauthenticated(self):
        form_data = {"bio": "hey", "altered_handle": "test_0000", "avatar": "NE_DEFAULT.png"}

        form = UserProfileForm(data=form_data)

        self.assertTrue(form.is_valid())

    def test_edit_profile_unauthenticated(self):
        form_data = {"bio": "hey", "altered_handle": "test_0000"}

        response = self.client.post(reverse("profile-edit"), form_data)

        self.assertRedirects(
            response, get_login_url("profile-edit"), status_code=HTTPStatus.FOUND
        )

    def test_edit_profile_authenticated(self):
        user = User.objects.create_user("user1")
        user.profile.bio = "hey"
        user.profile.altered_handle = "test_0000"
        user.profile.save()
        form_data = {"bio": "new bio", "altered_handle": "another_handle_0001", "avatar": "NE_DEFAULT.png"}
        self.client.force_login(user)

        response = self.client.post(reverse("profile-edit"), form_data)

        user.refresh_from_db()
        self.assertEqual(user.profile.bio, form_data["bio"])
        self.assertEqual(user.profile.altered_handle, form_data["altered_handle"])
        self.assertRedirects(
            response, user.profile.get_absolute_url(), status_code=HTTPStatus.FOUND
        )
