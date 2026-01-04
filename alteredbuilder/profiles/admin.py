from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet

from profiles.models import Follow, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "bio", "is_spam"]
    list_filter = ["is_spam"]
    show_facets = admin.ShowFacets.ALWAYS
    search_fields = ["user__username"]
    readonly_fields = ["user", "code", "altered_handle", "discord_public"]
    fieldsets = [
        (None, {"fields": ["user", "code", "bio", "avatar", "is_spam"]}),
        ("Platform", {"fields": ["collection"]}),
        ("Social accounts", {"fields": ["altered_handle", "discord_public"]}),
    ]
    actions = ["mark_as_spam"]

    @admin.action(description="Report as spam")
    def mark_as_spam(self, request, queryset: QuerySet[UserProfile]):
        updated_profiles = queryset.update(is_spam=True, bio="")
        updated_users = (
            get_user_model()
            .objects.filter(profile__in=queryset)
            .update(is_active=False)
        )
        self.message_user(
            request,
            f"{updated_profiles} profiles(s) reported as spam, {updated_users} user(s) disabled.",
        )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ["__str__"]
    readonly_fields = ["follower", "followed"]
