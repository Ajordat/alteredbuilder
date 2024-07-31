from django.contrib.auth.models import Group, User
from rest_framework import serializers

from decks.models import Card


# API serializers. They define what fields of the referred model they will return.
# `__all__` also includes the field `url`, which will be a link to the object's detail


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class CardSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Card
        fields = "__all__"
